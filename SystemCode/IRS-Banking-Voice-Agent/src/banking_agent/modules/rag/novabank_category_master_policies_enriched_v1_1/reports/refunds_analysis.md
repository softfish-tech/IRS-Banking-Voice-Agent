## PART 1: Analysis & Expansion Report — `refunds`

审阅日期：2026-10-11。覆盖 2 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_refunds_master_policy.md)。

### Missing Rules Added

- 补充商户承诺与实际退款发起的差别，缺失退款所需reference和日期。
- 补充部分退款、退役／一次性卡退款、退款失败后重新发起，以及禁止双重补偿。
- 区分授权释放、网络撤销、商户退款和银行批准补偿；明确各自的计时起点。

### Category Recommendation

现有13类足够。信用账单返款、借贷争议及merchant acquiring退款接口不属于个人借记卡退款政策。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-24: Revolut — Problems with a Refund](https://help.revolut.com/en-LV/help/card-payments-withdrawals/refunds/why-is-my-refund-pending/) | Merchant issuance, incomplete refunds and inactive-card refunds require different traces. | NovaBank uses business-day clocks and its original-rate refund rule. |
| [REF-06: DBS — Guide to Submit Card Transaction Dispute](https://www.dbs.com.sg/personal/support/general-incorrect-transaction.html) | Pending authorisation, settled disputes and duplicate recovery require separate handling. | Do not adopt liability presumptions, real claim windows or temporary-credit promises. |
| [REF-18: Revolut — My Single-Use Virtual Card Is Not Working](https://help.revolut.com/help/cards/card-issue/my-disposable-virtual-card-is-not-working/) | Single-use restrictions and refunds after credential retirement. | NovaBank issuance counts, expiry and purchase caps are independent design choices. |
| [REF-04: DBS — Overseas Card Transaction Fees](https://www.dbs.com.sg/personal/support/card-charges-and-fees-overseas-transaction-fees.html) | Separate settlement-date rates, merchant DCC and issuer charges. | Do not import actual fee rates or refund conversion methods. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`request_refund`, `Refund_not_showing_up`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
