## NovaBank Category Master Policies — Enriched v1.1

已完成剩余12个Category、70个intent的公开FAQ对照增强，并收录上一轮card_lifecycle v1.1，合计13类、77个BANKING77标签。政策正文为英文，12份本轮分析报告为中文。

NovaBank为虚构银行；公开资料仅提供运营主题参考，不决定NovaBank费率、限额、法律责任或支持范围。数字是合成设计，不能作为真实银行政策使用。

### PART 1 / PART 2 文件索引

| Category | Intents | PART 1: 分析及扩类报告 | PART 2: 完整增强政策 |
| --- | ---: | --- | --- |
| `card_lifecycle` | 7 | [分析报告](reports/card_lifecycle_analysis.md) | [完整政策](policies/NovaBank_card_lifecycle_master_policy.md) |
| `card_usage_and_access` | 8 | [分析报告](reports/card_usage_and_access_analysis.md) | [完整政策](policies/NovaBank_card_usage_and_access_master_policy.md) |
| `currency_exchange` | 4 | [分析报告](reports/currency_exchange_analysis.md) | [完整政策](policies/NovaBank_currency_exchange_master_policy.md) |
| `card_payments` | 7 | [分析报告](reports/card_payments_analysis.md) | [完整政策](policies/NovaBank_card_payments_master_policy.md) |
| `cash_withdrawals` | 7 | [分析报告](reports/cash_withdrawals_analysis.md) | [完整政策](policies/NovaBank_cash_withdrawals_master_policy.md) |
| `card_top_ups` | 9 | [分析报告](reports/card_top_ups_analysis.md) | [完整政策](policies/NovaBank_card_top_ups_master_policy.md) |
| `security_and_unrecognised_transactions` | 6 | [分析报告](reports/security_and_unrecognised_transactions_analysis.md) | [完整政策](policies/NovaBank_security_and_unrecognised_transactions_master_policy.md) |
| `account_management` | 5 | [分析报告](reports/account_management_analysis.md) | [完整政策](policies/NovaBank_account_management_master_policy.md) |
| `bank_transfers` | 12 | [分析报告](reports/bank_transfers_analysis.md) | [完整政策](policies/NovaBank_bank_transfers_master_policy.md) |
| `virtual_cards` | 4 | [分析报告](reports/virtual_cards_analysis.md) | [完整政策](policies/NovaBank_virtual_cards_master_policy.md) |
| `cash_and_cheque_deposits` | 2 | [分析报告](reports/cash_and_cheque_deposits_analysis.md) | [完整政策](policies/NovaBank_cash_and_cheque_deposits_master_policy.md) |
| `identity_verification` | 4 | [分析报告](reports/identity_verification_analysis.md) | [完整政策](policies/NovaBank_identity_verification_master_policy.md) |
| `refunds` | 2 | [分析报告](reports/refunds_analysis.md) | [完整政策](policies/NovaBank_refunds_master_policy.md) |

### 对B-RAG的使用方式

1. 当前知识索引只载入 `policies/` 的13个md；参考网页、reports、README和JSON登记文件不作为NovaBank客服规则入库。
2. 解析YAML frontmatter，并按 `##` / `###` 分割；每个chunk保留policy_id、category、included_intents、version、effective_date、synthetic、source_type。从intent标题另取该chunk的精确intent，不把整份included_intents误当成每段都涉及全部标签。
3. 意图映射直接使用本包的banking77_mapping.json，保留 `Refund_not_showing_up` 的大小写和 `reverted_card_payment?` 的问号。13类是项目业务分组，BANKING77本身提供的是77标签。
4. 对2026-10-11及以后的模拟事件选择v1.1。v1.0单独存为历史版本；不要把旧77份逐intent草稿、旧Category政策与本包一同设为当前权威。
5. 一个intent chunk须包含处理条件、费用／期限、验证、边界和新增例外。小块检索需补取共享日历／限额／证据章节；可按Related Intents扩展检索，但不得扩展产品。
6. B-RAG负责检索证据，不执行冻结、转账或退款。风险和投诉状态交由C，模拟执行交由E；资料不全用CLARIFY，政策证据不足用ABSTAIN。

### 扩类结论

当前13类足以承载本次增强。保留不支持现金／支票、direct debit、国际转账、信用／透支、企业／联名／未成年人账户的明确边界。只有在团队决定真的扩展产品时，才另行设计credit_and_overdraft、international_transfers等类别及映射；不因参考页面出现产品就自动加类。已有security_and_unrecognised_transactions承载当前欺诈调查，不重复创建同义类别。

### 溯源与检查

[官方参考登记](references/REFERENCE_REGISTER.md)记录27个URL，其中24个用于本轮其余12类、3个来自上一轮生命周期增强。没有分发整站抓取文本，也没有声称保存了网页快照。来源包含不同地区，差异在每份报告中说明。

[校验报告](validation_report.json)核对13政策、77标签覆盖、70个新增intent块、frontmatter、标题、版本、旧文件未改及card_lifecycle保留。[变更登记](reports/enrichment_change_register.json)逐intent记录合成新增规则和参考主题来源。[跨类审阅](reports/CROSS_CATEGORY_REVIEW.md)记录共同约束及本轮校正。上述检查不等于已测得召回率或法律合规认证。

### FAQ retrieval-expression preparation

[`../build_knowledge_chunks.py`](../build_knowledge_chunks.py) parses primary questions and all alternative questions, checks FAQ source/category/version metadata, and emits these preparation artifacts:

- `../chunks/NovaBank_knowledge_chunks_v1_1.jsonl`: policy-authoritative content with compact retrieval hints.
- `../chunks/NovaBank_faq_chunk_mapping_v1_1.jsonl`: one row per FAQ, preserving every expression under one `faq_id`, and ranked intent-scoped candidate chunks.
- `../chunks/validation_report_v1_1.json`: expression coverage, unmatched FAQs, output hashes and policy clarification trace.

Candidate links require the same policy ID, version and category plus explicit primary/related intent applicability. Lexical scores rank candidates; they do not certify sufficient evidence or permission to answer. The mapping is a separate query-matching input, not policy evidence. A future retriever should index expressions, group hits by `faq_id`, retrieve candidate policy chunks and verify evidence; scoring multiple alternative questions must not fill top_k with duplicates of one FAQ. FAQ answers, this README and validation JSON remain outside the policy-evidence index. This builder does not implement live retrieval or measure Recall@5.
