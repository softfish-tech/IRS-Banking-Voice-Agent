> 历史质量审计。对应结构化报告与旧检查脚本已归档于 src/banking_agent/modules/rag/archive/pre_integration_20261016.zip。当前语料状态以 chunks/validation_report_v1_1.json 与 corpus_manifest.json 为准。

# NovaBank 知识质量复检 — 2026-10-14

**此前 3 项问题均已修正并通过针对性复检。** 151 个知识块及原有 ID、77 个意图、231 条 FAQ 保持完整。

## 已完成的修正

| 问题 | 修正 | 范围 |
| --- | --- | --- |
| KQ-001：退款上限 | 新增退款 ≤ 原始本金减已退款；累计退款 ≤ 原始本金，避免重复扣减 | Policy、FAQ、草稿、退款上限块 |
| KQ-002：非工作日配送 | 14:00 截止仅适用于工作日；晚于截止或非工作日接受，Day 0 顺延到下一工作日 | 构建逻辑及 7 个配送块 |
| KQ-003：身份复核起点 | 最终决定通过安全 App 或注册渠道通知后起算 30 个自然日；内部记录或补交资料不重启期限 | Policy、FAQ、草稿、身份复核块 |

## 验证

- 9 项 RAG 回归测试全部通过，包括既有 FAQ 替代表达与重建一致性检查。
- 来源政策哈希、构建校验报告与 FAQ 映射均已同步重建。
- 结构校验状态 PASS；两块为保留完整条件略超过建议长度，不强行拆分。
- 跨类别 10,321 对组合重新扫描后仍有 20 对候选：7 对可抽取共享子规则，13 对保留业务区分。未自动删除或合并任何块。

## 跨类别候选

| ID | 块 A | 块 B | 余弦 | 判定 |
| --- | --- | --- | ---: | --- |
| DQ-001 | NB-v1_1-lost_or_stolen_phone-002 | NB-v1_1-passcode_forgotten-002 | 0.4805 | 可抽取共享子规则 |
| DQ-002 | NB-v1_1-exchange_charge-002 | NB-v1_1-card_payment_fee_charged-002 | 0.4215 | 保留业务区分 |
| DQ-003 | NB-v1_1-exchange_charge-001 | NB-v1_1-atm_support-002 | 0.4204 | 可抽取共享子规则 |
| DQ-004 | NB-v1_1-edit_personal_details-002 | NB-v1_1-verify_my_identity-001 | 0.3969 | 保留业务区分 |
| DQ-006 | NB-v1_1-receiving_money-003 | NB-v1_1-verify_source_of_funds-001 | 0.3845 | 可抽取共享子规则 |
| DQ-005 | NB-v1_1-lost_or_stolen_phone-002 | NB-v1_1-edit_personal_details-001 | 0.3838 | 保留业务区分 |
| DQ-008 | NB-v1_1-order_physical_card-004 | NB-v1_1-edit_personal_details-003 | 0.37 | 可抽取共享子规则 |
| DQ-007 | NB-v1_1-card_payment_fee_charged-002 | NB-v1_1-wrong_exchange_rate_for_cash_withdrawal-001 | 0.3699 | 保留业务区分 |
| DQ-009 | NB-v1_1-top_up_failed-002 | NB-v1_1-failed_transfer-002 | 0.3661 | 保留业务区分 |
| DQ-010 | NB-v1_1-pin_blocked-001 | NB-v1_1-passcode_forgotten-001 | 0.3568 | 保留业务区分 |
| DQ-011 | NB-v1_1-card_payment_wrong_exchange_rate-001 | NB-v1_1-wrong_exchange_rate_for_cash_withdrawal-001 | 0.3518 | 保留业务区分 |
| DQ-012 | NB-v1_1-top_up_by_card_charge-002 | NB-v1_1-transfer_fee_charged-002 | 0.3456 | 保留业务区分 |
| DQ-013 | NB-v1_1-exchange_charge-001 | NB-v1_1-card_payment_fee_charged-001 | 0.3415 | 可抽取共享子规则 |
| DQ-014 | NB-v1_1-card_swallowed-002 | NB-v1_1-lost_or_stolen_card-002 | 0.3409 | 可抽取共享子规则 |
| DQ-015 | NB-v1_1-card_acceptance-001 | NB-v1_1-atm_support-001 | 0.3399 | 保留业务区分 |
| DQ-016 | NB-v1_1-contactless_not_working-001 | NB-v1_1-declined_card_payment-001 | 0.3396 | 保留业务区分 |
| DQ-017 | NB-v1_1-pending_cash_withdrawal-002 | NB-v1_1-cash_withdrawal_not_recognised-002 | 0.3351 | 保留业务区分 |
| DQ-019 | NB-v1_1-exchange_rate-002 | NB-v1_1-card_payment_wrong_exchange_rate-001 | 0.3312 | 保留业务区分 |
| DQ-018 | NB-v1_1-exchange_rate-002 | NB-v1_1-card_payment_fee_charged-001 | 0.3309 | 可抽取共享子规则 |
| DQ-020 | NB-v1_1-top_up_failed-001 | NB-v1_1-failed_transfer-002 | 0.325 | 保留业务区分 |

详细 JSON 保留原始发现及修正前证据，并记录当前块内容、来源定位和复检结果。原先的 142 个未新增问题块未被当作重新获得完整语义认证；本次关闭的是已识别的 3 项问题。词法候选分数不是重复概率，也不是检索效果评测。
