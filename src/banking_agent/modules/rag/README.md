# B-RAG 模块：C / E 联调指南

B负责检索政策证据和来源信息。当前推荐后端是**优化BM25召回前20条，再由Cross-Encoder重排，默认返回前5条**。

- **B**：返回候选证据、来源和排序分数。
- **C**：判断证据充分度、风险和最终业务动作，例如 `ANSWER`、`ABSTAIN`。
- **E**：管理调用顺序、合并State、组织最终回答和引用、记录决策轨迹。

`status="ok"`仅表示存在候选文档，不保证证据足以回答。当前没有启用拒答阈值。
本模块使用合成NovaBank政策，不连接真实银行系统。

## 1. E如何接入

### 1.1 环境准备

在仓库根目录、Python 3.11+环境中安装：

```sh
python -m pip install -e '.[rag-dense]'
```

真实后端默认加载已缓存的模型，不在请求过程中下载模型。
默认Cross-Encoder为 `cross-encoder/ms-marco-MiniLM-L6-v2`，固定revision：

```text
233902d25c440f23af6f7d6e94d2946bac0bee0a
```

首次准备模型时，可在允许联网的启动或部署准备阶段运行：

```python
from banking_agent.modules.rag import create_retriever

backend = create_retriever("real", local_files_only=False)
```

模型缓存在Hugging Face缓存目录，可使用 `HF_HOME` 指定位置。模型权重不要提交到仓库。
部署时应显式安装依赖、准备模型缓存并检查初始化是否成功。

### 1.2 推荐方式：启动时创建，依赖注入

```python
from banking_agent.modules.rag import create_retriever

# 应用启动时执行一次；默认local_files_only=True。
rag_backend = create_retriever("real")

# 请求处理阶段复用同一个对象。
result = rag_backend.retrieve(
    query="How much does replacing a lost card cost?",
    top_k=5,
)
```

构造时完成语料加载、BM25索引和重排模型初始化。不要在每次请求里创建实例。

可配置参数：

| 参数 | 默认值 / 用途 |
| --- | --- |
| `jsonl_path` | `chunks/NovaBank_knowledge_chunks_v1_1.jsonl` |
| `faq_path` | `chunks/NovaBank_faq_chunk_mapping_v1_1.jsonl` |
| `candidate_k` | 20；BM25候选数量 |
| `model_name` | 上述Cross-Encoder模型名，也可指定本地模型目录 |
| `revision` | 上述固定commit；换模型时需同时指定对应revision |
| `local_files_only` | `True`；只使用本地模型缓存 |

当 `top_k > candidate_k` 时，候选池扩大至至少 `top_k`。
目前记录的开发集指标对应候选20、输出5，其他配置需要重新评测。

语料、FAQ映射或模型配置变化后，应在受控启动流程中新建实例。已有实例不会在查询时监控磁盘变化。

### 1.3 兼容函数式入口

```python
from banking_agent.modules.rag import configure_retriever, retrieve

# 仅在应用启动时配置；不要在并发请求期间切换全局后端。
configure_retriever("real")

result = retrieve("card replacement fees", top_k=5)
```

**模块级入口默认仍为Mock。E联调真实检索时必须显式配置 `real`。**
初始化失败不会自动切换到Mock。多应用或测试隔离场景优先使用依赖注入。

## 2. 返回契约

主调用签名：

```python
retrieve(query: str, top_k: int = 5) -> dict
```

返回值严格遵循：

```json
{
  "status": "ok",
  "data": {
    "docs": [
      {
        "document_id": "chunk_id",
        "title": "Knowledge chunk title",
        "source": "Policy ID | version | source type",
        "score": 1.23,
        "excerpt": "Complete original knowledge chunk content"
      }
    ]
  }
}
```

| 字段 | 含义与使用方式 |
| --- | --- |
| `document_id` | 原始chunk_id；用于定位证据和决策轨迹 |
| `title` | 知识块标题 |
| `source` | Policy标识、版本和可读来源标识；用于引用 |
| `score` | 当前后端的排序分数；真实后端为CE原始相关性分数 |
| `excerpt` | 完整原始知识块正文，不任意截断 |

`score`不是回答正确率、证据充分度或业务决策置信度。BM25、余弦、RRF和CE分数不应直接跨模式比较。
模型编码可能有输入长度限制；这不改变返回的完整 `excerpt`。

返回中的每个文档都使用canonical `RetrievedDocument` 校验。边界会拒绝额外字段、重复ID、非有限分数和不合规状态；真实后端还检查重排器是否修改了证据标题、来源或正文。

### 2.1 三种状态

| 状态 | 含义 | E / C处理 |
| --- | --- | --- |
| `ok` | 检索成功并返回候选 | E记录证据并请求C后检查；不能直接认定可回答 |
| `empty` | 调用成功，没有候选可返回 | E交由C后检查，通常进入 `ABSTAIN` |
| `error` | 非法请求、运行异常或返回数据不合规 | E记录技术失败，走约定安全路径，不当作正常无证据 |

`empty`和`error`都严格返回空文档列表：

```json
{"status": "empty", "data": {"docs": []}}
```

```json
{"status": "error", "data": {"docs": []}}
```

公共函数入口、真实后端及Hybrid主入口会将查询时普通 `Exception` 转换为 `error`。
空query、非正整数top_k也返回error；不会吞掉进程退出或中断信号。
底层BM25方法、直接返回列表的实验方法仍可抛异常，不是E的集成边界。

**启动异常与查询异常不同**：模型缺失、依赖缺失或语料损坏可能使构造函数抛错。E应在启动阶段处理并明确报告初始化失败。

日志只记录异常类型，不输出完整query、证据正文或异常中的敏感值。E仍需记录请求级技术失败和决策轨迹。

## 3. C / E调用顺序和职责边界

```text
用户文本
  → A：理解意图、风险、实体
  → C：前置业务决策
  → 仅允许证据回答路线时，E调用B
  → B：返回ok / empty / error及证据
  → E记录B结果，再调用C检查证据
  → C：最终ANSWER / ABSTAIN等动作
  → E：组织最终回答、来源引用和状态输出
```

高风险场景按团队规则由C决定路由，不能因为B能检索到文档就绕过风险处理。
B不直接改写AgentState、不决定投诉或推荐权限、不生成最终用户回答。

### 3.1 E接收证据示例

以下只展示字段映射，不是完整编排器：

```python
from banking_agent.schemas.state import RetrievedDocument

result = rag_backend.retrieve(user_text, top_k=5)

if result["status"] == "ok":
    state.retrieved_docs = [
        RetrievedDocument.model_validate(doc)
        for doc in result["data"]["docs"]
    ]
    # 下一步：调用C进行证据充分度和业务动作检查。
elif result["status"] == "empty":
    state.retrieved_docs = []
    # 下一步：调用C后检查，通常ABSTAIN。
else:
    state.retrieved_docs = []
    # 下一步：E记录技术失败并进入约定的安全路径。
```

不要将error伪装成正常empty，不要在收到ok后跳过C。

### 3.2 C检查证据时需要注意

- 文档是否回答了问题要求的费用、条件、时限、起算事件和例外。
- 多条件问题是否找齐必要证据；首条相关并不代表全部条件有依据。
- “Policy明确不支持服务”仍然是有效证据，应与“没有可靠信息”区分。
- 返回文档是否只是主题相近，却缺少用户要求的具体事实。
- CE高分仅表示模型认为文本相关，不能单独当作充分度依据。

当前没有启用证据筛选阈值。因此S08无证据路线仍需全链路验证，不能仅凭候选存在就生成答案。

## 4. 每个目录是做什么的

```text
rag/
├── README.md                         本联调指南
├── __init__.py                       包级公共接口
├── retriever.py                      工厂、函数入口、契约校验、场景Mock
├── real_retriever.py                 优化BM25 + Cross-Encoder
├── bm25_retriever.py                 BM25加载、校验和排序
├── hybrid_retriever.py               BM25 / Dense / RRF实验后端
├── cross_encoder_reranker.py         问题与知识块联合评分
├── build_knowledge_chunks.py         知识库重建工具
├── evaluate_retrieval.py             统一离线评测
├── chunks/                          正式检索数据和校验记录
├── chunk_sources/                   人工维护的知识块生成输入
├── faqs/                            FAQ源文件
├── novabank_category_master_policies_enriched_v1_1/
│   ├── policies/                    13份权威Policy
│   ├── reports/                     政策分析和修订记录
│   └── references/                  研究来源登记
├── tests/                           B专属单元与契约测试
├── docs/                            B专属接入与验收文档
├── evaluation/                      人工批准的评测资料
│   └── evidence_filter_v1/           无证据诊断集及审批
└── archive/                         历史实验与旧材料
```

### 4.1 `chunks/`：运行时检索数据

| 文件 | 用途 |
| --- | --- |
| `NovaBank_knowledge_chunks_v1_1.jsonl` | 151块正式语料；每行一个chunk |
| `NovaBank_faq_chunk_mapping_v1_1.jsonl` | FAQ问法与候选块的关联，用作排序提示 |
| `validation_report_v1_1.json` | 生成和一致性检查的详细报告 |
| `corpus_manifest.json` | 数量、必填字段、来源检查和语料哈希摘要 |

语料保留原文件名，没有重复复制为validated_corpus.jsonl。
每块具备chunk_id、title、content、source_type、source_policy_id、source_policy_version、source_document等。
只允许指定来源类型进入索引；分析报告、注册表不参与证据检索。
FAQ候选映射不是人工gold，不能代替Policy依据。

两个校验报告的PASS说明特定检查通过，不代表所有问题都能得到正确答案。

### 4.2 `chunk_sources/`：重建所需输入

`knowledge_chunk_drafts_v1_1.txt` 是人工整理的知识块输入，生成器仍依赖它。
名字带drafts不代表可以删除。在线查询不读取此目录。

修改Policy后，应同步相关FAQ及知识块输入，再重建和检查；生成器不会自动理解Policy变更并改写人工输入。

### 4.3 `faqs/`：231条FAQ

`NovaBank_BANKING77_FAQs_v1_1.md` 覆盖77个intent，保存问题、替代表达、回答和Policy来源。
主要用于维护和构建FAQ候选映射；在线查询不逐次解析此Markdown。
业务事实以对应版本的Policy为准。

### 4.4 政策来源包

`novabank_category_master_policies_enriched_v1_1/` 保存完整来源追溯资料：

| 文件 / 子目录 | 用途 |
| --- | --- |
| `policies/` | 13个业务类别的权威政策正文；冲突时回到这里确认 |
| `reports/` | 类别分析、跨类别审查和修订登记；不作为回答证据 |
| `references/` | 研究参考登记；不是NovaBank生效政策 |
| `manifest.json` | 政策清单、版本、路径、哈希与资料排除规则 |
| `banking77_mapping.json` | 77个intent与业务类别的映射 |
| `novabank_shared_terms.json` | 跨政策共享术语和约定 |
| `validation_report.json` | 政策包层面的检查 |
| `README.md` | 政策包使用及权威性说明 |

这些资料用于维护和追溯；当前真实后端索引的是生成后的JSONL，不是每次扫描Policy目录。

### 4.5 `evaluation/`：检索标准答案

- `dev.jsonl`：76条开发题，用于诊断与调参。
- `test.jsonl`：32条冻结题，最终验收时才运行。
- `manifest.json`：108条原gold审批、分组及文件哈希。
- `evidence_filter_v1/diagnostics.jsonl`：24条新增已批准no_evidence题，加16条复用dev对照。
- `evidence_filter_v1/manifest.json`、`REVIEW.md`：审批信息、哈希和人工清单。

三类标签：supported有支持证据；unsupported有明确不支持服务的证据；no_evidence没有问题所需可靠信息。
16条对照已存在于dev，联合评测不能重复统计。
新增诊断题的审批不等于筛选算法通过验收。

### 4.6 `archive/`：历史材料

`pre_integration_20261016.zip` 保存历史实验、完整排名、旧质量报告、重复说明和过期测试。
内含原仓库相对路径与ARCHIVE_SHA256.json，已通过完整性和逐文件哈希校验。
需要复查时解压到临时目录，不直接覆盖当前交付。归档不在查询路径加载。

## 5. 检索组件如何协作

当前选定后端：

```text
RealRetriever
  → BM25Retriever：优化召回前20
  → CrossEncoderReranker：重排、默认取5
  → 严格契约校验
  → 返回完整证据
```

`HybridRetriever` 已独立封装BM25、Dense和RRF，供消融实验使用；不是当前默认真实后端。
如确需调用：

```python
backend = create_retriever(
    "hybrid",
    jsonl_path="src/banking_agent/modules/rag/chunks/NovaBank_knowledge_chunks_v1_1.jsonl",
    local_files_only=True,
)
result = backend.retrieve("card replacement fees", top_k=5)
```

该模式还需要缓存Embedding模型；RRF按排名融合，不直接相加BM25和余弦分数。
E应使用公共工厂和retrieve，而不是自行拼接B内部算法。

## 6. 测试、评测与验收状态

从仓库根目录执行：

```sh
PYTHONPATH=src python -m unittest discover -s src/banking_agent/modules/rag/tests/unit -v
PYTHONPATH=src python -m unittest discover -s src/banking_agent/modules/rag/tests/integration -v

# 只校验已批准数据与来源，不运行检索。
PYTHONPATH=src python -m banking_agent.modules.rag.evaluate_retrieval --validate-only

# 使用新的输出目录，避免覆盖结果；默认dev。
PYTHONPATH=src python -m banking_agent.modules.rag.evaluate_retrieval \
  --backend real --output-dir /tmp/rag-dev-new
```

评测支持real、bm25、dense、hybrid。test仅在冻结方案后显式指定 `--split test`。

最近一次整理验收：49项单元测试、4项契约集成测试通过；151块内容哈希保持不变。
真实模型dev结果精确复现此前重排方案：

| 指标 | 结果 |
| --- | ---: |
| Hit@1 | 78.87% |
| Recall@5 | 95.07% |
| 多块必要证据全部命中@5 | 5/6 |

记录见仓库 `src/banking_agent/modules/rag/docs/acceptance.json`。这些是开发集结果，不是独立测试性能。
当前test未运行；无证据识别仍有明显缺口；完整C/E编排与业务E2E验收尚需集成方完成。

## 7. C / E联调检查清单

- [ ] E启动时显式选择real，依赖和本地模型准备完成。
- [ ] E复用同一实例，不在请求中重新构建索引或切换全局后端。
- [ ] ok文档能映射到canonical RetrievedDocument并保留完整来源和正文。
- [ ] empty与error分别处理，技术失败不会被当作成功答案。
- [ ] C在B返回后执行证据充分度检查，而不是将ok或高分等同于ANSWER。
- [ ] 多块问题检查全部必要证据，明确不支持服务的条款得到正确处理。
- [ ] 高风险路线仍由C控制，E不绕过前置决策调用B。
- [ ] E最终回答基于获准证据，并记录document_id、引用和决策轨迹。

## 8. 团队权威参考

- [模块职责](../../../../docs/module_ownership.md)
- [模块接口契约](../../../../docs/module_api_contract.md)
- [场景与验收要求](../../../../docs/scenario_table.md)
- [工程规范](../../../../docs/engineering_conventions.md)
- [canonical State](../../schemas/state.py)
- [canonical enums](../../schemas/enums.py)

字段名和枚举以可执行schema为准。本文用于接入说明，不修改C/E的职责和共享契约。
