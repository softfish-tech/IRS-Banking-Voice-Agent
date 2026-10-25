## Cross-Category Consistency Review

### Authority and Preserved Terms

本次保留v1.0商业参数；上一轮card_lifecycle v1.1作为物理卡生命周期权威。其余12类升级日期统一为2026-10-11。原始v1.0文件未改。公开银行费率、授信产品、责任规则和海外地区资格未移植到NovaBank。

| 共享主题 | 本包一致规则 | 适用类别 |
| --- | --- | --- |
| 实体替换与续卡 | 通常最多2张未退役，续卡暂可3张但最多2张可用；损坏／安全替换先退役旧卡，续卡例外单独处理 | lifecycle / usage / ATM / security |
| 配送 | SGD15普通替换；标准运费0、Day5；加急10、Day2；14:00截止确定Day0，仅新加坡地址 | lifecycle / usage / ATM / security |
| 消费与钱包 | 单笔5000、日10000共享；实体tap100单笔、300累计；一次性卡500更严格；钱包token最多3 | usage / payments / virtual |
| ATM | 实体卡；单笔500、日1000；始终扣SGD；成功手续费2，失败无现金银行手续费0 | ATM / FX / security |
| 兑换 | 0.50%、最低等值0.50；30秒报价；DCC为第三方转换不收NovaFX；退款用原成交汇率无新增NovaFX费 | FX / payments / ATM / refunds |
| 充值 | 同名新加坡Visa/Mastercard借记卡；SGD20–2000、日5000、月20000；auto200低于100触发，每日一次 | topups / account / identity |
| 充值释放 | pending最多72小时；最终failed后1工作日发释放指令，外部5工作日从该指令计，不从充值日计 | topups |
| 转账 | 仅国内SGD；单笔10000、日20000为出账上限；入账无独立数值cap；通常60秒，24小时后trace | transfers / cashcheque / identity |
| 资金来源 | 单笔银行入账至少10000或30滚动日bank+card gross入账至少20000或risk flag；材料完整后5工作日 | identity / topups / transfers |
| 安全 | 24/7紧急接报；验证后freeze60秒、session/token撤销5分钟；无自动48小时责任丧失或赔付 | security / lifecycle / usage / account |
| 退款时钟 | 商户实际发起后5工作日；银行批准后2工作日；hold释放和network reversal另按payments | refunds / payments / virtual / account |
| 手机变更 | 批准后24小时限制新增收款人和card topup；失去旧号走安全恢复 | account / security / transfers / topups |
| 不支持服务 | 现金／支票、direct debit mandates、海外转账、信用透支、联名／企业账户始终不支持 | all |

### Explicit Clarifications

- 将实体tap故障的继承措辞“arrives in 5 business days”统一为Day5并保留Day0截止模型，不修改配送参数。
- 解释“一张pending＋一张settled”不是两次最终扣款；冻结／退役不会取消原有批准授权。
- 身份、卡片所有权和资金来源是三种不同验证，某一项通过不会自动让其他项通过。
- 原来70个intent事实块保留，本次逐块添加操作例外；单独共享条款补充旧文件未列出的钱包／账号／身份控制。

### Verification Limits

本记录为人工编辑审阅说明，结构校验为可重复脚本检查。没有运行实际向量检索、模型问答或模拟支付系统；需要团队接入后测召回与拒答。真实法规审查不属于此合成语料校验。

### Timing Clarifications — 2026-10-14

These editorial clarifications preserve policy version 1.1, effective date 2026-10-11, numeric deadlines and fees. Policy, FAQ and chunk drafts are synchronised.

- REVIEW-001: Every manual/automatic card top-up uses recorded issuer authorisation as the 72-hour start event, not request initiation or NovaBank acceptance. Ownership review does not restart it. Final FAILED status starts the one-business-day release instruction clock; sending that instruction starts the issuer five-business-day release window.
- REVIEW-002: An explicitly disputed purchase fee has a 60-calendar-day intake window from that fee posting to the NovaBank ledger. Recognised purchase/merchant disputes retain their settlement-based windows.
- REVIEW-003: An ATM rate-calculation error has a 60-calendar-day intake window from the disputed withdrawal posting to the NovaBank ledger. Cash-discrepancy reporting retains 30 calendar days from withdrawal.
- REVIEW-004: Overdue ATM status-only review takes up to 2 business days after complete evidence; no-cash/short-cash/excess-cash reconciliation has a 10-business-day decision target after complete evidence. Both acknowledge within 1 business day at SGD 0. Cash problems are reported immediately, even while pending.

### Knowledge Quality Clarifications — 2026-10-14

- KQ-001: Additional refunds are limited by remaining original principal after prior credits; aggregate credited refunds including merchant credits and bank-approved principal corrections never exceed original settled principal. These are distinct caps, not a second deduction of prior refunds from the aggregate cap.
- KQ-002: Every generated delivery cutoff includes late or non-business-day acceptance moving to the next business day; working-day acceptance by 14:00 keeps that day as Day 0.
- KQ-003: The one-request, 30-calendar-day identity reconsideration window starts when the final decision is notified through the secure app or registered contact channel. Internal recording or subsequent uploads do not start/restart it; staff decision target remains 5 business days after complete evidence.

Numeric policy limits, version 1.1 and effective date 2026-10-11 are preserved.
