# Part A 成果说明：Intent / Risk / Entity

**负责人：** A（GitHub: `llsosu-zxy`）  
**模块目录：** `src/banking_agent/modules/intent/`  
**最终状态：** 已完成并合入 `main`（PR #5，合并提交 `66f6b1e`）

## 1. 分工定位

Part A 是整条语音银行 Agent 流水线的感知层：E 在每一轮用户文本请求开始时调用 A，A 返回结构化的意图、置信度、风险等级和实体，供 C 的规则/状态机做业务决策。

A 的职责边界是“理解”，不是“决策”：

- 输入：`session_id`、`user_text`。
- 输出：`{status, data: {intent, confidence, risk_level, entities}}`。
- 不返回 `action`、`reason_code`、`next_state` 或 `final_response`。
- 不读取投诉状态、handoff 状态或 consent，因此不能决定是否允许推荐或是否升级。

## 2. 交付物总览

| 交付要求 | 对应实现 | 状态 |
| --- | --- | --- |
| BANKING77 标签空间与映射 | `banking77.py` | 完成 |
| Intent classification | `mock.py`、`classifier.py` | 完成 |
| Risk detection | `taxonomy.py`、`mock.py` | 完成 |
| Entity extraction | `taxonomy.py`、`mock.py` | 完成 |
| `classify(text)` 接口 | `mock.py`、`adapter.py` | 完成 |
| Macro-F1 实验 | `scripts/train_intent_baseline.py` | 完成 |
| 0.9307 模型组合交付 | `model_artifacts/`、`encoder_classifier.py` | 完成 |
| 模型导出与校验 | `scripts/export_encoder_classifier.py`、`manifest.json` | 完成 |
| 单元测试与契约测试 | `tests/unit/test_intent_module.py`、`tests/unit/test_encoder_classifier.py`、`tests/integration/test_intent_adapter.py` | 完成 |
| 模块文档 | `docs/intent_module.md`、`docs/results_intent_baseline.md` | 完成 |
| E 的异步集成接口 | `IntentModuleAdapter` | 完成 |

## 3. 核心实现

### 3.1 Intent classification

模块提供三条实现路径，共用同一个 `UnderstandingResult` 输出：

- Phase-one 确定性路径：`classify(text)` 直接实现契约。S01–S08 的 `intent / confidence / risk_level` 使用场景表约定的固定值；其他文本走加权关键词规则，保证 mock 阶段可重复、可测试。
- Phase-two 通用训练路径：`TrainedIntentClassifier` 加载 joblib 序列化的 BANKING77 77 类模型，把细粒度标签映射为运营意图，并以“预测标签所属路由的概率质量”作为置信度。
- 已发布编码器路径：`EncoderIntentClassifier` 加载本次交付的冻结 MiniLM + LogisticRegression 组合，使用 NumPy softmax 推理，不要求运行时安装 scikit-learn。

运营意图共 6 个，另加 `UNKNOWN`：

`card_fee_enquiry`、`fee_complaint`、`unauthorized_transaction`、`fraud_suspicion`、`product_recommendation`、`policy_enquiry`、`UNKNOWN`。

主要接口：

| 接口 | 用途 |
| --- | --- |
| `classify(text) -> UnderstandingResult` | 主入口；固定场景值 + 规则泛化 |
| `classify_by_rules(text)` | 只走规则层，用于检查泛化能力 |
| `score_intent(text)` | 返回 `(intent, confidence)` |
| `analyze(payload)` | 同步契约适配器，输入 `{session_id, user_text}` |
| `IntentModuleAdapter().analyze(session_id, user_text)` | E 使用的异步适配器 |
| `TrainedIntentClassifier.load(path).classify(text)` | 可选的训练模型入口 |
| `EncoderIntentClassifier.from_pretrained().classify(text)` | 已发布的 0.9307 模型入口 |

规则层置信度使用 `0.50 + 0.09 × 规则得分`，上限 0.95；无匹配时返回 `UNKNOWN` 和 0.31。该置信度是启发式分数，不是校准概率；训练路径使用校准后的路由概率质量。

### 3.2 Risk detection

BANKING77 没有风险标签，因此风险不是模型输出，而是独立、可审计的规则层：

```text
risk = max(短语层风险, 意图基线风险)
```

- 高风险短语：`without my permission`、`unauthorised`、`scam`、`fraud`、`stolen`、`hacked`、`suspicious`、`not me`、`someone used`、OTP 等。
- 中风险短语：`charged twice`、`overcharged`、`wrong amount`、`dispute`、`refund`、`declined`、`failed`、`pending` 等。
- 意图基线：欺诈/未授权为 HIGH，费用投诉为 MEDIUM，其余为 LOW。

两个不变量：

- 高风险短语不会被低意图置信度降级。
- `RiskLevel.UNKNOWN` 表示“无法判断”，不等于 `LOW`；S07 返回 `UNKNOWN`。

风险等级只是给 C 的信号，A 不据此做升级或拒答决定。

### 3.3 Entity extraction

实体类型在 `taxonomy.py` 中冻结为 9 类：

`payment_method`、`amount`、`currency`、`date`、`relative_time`、`account_type`、`product`、`channel`、`transaction_reference`。

实现方式：

- Gazetteer 最长短语优先，避免 `credit card` 同时被识别成 `card`。
- 金额、币种、日期、相对时间、交易参考号使用正则。
- Gazetteer 匹配置信度 0.90，正则匹配置信度 0.85。
- 月份只有在带日、带年或带日期介词时才识别，避免把情态动词 `may`、动词 `march` 当作日期。
- 金额、日期和账户参考号采取保守策略，由 E 在执行前向用户确认。

### 3.4 BANKING77 映射

`banking77.py` 保存 77 个官方标签及发布顺序，并提供到运营意图的桥接：

- 77 个标签全部覆盖。
- 19 个标签显式映射到风险/费用路由。
- 58 个长尾标签默认落到 `policy_enquiry`。
- BANKING77 中没有 `fraud_suspicion`、`fee_complaint`、`product_recommendation` 的原生标签；这三类主要由规则层和场景文本覆盖。

`scripts/validate_intent_mapping.py --check` 可验证标签完整性、路由合法性，以及 B 的 `banking77_mapping.json` 标签集合是否与 A 一致，防止两个模块的 77 类标签空间漂移。

### 3.5 E 集成接口

E 的 orchestrator 协议要求：

```python
async def analyze(self, session_id: str, user_text: str) -> IntentResult | RawResult
```

A 提供 `IntentModuleAdapter` 实现该协议：

```python
adapter = IntentModuleAdapter()
result = await adapter.analyze(session_id, user_text)
```

返回的映射可直接通过 `IntentResult`（`ModuleResult[UnderstandingResult]`）校验。技术错误返回 `{"status": "error", "data": null}`，避免 E 的 `extra="forbid"` 校验失败。

训练模型可通过注入使用，不改变 E 的调用点：

```python
adapter = IntentModuleAdapter(
    classifier=TrainedIntentClassifier.load(path).classify
)
```

已发布模型使用同一注入方式：

```python
from banking_agent.modules.intent import EncoderIntentClassifier

classifier = EncoderIntentClassifier.from_pretrained()
adapter = IntentModuleAdapter(classifier=classifier.classify)
```

`session_id` 只为协议兼容而接收，A 不读取也不写入会话状态。

## 4. Macro-F1 实验

### 4.1 数据与协议

- 数据集：BANKING77（CC-BY-4.0）。
- 规模：10,003 条训练、3,080 条测试、77 个意图。
- 开发集：从训练集分层抽取 12%，固定随机种子 42，用于模型和超参数选择。
- 测试集只在最终模型确定后评分一次，避免用测试集调参。

### 4.2 模型对比

| 模型 | Dev Macro-F1 | Test Macro-F1 | Test accuracy |
| --- | ---: | ---: | ---: |
| Majority class | 0.0005 | 0.0003 | 0.0130 |
| TF-IDF + ComplementNB | 0.8014 | 0.7934 | 0.7990 |
| TF-IDF + LogisticRegression | 0.8584 | 0.8726 | 0.8724 |
| TF-IDF + LinearSVC | 0.8891 | 0.8940 | 0.8938 |
| TF-IDF + 校准 LinearSVC | 0.8895 | 0.8903 | 0.8903 |
| 冻结 all-MiniLM-L6-v2 + LogisticRegression | 0.9213 | **0.9307** | 0.9312 |

最终按 dev Macro-F1 选择 `encoder_logreg`，测试集 Macro-F1 为 **0.9307**，accuracy 为 **0.9312**。

### 4.3 路由级结果

把 77 类预测映射为运营意图后，测试集结果：

| 路由 | F1 | Support |
| --- | ---: | ---: |
| `card_fee_enquiry` | 0.9645 | 240 |
| `fee_complaint` | 0.9694 | 280 |
| `fraud_suspicion` | 0.9426 | 120 |
| `policy_enquiry` | 0.9922 | 2320 |
| `unauthorized_transaction` | 0.9333 | 120 |

路由 Macro-F1 **0.9604**，accuracy **0.9838**。`product_recommendation` 不在 BANKING77 中，因此不参与该数据集评分。

### 4.4 主要误差

测试集上最弱的意图包括 `transfer_not_received_by_recipient`（0.7952）、`balance_not_updated_after_bank_transfer`（0.8000）、`pending_transfer`（0.8169）。常见混淆如 `card_arrival → card_delivery_estimate`、`card_payment_not_recognised → compromised_card`。后者虽然细粒度错误，但仍落在高风险路由上，不会降低安全等级。

### 4.5 已发布模型组合（0.9307）

本次把实验中胜出的完整推理组合提交到
`src/banking_agent/modules/intent/model_artifacts/`，不是只提交一个准确率数字：

| 组成 | 冻结内容 |
| --- | --- |
| 编码器 | `sentence-transformers/all-MiniLM-L6-v2`，revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`，Apache-2.0 |
| 分类器参数 | `logreg_params.npz`：`coef` 77×384、`intercept` 77、sklearn 类别顺序 |
| 分类器配置 | `C=10.0`、`class_weight="balanced"`、`max_iter=2000`、`random_state=42` |
| 标签顺序 | `label_order.json`：BANKING77 官方发布顺序 77 类 |
| 路由映射 | `route_mapping.json`：77 个 label → 6 个运营意图，19 条显式 + 58 条默认 |
| 文本预处理 | `preprocessing.json`：原始文本直通、tokenizer 大小写/截断、batch 64、L2 归一化 |
| 推理包装 | `encoder_classifier.py`：校验 checksum/标签/路由后用 NumPy softmax 推理 |
| Manifest | `manifest.json`：revision、编码器快照逐文件 SHA-256、指标、依赖版本、入口 |

编码器权重约 90 MB，没有直接提交到 Git。`manifest.json` 固定不可变 revision，
并记录 snapshots 中每个文件的字节数与 SHA-256；`from_pretrained()` 会校验四个本地
参数/配置文件。NumPy 推理与 sklearn `predict` 在测试集上 **0 mismatch**，softmax
概率最大绝对差为 `2.915e-06`。精确依赖记录在 `requirements-inference.txt`；
复现导出使用 `scripts/export_encoder_classifier.py`。

## 5. 测试与验证

- A 专项单元测试：49 个，新增覆盖 manifest/revision、artifact SHA-256、77 类标签顺序、完整路由映射、预处理配置、NumPy 概率与路由概率质量、批量/单条一致性。
- A 契约集成测试：3 个，使用 E 的 `assert_intent_adapter_contract` 校验规则适配器和已发布模型适配器。
- 全仓库回归：104 个 unit、29 个 integration、1 个 e2e，全部通过。
- GitHub Actions：`Python 3.11 tests` 在 PR 和合并后的 `main` 上均为 success。
- Lint：`ruff`（E4/E7/E9/F/I/W，行宽 100）全部通过。
- 映射校验：77 labels、19 条显式路由、58 条默认 `policy_enquiry`。
- 模型导出：dev Macro-F1 0.921297；test Macro-F1 0.930748；test accuracy 0.931169；NumPy/sklearn 0 mismatch。
- 真实编码器 smoke test：成功加载固定 revision，S03 返回合法 `UnderstandingResult` 与 HIGH risk。

核心场景固定值：

| 场景 | Intent | Confidence | Risk |
| --- | --- | ---: | --- |
| S01 | `card_fee_enquiry` | 0.94 | LOW |
| S02 | `fee_complaint` | 0.92 | MEDIUM |
| S03 | `unauthorized_transaction` | 0.97 | HIGH |
| S04 | `fraud_suspicion` | 0.95 | HIGH |
| S05 | `product_recommendation` | 0.91 | LOW |
| S06 | `product_recommendation` | 0.93 | LOW |
| S07 | `UNKNOWN` | 0.31 | UNKNOWN |
| S08 | `policy_enquiry` | 0.88 | LOW |

## 6. 已知限制

- Phase-one 默认使用确定性规则层；`TrainedIntentClassifier` 和 `EncoderIntentClassifier` 都是 opt-in，尚未替换默认 `classify()`。
- `scikit-learn`、`joblib`、`sentence-transformers` 是可选依赖，不是默认运行时依赖；默认安装只需要 `pydantic`。
- 编码器权重未放入 Git，首次使用需要从 Hugging Face 获取固定 revision；本地已有对应缓存时可直接离线加载。
- 训练路径不会主动 abstain，低置信度交由 C 的阈值规则处理；`UNKNOWN` 是 mock 路径的输出。
- BANKING77 不包含欺诈、投诉和推荐的原生意图，这三类主要依赖规则层和场景文本。
- 规则层置信度是启发式分数，不是校准概率；训练路径使用路由概率质量。
- 9 类实体尚未写入 E 维护的 `docs/module_api_contract.md`；当前在 `taxonomy.py` 和模块文档中冻结，正式共享前需要 E/C 确认。
- 实体抽取偏保守，金额、日期、账户参考号应由 E 在执行前向用户确认。

## 7. 复现方式

```powershell
$env:PYTHONPATH="src;tests"

# A 单元测试与适配器契约测试
python -m unittest discover -s tests/unit -p "test_intent_module.py" -v
python -m unittest discover -s tests/integration -p "test_intent_adapter.py" -v

# 全仓库回归
python -m unittest discover -s tests/unit
python -m unittest discover -s tests/integration
python -m unittest discover -s tests/e2e

# 映射校验
.venv\Scripts\python.exe scripts\validate_intent_mapping.py --check

# Macro-F1 实验（可选依赖：scikit-learn、joblib、sentence-transformers）
.venv\Scripts\python.exe scripts\train_intent_baseline.py --encoder

# 导出并验证已发布的 0.9307 组合
.venv\Scripts\python.exe scripts\export_encoder_classifier.py
python -m unittest discover -s tests/unit -p "test_encoder_classifier.py" -v
```

原始 CSV 放在 `data/raw/banking77/`，实验生成物写入 `data/processed/`，均被 `.gitignore` 排除。已发布的小型参数/配置 artifact 位于 `model_artifacts/` 并纳入版本控制；90 MB 编码器权重通过 HF revision 固定。

## 8. 文件索引

| 文件 | 作用 |
| --- | --- |
| `src/banking_agent/modules/intent/taxonomy.py` | 意图、风险短语、实体词表和正则 |
| `src/banking_agent/modules/intent/mock.py` | 规则分类、风险检测、实体抽取、同步契约适配器 |
| `src/banking_agent/modules/intent/banking77.py` | 77 类标签空间与运营意图映射 |
| `src/banking_agent/modules/intent/classifier.py` | 可选训练分类器与路由概率质量置信度 |
| `src/banking_agent/modules/intent/encoder_classifier.py` | 已发布 MiniLM + LogisticRegression 的 NumPy 推理包装与完整性校验 |
| `src/banking_agent/modules/intent/model_artifacts/` | 0.9307 参数、77 标签、路由、预处理、manifest、依赖与 README |
| `src/banking_agent/modules/intent/adapter.py` | E 使用的异步 `IntentModuleAdapter` |
| `src/banking_agent/modules/intent/__init__.py` | 模块导出 |
| `scripts/train_intent_baseline.py` | Macro-F1 基线阶梯、编码器档、模型保存 |
| `scripts/export_encoder_classifier.py` | 固定 revision 重训并导出可发布模型组合 |
| `scripts/validate_intent_mapping.py` | 标签/路由/与 B 注册表一致性校验 |
| `tests/unit/test_intent_module.py` | A 专项单元测试 |
| `tests/unit/test_encoder_classifier.py` | 模型 artifact、checksum、标签/路由和推理测试 |
| `tests/integration/test_intent_adapter.py` | 基于 E 契约 harness 的适配器测试 |
| `docs/intent_module.md` | 模块接口、风险、实体、BANKING77、限制说明 |
| `docs/results_intent_baseline.md` | 自动生成的实验报告 |

## 9. 交付记录

- 功能提交：`307e286 feat(a): add intent, risk, and entity module`
- Pull Request：#5
- 合并提交：`66f6b1e Merge pull request #5 from softfish-tech/feature/a-intent-mock`
- 合并后 CI：success
- 分支状态：`feature/a-intent-mock` 已删除

A 部分已完成交付并通过全量回归，代码位于 `main`，可直接供 E 的 `ModuleBundle` 注入使用。
