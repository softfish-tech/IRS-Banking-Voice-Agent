## PART 1: Analysis & Expansion Report — `card_payments`

审阅日期：2026-10-11。覆盖 7 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_card_payments_master_policy.md)。

### Missing Rules Added

- 区分一笔pending加一笔settled与两笔settled重复扣款。
- 补充酒店／租车预授权、商户更名、分拆入账、金额调整和撤销后补入账。
- 明确冻结不取消既有授权，手续费计算错误与商户争议使用不同处理时钟。

### Category Recommendation

现有13类足够。信用卡分期、账单利息和授信额度若成为产品，应新增credit_and_overdraft；本次不启用。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-04: DBS — Overseas Card Transaction Fees](https://www.dbs.com.sg/personal/support/card-charges-and-fees-overseas-transaction-fees.html) | Separate settlement-date rates, merchant DCC and issuer charges. | Do not import actual fee rates or refund conversion methods. |
| [REF-06: DBS — Guide to Submit Card Transaction Dispute](https://www.dbs.com.sg/personal/support/general-incorrect-transaction.html) | Pending authorisation, settled disputes and duplicate recovery require separate handling. | Do not adopt liability presumptions, real claim windows or temporary-credit promises. |
| [REF-03: DBS — Lock your Card Temporarily using Payment Controls](https://www.dbs.com.sg/personal/support/card-temp-lock-card.html) | Distinguish temporary protective controls from permanent cancellation. | NovaBank action timings and token treatment are synthetic. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`card_payment_wrong_exchange_rate`, `extra_charge_on_statement`, `card_payment_fee_charged`, `pending_card_payment`, `declined_card_payment`, `transaction_charged_twice`, `reverted_card_payment?`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
