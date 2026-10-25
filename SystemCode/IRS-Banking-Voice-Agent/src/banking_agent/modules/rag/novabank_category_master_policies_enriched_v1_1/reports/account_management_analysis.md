## PART 1: Analysis & Expansion Report — `account_management`

审阅日期：2026-10-11。覆盖 5 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_account_management_master_policy.md)。

### Missing Rules Added

- 补充合法姓名变更证据、旧手机号不可用的人工恢复和24小时敏感功能限制。
- 区分居住资格与国籍、临时出国与迁出新加坡。
- 补充多币种余额、未结算交易／退款／投诉的销户阻断，以及最终销户后的卡token撤销。

### Category Recommendation

现有13类足够。联名、未成年人、遗产／授权代理及企业账户若上线，需要新产品政策；本次不引入。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-14: DBS — Update Personal Details](https://www.dbs.com.sg/personal/digital-banking/update-particulars) | Contact updates differ from legal identity changes and supporting-document updates. | Overseas addresses and physical channels do not expand NovaBank eligibility. |
| [REF-15: DBS — Close a Current/Savings Account](https://www.dbs.com.sg/personal/support/bank-account-closure.html) | Closure requires handling remaining balances, holds and linked facilities. | Joint, loan-linked and branch closure services are excluded. |
| [REF-13: Revolut — Lost or Stolen Device](https://help.revolut.com/en-US/help/profile-and-plan/log-in-issues/my-phone-has-been-lost-or-stolen/) | Lost-device access recovery, session removal and transaction review. | No real contact address, product or recovery channel is reused. |
| [REF-22: DBS — Documents Required for Account Opening](https://www.dbs.com.sg/personal/support/bank-account-opening-documents-required.html) | Identity/address evidence must match application particulars and be readable. | NovaBank evidence list and 90-calendar-day freshness are synthetic. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`age_limit`, `edit_personal_details`, `passcode_forgotten`, `terminate_account`, `country_support`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
