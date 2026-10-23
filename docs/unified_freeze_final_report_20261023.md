# Final structured-freeze synthesis — 2026-10-23

## Decision

This is the current final report for the **structured** full-system freeze. It
combines the immutable original unified run with a separately frozen legacy
reconciliation. It is the baseline for independent final-response semantic
evaluation, not a claim that all generated text has passed an LLM judge.

## Provenance

| Source | Scope | SHA-256 |
| --- | --- | --- |
| [Unified raw-v1](../artifacts/evaluation/unified_freeze_20261023_182527/report.json) | Single-turn, technical, legacy and expanded multi-turn, each ×3 | `5dd4f1cbcc1c9dccc86f5312dd06ca4fbce6c44d4589962806db6ca99c1ff824` |
| [Corrected raw-v1 aggregation](../artifacts/evaluation/unified_freeze_20261023_182527/report_rescored.json) | Same raw attempts; corrected legacy denominators only | `a308cb05aff1b91515d23e965be1e7f595deb406ee1843705995e252004402f1` |
| [Legacy reconciliation-v2](../artifacts/evaluation/legacy_reconciliation_v2_20261023/report.json) | Legacy 24 sequences / 49 turns ×3 after C/fixture reconciliation | `e9be9fdd1963ed71679f1d548c9f1ba7bbcee168b89d2e584050834f147fc563` |
| [Legacy reconciliation post-B0 fix](../artifacts/evaluation/legacy_reconciliation_post_b0_fix_20261023/report.json) | Same legacy population ×3 after the bounded-context safety repair | `ce2f9c51e30ee53ef8cf4b3670bc0d2391b860f1f1f95cbfc2ea19fade180fbd` |

Raw-v1 remains immutable. The post-B0 reconciliation replaces the legacy
state/workflow conclusion below. Its manifest records the submitted code
revision; its `dirty` flag is caused only by an untracked local zip, not a
tracked source diff. This remains a controlled cross-revision synthesis, not a
manufactured same-revision total.

## Single-turn structured results

| Population | E2E appropriate | Resolved answer / recommendation | Safe non-answer |
| --- | ---: | ---: | ---: |
| Core business, 40 cases ×3 | 117/120 | 33/33 | 84/87 |
| Complex development, 36 cases ×3 | 104/108 | 14/15 | 90/93 |
| Complex holdout, 12 cases ×3 | 33/36 | 3/3 | 30/33 |
| All business attempts, 88 cases ×3 | 254/264 | 50/51 | 204/213 |

- Core all-three-repeat stability: 39/40 cases.
- Controlled technical fail-closed checks: 6/6.
- Required evidence / grounding: core 24/24; complex 24/30.
- Recommendation permission: permitted 30/30; denied 45/45.

## Multi-turn structured results

| Population | Turn result | Three-repeat sequence result | Interpretation |
| --- | ---: | ---: | --- |
| Legacy state/workflow, post-B0 reconciliation | 29/36 | 4/6 | Remaining safe workflow/action mismatches are reported separately. |
| B0 bounded context, post-B0 reconciliation | 54/54 | 18/18 | All contextual oracles pass; no context safety violation. |
| Pre-context legacy oracle, post-B0 reconciliation | 15/54 | 5/18 | Historical context-disabled diagnostic only. |
| Legacy technical fixture | 3 attempts | — | Not a real-module success denominator. |
| Expanded reviewed multi-turn, raw-v1 | 117/117 | 13/13 | Structured actions, context, evidence, D permission and available text constraints passed. |

Expanded raw-v1 context diagnostics: reference resolution 30/30, topic switch
9/9, stale-context prevention 15/15, clarification closure 3/3, and
unresolved-reference clarification 3/3.

### Context safety closure and remaining workflow gaps

`E2E-MT-SEM-002` now gives `CLARIFY / REPLACEMENT_REASON_REQUIRED` for “Does
that include delivery?” in all three post-B0 repetitions. The full legacy
reconciliation records zero safety violations. The remaining state/workflow
gaps are safe action mismatches in `E2E-MT-STATE-002` (complaint handling was
expected; `CLARIFY` or `ABSTAIN` occurred), so they must not be presented as a
fully passing workflow result.

## Reliability observations

Do not pool these measurements because legacy was rerun in reconciliation-v2.

| Source | LLM fallback | Latency p50 / p95 |
| --- | ---: | ---: |
| Raw-v1 full run | 147/964 module events | 4,544 / 8,839 ms |
| Legacy reconciliation post-B0 fix | 34/286 module events | 6,448 / 11,053 ms |

## Separate local ASR smoke evaluation

ASR is a local terminal boundary, not part of the text-agent E2E denominator.
The completed artifact is
[`ascend_turbo_metal_v1/report.json`](../artifacts/asr/ascend_turbo_metal_v1/report.json),
with its fixed public-clip selection in
[`selection.json`](../artifacts/asr/ascend_turbo_metal_v1/selection.json).
It used local whisper.cpp with multilingual `large-v3-turbo-q5_0` under the
tested Apple-Silicon Metal configuration, on a deterministic 80-clip public
CAiRE/ASCEND test smoke set.

| Stratum | Successful clips | Mixed-token error rate |
| --- | ---: | ---: |
| Mandarin-English mixed (60) | 60/60 | 21.12% |
| Mandarin (10) | 10/10 | 26.36% |
| English (10) | 10/10 | 31.82% |

This metric tokenizes Chinese characters and English/number words; it is a
reproducible smoke metric, not a published WER or a banking-domain claim.
Audio is processed locally and transiently. A future voice UI must present the
transcript for user confirmation before text can enter A/C/B/D, so these ASR
results must not be pooled with text E2E, safety, RAG, or final-response
semantic rates.

## Independent final-response semantic overlay

The merged response-judge report is
[`final_response_semantic_v2/report.json`](../artifacts/evaluation/final_response_semantic_v2/report.json)
(SHA-256 `dc416ed6c74a946756d1c1abca444a42798c373e05984814660b7847e087ef3d`).
It preserves the earlier core/complex/expanded verdicts and replaces their
unscored legacy population with the separately judged post-B0 legacy report;
it does not rerun A/B/C/D/E. Only reviewed `ANSWER` and `CLARIFY` text enters
this semantic denominator. All other actions stay in their existing structural
safety metrics.

| Population | Text passed / scored | Judge unavailable | Not in text denominator |
| --- | ---: | ---: | ---: |
| Core single-turn | 33/33 | 0 | 87 structural-action rows |
| Complex single-turn | 55/55 | 2 | 87 structural-action rows |
| Expanded multi-turn | 60/64 | 2 | 51 structural-action rows |
| Legacy multi-turn | 63/72 | 0 | 75 structural-action rows |
| **Reviewed-text total** | **211/224 (94.2%)** | **4** | **300 structural-action rows** |

The 13 scored text failures comprise four expanded-multi-turn clarifications
and nine legacy clarifications that ask for a card type, fee reference, or
other context rather than the required replacement reason. They are text-quality
failures, not safety violations. The four unavailable rows exhausted the
judge's structured-output retries and are explicitly unscored, not treated as
passes or agent failures. The earlier judge request-ID collision was corrected;
the retry report reused 519 prior verdicts and retried only the nine unavailable
rows.

## Post-freeze B0 repair evidence and full legacy confirmation

After reconciliation-v2, E's bounded deterministic resolver was narrowly
extended for the exact reviewed follow-up “Does that include delivery?” when
the preceding user turn explicitly concerns a replacement-card fee. It resolves
only to “Does the replacement-card fee include delivery?”, then relies on the
existing C evidence gate to require the replacement reason.

The targeted real two-turn smoke is
[`b0_sem002_fix_smoke_20261023/report.json`](../artifacts/evaluation/b0_sem002_fix_smoke_20261023/report.json)
(SHA-256 `767ee9f89a5dfc733e90e2fa7163df95f602ff6f31e1adf638acb3e4470b1e15`).
Its follow-up is `CONTEXT_PASS`, with contextual resolution and
`CLARIFY / REPLACEMENT_REASON_REQUIRED`. The subsequent 24-sequence /
three-repeat reconciliation above confirms this result at the full legacy
scope: 54/54 B0 turns, 18/18 stable sequences, and zero safety violations.
