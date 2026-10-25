## PART 1: Analysis & Expansion Report — `cash_and_cheque_deposits`

审阅日期：2026-10-11。覆盖 2 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_cash_and_cheque_deposits_master_policy.md)。

### Missing Rules Added

- 补充第三方银行已收现金／支票与NovaBank收到后续电子转账的两层区分。
- 说明真实银行清算流程不能套用于NovaBank；回执不证明NovaBank已收到款项。
- 补充冒充NovaBank存款代理的即时安全升级与替代境内电子转账的准确边界。

### Category Recommendation

现有13类足够且本类必须保留拒绝／澄清知识。若未来开放实物存款，可在本类新增产品规则；本次不编造清算服务。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-20: DBS — Deposit Cash](https://www.dbs.com.sg/personal/support/bank-ssb-deposit-cash.html) | Cash deposit involves an actual accepting bank and an identifiable receipt. | Reference comparison only: NovaBank accepts no physical cash. |
| [REF-21: DBS — Cheque Clearing](https://www.dbs.com.sg/personal/support/bank-cheque-clearing.html) | Deposit receipt, clearing and available funds are separate concepts. | Reference comparison only: NovaBank accepts no cheques and quotes no clearing SLA. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`balance_not_updated_after_cheque_or_cash_deposit`, `top_up_by_cash_or_cheque`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
