## PART 1: Analysis & Expansion Report — `identity_verification`

审阅日期：2026-10-11。覆盖 4 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_identity_verification_master_policy.md)。

### Missing Rules Added

- 补充拍摄质量、姓名差异、证件有效期、人工审核及无法补足证据的处理。
- 按工资、售产、继承和赠与细分来源证据；核对实际转入链条而非仅看收入证明。
- 统一资金来源触发阈值、gross计数、完整材料后5个工作日的时钟和人工复核。

### Category Recommendation

现有13类足够。企业受益人核查、税务申报及法律咨询超范围；不把真实银行阈值当作法定标准。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-22: DBS — Documents Required for Account Opening](https://www.dbs.com.sg/personal/support/bank-account-opening-documents-required.html) | Identity/address evidence must match application particulars and be readable. | NovaBank evidence list and 90-calendar-day freshness are synthetic. |
| [REF-23: Revolut — Documents for Source of Funds Verification](https://help.revolut.com/en-IT/help/profile-and-plan/profile-plan/verifying-identity/documents-for-the-source-of-funds-verification/) | Match income type with documentary provenance and the corresponding bank credit. | No actual reporting threshold or acceptance guarantee is adopted. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`why_verify_identity`, `unable_to_verify_identity`, `verify_source_of_funds`, `verify_my_identity`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
