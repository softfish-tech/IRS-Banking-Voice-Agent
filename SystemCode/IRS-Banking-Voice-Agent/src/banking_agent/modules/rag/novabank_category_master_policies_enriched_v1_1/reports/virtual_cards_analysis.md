## PART 1: Analysis & Expansion Report — `virtual_cards`

审阅日期：2026-10-11。覆盖 4 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_virtual_cards_master_policy.md)。

### Missing Rules Added

- 补充商户零额测试、多次授权、分拆订单及保存卡号的兼容性边界。
- 明确一次性卡以一次批准消费为耗用点；失败授权不耗用，已退役卡仍能匹配原交易退款。
- 补充安全显示卡资料、被替换卡不会自动迁移订阅、实体与虚拟限额共享。

### Category Recommendation

现有13类足够。信用虚拟卡、企业员工卡和钱包ATM不支持；无需扩类。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-18: Revolut — My Single-Use Virtual Card Is Not Working](https://help.revolut.com/help/cards/card-issue/my-disposable-virtual-card-is-not-working/) | Single-use restrictions and refunds after credential retirement. | NovaBank issuance counts, expiry and purchase caps are independent design choices. |
| [REF-19: Revolut — What Is a Virtual Card](https://help.revolut.com/en-IN/help/cards/virtual-cards/question-how-to-use-a-virtual-card/) | Separate reusable from one-use credentials and protect access to card details. | No India-specific service or product entitlement is adopted. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`getting_virtual_card`, `disposable_card_limits`, `virtual_card_not_working`, `get_disposable_virtual_card`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
