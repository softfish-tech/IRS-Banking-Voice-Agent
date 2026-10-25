# B-RAG 最终联调交付 — 2026-10-16

## 交付定位

当前版本供C/E全链路联调，不代表无可靠证据场景已经通过业务验收。
B返回检索候选；C负责证据充分度及风控裁决；E负责状态与最终回答。
没有启用−6或其他拒答阈值，ok不等于允许回答。

## 启动

```sh
python -m pip install -e '.[rag-dense]'
```

```python
from banking_agent.modules.rag import create_retriever
backend = create_retriever('real')
result = backend.retrieve('card replacement fees', top_k=5)
```

在E启动时创建一次。默认只读本地模型缓存；首次模型准备可显式使用
local_files_only=False。模块级retrieve默认仍为mock，函数式接入需先configure_retriever('real')。
完整用法见src/banking_agent/modules/rag/README.md。

## 包含范围

交付快照包含src、tests、docs、pyproject.toml、README、AGENTS.md、.gitignore及已有项目骨架。
这不是Git diff：原目录没有.git，无法识别与团队当前分支的差异。
合并时应先克隆团队仓库并在feature/b-rag-integration分支审查改动，不直接覆盖团队共享State或他人工作。

未打包：模型权重、虚拟环境、字节码缓存、.env、Git元数据、历史归档ZIP、生成的完整排名结果。
历史归档仍保留在原工作目录，不是运行依赖。当前语料、已审批评测标签、报告及契约测试保留。

## 验收命令

```sh
PYTHONPATH=src python -m unittest discover -s src/banking_agent/modules/rag/tests/unit -v
PYTHONPATH=src python -m unittest discover -s src/banking_agent/modules/rag/tests/integration -v
PYTHONPATH=src python -m banking_agent.modules.rag.evaluate_retrieval --validate-only
```

冻结test未运行。当前记录的真实模型dev指标：Hit@1 78.87%，Recall@5 95.07%，多块全部命中5/6。
固定−6新问法确认未降低8道近域无证据题的误返回，因此不启用为充分度门控。
无证据候选需要C核查所问事实，而不是E据相近主题生成数值。

## 建议PR说明

标题：feat: deliver B-RAG retrieval backend for C/E integration

提供优化BM25候选20与固定Cross-Encoder重排的真实后端，以及BM25/Dense/RRF实验组件。
公共请求入口返回严格的ok/empty/error证据包，保留完整正文和来源；初始化失败明确报错。
提供政策与FAQ追溯、语料重建、已批准评测集、单元和契约测试及C/E接入说明。

未新增AgentState字段或业务动作；C仍拥有充分度和风控决策权。E必须显式选择real后端。
已知限制是无证据拒答与完整C/E E2E尚需联合验收；不将高检索分数作为回答许可。

## 文件归属更新

B专属测试现位于src/banking_agent/modules/rag/tests/，B文档位于同模块docs/；共享State测试和团队契约保留原处。B测试共52项通过，共享State测试4项通过。
