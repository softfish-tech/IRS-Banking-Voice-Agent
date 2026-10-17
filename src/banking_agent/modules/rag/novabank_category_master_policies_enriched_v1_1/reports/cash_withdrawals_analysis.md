## PART 1: Analysis & Expansion Report — `cash_withdrawals`

审阅日期：2026-10-11。覆盖 7 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_cash_withdrawals_master_policy.md)。

### Missing Rules Added

- 补充ATM无现金但扣款、少给／多给现金、设备异常的安全处置。
- 区分吞卡后的卡片保护与交易对账，禁止承诺取回ATM内的卡。
- 补充运营方附加费、DCC、外币现金从SGD扣款，以及外币余额不能替代SGD取现余额。

### Category Recommendation

现有13类足够。无卡／钱包ATM、ATM存款和网点救援不属于NovaBank服务；不新增类别。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-07: UOB — ATM Help & Guides](https://www.uob.com.sg/online-branch/branch-atm/atm-help-guides.page) | ATM access, retained cards and overseas controls need separate workflows. | NovaBank has no branch or ATM retrieval service. |
| [REF-08: UOB — ATM Security](https://www.uob.com.sg/online-branch/branch-atm/atm-security.page) | Check ATM safety; report suspicious equipment and unauthorised use promptly. | Do not transplant real-bank alert thresholds or product controls. |
| [REF-05: DBS — Transact & Withdraw in Foreign Currency Overseas](https://www.dbs.com.sg/personal/support/bank-atm-debit-card-withdraw-cash-overseas.html) | Distinguish purchase funding balances from overseas ATM funding. | Actual supported currencies and balance selection differ from NovaBank. |
| [REF-04: DBS — Overseas Card Transaction Fees](https://www.dbs.com.sg/personal/support/card-charges-and-fees-overseas-transaction-fees.html) | Separate settlement-date rates, merchant DCC and issuer charges. | Do not import actual fee rates or refund conversion methods. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`pending_cash_withdrawal`, `wrong_amount_of_cash_received`, `atm_support`, `declined_cash_withdrawal`, `card_swallowed`, `wrong_exchange_rate_for_cash_withdrawal`, `cash_withdrawal_charge`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
