## PART 1: Analysis & Expansion Report — `card_usage_and_access`

审阅日期：2026-10-11。覆盖 8 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_card_usage_and_access_master_policy.md)。

### Missing Rules Added

- 区分实体卡关联、激活与钱包token；禁止凭关联状态判断卡已可用。
- 补充PIN重试停止条件、换PIN后的首次验证、接触式与非接触式故障分流。
- 说明多个设备共享消费限额，解除冻结不会重启已撤销的钱包token。

### Category Recommendation

现有13类足够。钱包取现、附属卡及其他发行网络仍不支持；无需增加类别。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-01: DBS — Reset Card PIN](https://www.dbs.com.sg/ibanking/help/reset-card-pin.html) | Secure PIN reset and avoiding predictable PINs. | Card types and PIN lengths differ; NovaBank uses four digits. |
| [REF-02: DBS — Unable to Withdraw and Transact](https://www.dbs.com.sg/personal/support/bank-atm-debit-card-unable-to-withdraw.html) | Diagnose activation, usable funds and card controls before replacement. | Real-bank delivery and authentication channels are not adopted. |
| [REF-03: DBS — Lock your Card Temporarily using Payment Controls](https://www.dbs.com.sg/personal/support/card-temp-lock-card.html) | Distinguish temporary protective controls from permanent cancellation. | NovaBank action timings and token treatment are synthetic. |
| [REF-18: Revolut — My Single-Use Virtual Card Is Not Working](https://help.revolut.com/help/cards/card-issue/my-disposable-virtual-card-is-not-working/) | Single-use restrictions and refunds after credential retirement. | NovaBank issuance counts, expiry and purchase caps are independent design choices. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`card_linking`, `card_not_working`, `pin_blocked`, `contactless_not_working`, `card_acceptance`, `visa_or_mastercard`, `change_pin`, `apple_pay_or_google_pay`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
