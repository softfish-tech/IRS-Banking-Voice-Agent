## PART 1: Analysis & Expansion Report — `currency_exchange`

审阅日期：2026-10-11。覆盖 4 个BANKING77 intent。英文增强政策：[PART 2: Enriched Master Policy](../policies/NovaBank_currency_exchange_master_policy.md)。

### Missing Rules Added

- 补充报价过期、汇率方向与四舍五入示例。
- 明确足额同币种余额优先、不足时整笔从SGD兑换；ATM固定从SGD扣款。
- 区分商户DCC和NovaBank兑换；保留原成交汇率退款及零新增退款兑换费。

### Category Recommendation

现有13类足够。国际汇款、加密资产和外汇限价交易超出范围；若未来上线应独立设计。

### Source-to-Policy Trace

| 官方资料 | 参考主题 | NovaBank采纳边界 |
| --- | --- | --- |
| [REF-04: DBS — Overseas Card Transaction Fees](https://www.dbs.com.sg/personal/support/card-charges-and-fees-overseas-transaction-fees.html) | Separate settlement-date rates, merchant DCC and issuer charges. | Do not import actual fee rates or refund conversion methods. |
| [REF-05: DBS — Transact & Withdraw in Foreign Currency Overseas](https://www.dbs.com.sg/personal/support/bank-atm-debit-card-withdraw-cash-overseas.html) | Distinguish purchase funding balances from overseas ATM funding. | Actual supported currencies and balance selection differ from NovaBank. |

### Synthetic Terms and Intent Coverage

所有NovaBank价格、限额、期限、证据有效期及安全控制均为项目的合成设计，不能解释为上述真实银行的规则或法律结论。保留v1.0的核心商业条款；v1.1增加操作例外、状态区分与所需证据。

`exchange_rate`, `fiat_currency_support`, `exchange_via_app`, `exchange_charge`

本报告、参考登记表和旧版本不作为当前客户政策一起入库。每个intent的完整规则见对应英文政策中的 `###` 小节。
