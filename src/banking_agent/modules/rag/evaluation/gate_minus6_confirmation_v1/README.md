# 固定−6门控的新问法确认集

32题均待人工审批，未运行检索或查看CE分数。建议标签：8道no_evidence、16道supported、
8道unsupported；后两类都是有正确证据的正向对照，包含2道多块问题。

四组各8题：外部提供方精确费用缺失、起算事件辨别、卡种/状态/客户适用性、
已明确规定费用的对照。REVIEW.md给出完整问题、建议gold、近邻知识块原文及Policy链接。
questions.jsonl为机器可读草案，manifest.json记录固定协议、来源代码/数据哈希。

## 实验约束

- 固定当前优化BM25候选20、CE输出5及相同模型commit。
- 只比较不筛选与最高候选分数低于−6整题empty；等于−6时保留原top5。
- 不单独删除低分块，不调模型、不搜索其他阈值，不更改真实后端默认。
- 初始化和评分技术错误保留error，不能计作拒答成功。
- 新题与旧题部分共享intent、事实或gold，已逐题暴露关联；这是新问法确认，不是独立新意图盲测。
- 不根据模型分数挑题或修改gold。人工审批前程序拒绝评分。
- 若根据新题错误调整规则，本集合改为dev，之后另建验收样本；原冻结test不动。

## 审批与运行

请复核32题并提供需要修改的题ID、类别、全部必要chunk，以及审批人/日期。
审批不是自动生成的；此前24道题的审批不涵盖本次32道新题。
批准后记录每行和manifest的审批人、日期、ready状态，并更新数据哈希。
如gold或证据更改，先重新核对来源，不绕过冻结校验。

```sh
# 只做结构与来源校验，不调用模型，允许pending。
PYTHONPATH=src python -m banking_agent.modules.rag.evaluate_retrieval --gate-confirmation --validate-only

# 全部获批后才可执行；需要此前固定模型的本地缓存。
PYTHONPATH=src python -m banking_agent.modules.rag.evaluate_retrieval --gate-confirmation --output-dir /tmp/gate6-confirmation-new
```

输出comparison.json与完整baseline/gated排名。报告整体及分组误返回率、原有及新增
误拒题、Recall@5、多块全部命中率、明确不支持服务的gold损失及技术错误。
没有独立预先商定的业务验收阈值，因此程序只报告取舍，不自动宣布生产通过。
no_evidence标签针对“精确事实没有证据”，不意味着C/E不能安全解释该信息不可用。
