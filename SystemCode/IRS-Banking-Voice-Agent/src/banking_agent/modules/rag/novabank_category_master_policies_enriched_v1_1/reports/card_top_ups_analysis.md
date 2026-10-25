## PART 1: Analysis & Expansion Report — `card_top_ups`

审阅日期：2026-10-11。覆盖 9 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_card_top_ups_master_policy.md)。

### Missing Rules Added

- 补充发卡行认证失败、日期错位、外部双记录与NovaBank单记录的对账。
- 区分技术撤销和外部发卡行争议；禁止把争议冻结当成到账退款。
- 补充自动充值停止、生效时间、72小时pending后的释放指令及其起算点。

### Category Recommendation

现有13类足够。钱包充值、信用卡充值、第三方代充和商业卡充值仍不支持。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-09: Revolut — Card Deposit Limits and Fees](https://help.revolut.com/help/adding-money/card-deposit-limits-and-fees/) | Make counter periods explicit and distinguish bank fees from external issuer fees. | Rolling and adaptive limits differ; retain NovaBank calendar-day/month caps. |
| [REF-10: Revolut — My Card Deposit Did Not Work](https://help.revolut.com/en-IT/help/adding-money/with-card/more-help-with-a-card-deposit/) | Issuer authentication failures, statement date differences and failed-payment references. | Actual waiting times and wallet funding differ; NovaBank retains its own rules. |
| [REF-11: Revolut — Why Was My Top-Up Reverted?](https://help.revolut.com/en-LI/help/adding-money/with-card/more-help-with-adding-money-with-a-card/why-was-my-top-up-reverted/) | Distinguish technical reversals from issuer-disputed funding. | External dispute resolution has no guaranteed NovaBank completion deadline. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`automatic_top_up`, `pending_top_up`, `top_up_limits`, `supported_cards_and_currencies`, `top_up_reverted`, `topping_up_by_card`, `verify_top_up`, `top_up_failed`, `top_up_by_card_charge`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
