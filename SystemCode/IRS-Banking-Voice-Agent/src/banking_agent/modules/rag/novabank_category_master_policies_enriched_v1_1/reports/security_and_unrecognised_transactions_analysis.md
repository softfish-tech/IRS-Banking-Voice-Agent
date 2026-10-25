## PART 1: Analysis & Expansion Report — `security_and_unrecognised_transactions`

审阅日期：2026-10-11。覆盖 6 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_security_and_unrecognised_transactions_master_policy.md)。

### Missing Rules Added

- 补充丢失手机但仍持有卡、丢失卡但能使用App、全部失去访问的不同路线。
- 区分自愿授权诈骗、未知交易和卡资料暴露；均可紧急保护，但退款不保证。
- 明确冻结／撤销token不取消过去授权，不采用48小时自动丧失索赔资格规则。

### Category Recommendation

现有13类足够，已有security_and_unrecognised_transactions可承载当前欺诈调查。未来若新增完整案件调查模块，再评估扩展，不重复建立fraud_investigation。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-12: DBS — Lost or Stolen Card](https://www.dbs.com.sg/personal/support/card-issues-lost-card.html) | Prompt loss reporting and replacement are distinct from transaction investigations. | Actual liability and replacement charges are not adopted. |
| [REF-13: Revolut — Lost or Stolen Device](https://help.revolut.com/en-US/help/profile-and-plan/log-in-issues/my-phone-has-been-lost-or-stolen/) | Lost-device access recovery, session removal and transaction review. | No real contact address, product or recovery channel is reused. |
| [REF-03: DBS — Lock your Card Temporarily using Payment Controls](https://www.dbs.com.sg/personal/support/card-temp-lock-card.html) | Distinguish temporary protective controls from permanent cancellation. | NovaBank action timings and token treatment are synthetic. |
| [REF-08: UOB — ATM Security](https://www.uob.com.sg/online-branch/branch-atm/atm-security.page) | Check ATM safety; report suspicious equipment and unauthorised use promptly. | Do not transplant real-bank alert thresholds or product controls. |
| [REF-06: DBS — Guide to Submit Card Transaction Dispute](https://www.dbs.com.sg/personal/support/general-incorrect-transaction.html) | Pending authorisation, settled disputes and duplicate recovery require separate handling. | Do not adopt liability presumptions, real claim windows or temporary-credit promises. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`lost_or_stolen_card`, `card_payment_not_recognised`, `compromised_card`, `direct_debit_payment_not_recognised`, `lost_or_stolen_phone`, `cash_withdrawal_not_recognised`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
