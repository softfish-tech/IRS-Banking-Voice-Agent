## PART 1: Analysis & Expansion Report — `bank_transfers`

审阅日期：2026-10-11。覆盖 12 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_bank_transfers_master_policy.md)。

### Missing Rules Added

- 补充收款银行选择错误、失效账户、错转后的请求人与收款方配合条件。
- 区分取消pending与召回completed；说明凭回执不能造账或保证追回。
- 补充日期／状态／可用余额差异、退回款实际收讫后入账，以及一笔reference一宗trace。

### Category Recommendation

现有13类足够。海外汇款应另设international_transfers；本次仍只支持境内SGD。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-16: DBS — Made a Funds Transfer to a Wrong Recipient?](https://www.dbs.com.sg/personal/support/bank-local-wrong-funds-transfer.html) | Completed-transfer recall needs receiving-side cooperation; recovery cannot be guaranteed. | Real recall timeframes and legal conclusions are not adopted. |
| [REF-17: DBS — Unsuccessful Fund Transfer to Another Bank Account](https://www.dbs.com.sg/personal/support/bank-local-unsuccessful-transfer.html) | Wrong bank/account selection, inactive destinations and returned transfers. | Retry only after NovaBank confirms the original final status. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`top_up_by_bank_transfer_charge`, `cancel_transfer`, `transfer_not_received_by_recipient`, `declined_transfer`, `pending_transfer`, `transfer_timing`, `beneficiary_not_allowed`, `transfer_fee_charged`, `receiving_money`, `failed_transfer`, `transfer_into_account`, `balance_not_updated_after_bank_transfer`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
