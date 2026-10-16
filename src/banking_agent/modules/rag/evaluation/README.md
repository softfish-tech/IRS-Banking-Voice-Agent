# 已审批评测资料

- dev.jsonl：76条开发集；test.jsonl：32条冻结测试集。
- manifest.json：108条原gold审批、分组、哈希；数据未因清理改变。
- evidence_filter_v1/：24条已批准no_evidence，以及16条复用dev对照（不能重复统计）。
- 历史实验与旧脚本已收纳到 ../archive/pre_integration_20261016.zip，按原路径恢复。

当前仅保留统一评测入口 evaluate_retrieval.py：--backend real/bm25/dense/hybrid。
默认real和dev；bm25代表未经优化的baseline，real代表优化BM25+CE。
Dense/Hybrid只读本地缓存；后续正式对比需固定模型revision。
--validate-only校验数据来源和dev/test隔离，不运行检索。
每次使用新的--output-dir，避免覆盖证据；输出metrics.json、rankings.jsonl。

历史CE分数-6实验是开发结果，未启用为拒答阈值。真实入口返回候选后由C评估充分性。
新增诊断题审批不意味着筛选算法通过验收。test未用于调参。

## 固定−6的新问法确认（待审批）

`gate_minus6_confirmation_v1/`保存32条新增业务近域题及逐题来源，含2道多块问题。
它与旧数据部分共享事实，不声称新意图盲测。`--gate-confirmation --validate-only`
仅检查来源与结构；正式运行要求全部人工审批，不进行阈值搜索或改动默认后端。
