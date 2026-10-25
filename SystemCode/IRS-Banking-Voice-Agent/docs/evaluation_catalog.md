# Evaluation catalogue

This catalogue is the single entry point for interpreting the project's
synthetic evaluation data. A fixture's count must never be added to another
fixture's count unless this document identifies the two as disjoint.

For submission results, start with
[`unified_freeze_final_report_20261023.md`](unified_freeze_final_report_20261023.md).
This catalogue is the methods and denominator reference; the older
[`unified_freeze_20261023.md`](unified_freeze_20261023.md) is a historical
execution log, not the submission narrative.

## The three evaluation layers

| Layer | Data | Question answered | Current command | Not a measure of |
| --- | --- | --- | --- | --- |
| Workflow acceptance | 42 single-turn E2E cases: 40 business and 2 technical | Does A/B/C/D/E execute the required workflow, safety gates, state updates, and call order? | `scripts/evaluate_real_llm_e2e.py` | Robustness to new wording or final factual answer quality by itself |
| Semantic answer scorecard | 40 annotations attached to the 40 non-technical single-turn E2E cases (11 core + 29 variants) | Did understanding, C decision, B evidence, D output, and public response facts meet reviewed expectations? | Included in `scripts/evaluate_real_llm_e2e.py` | An additional independent 40-case sample |
| Complex-language stress set | 36 development + 12 disjoint holdout cases, each with a semantic overlay | Does A, an LLM draft, or fuse handle ambiguity, natural wording, multi-intent input, grounding traps, recommendations, and adversarial wording through to the final answer? | `scripts/evaluate_a_only_semantic.py`; `scripts/run_single_turn_fuse_freeze.py` | A replacement for core workflow regression coverage |

The first two layers share source scenarios. Their effective single-turn
workflow population is therefore **42 cases**, not 42 + 40. The complex set is
separate, so the current single-turn evaluation inventory is 42 workflow cases
plus 48 complex-language cases.

## What each report may conclude

| Report | Strictly scored | Use it for | Do not use it for |
| --- | --- | --- | --- |
| `evaluate_real_llm_e2e.py` | Workflow outcome; the scorecard also checks intent/risk, action/state, required/forbidden B documents, D product IDs, required answer facts, and forbidden answer claims | Core A-only vs shadow vs fuse acceptance; RAG/recommendation and answer-content checks | A claim about complex wording not represented in the 42 workflow cases |
| `evaluate_a_only_semantic.py` | A and LLM-draft intent/risk, C pre-retrieval route, fallback, latency, and merge disposition | Diagnosing whether an observed complex-language failure starts in A, the LLM draft, or fuse | RAG correctness, recommendation ranking, or factual answer quality |
| `run_single_turn_fuse_freeze.py` | The 48 complex cases through real A/B/C/D/E: strict semantic pass plus separate downstream-outcome, response and evidence-grounding metrics; final C route/state, B evidence, D product IDs, trace and performance | Frozen end-to-end comparison of A-only and experimental fuse | A reason to tune holdout or activate fuse by default before results are reviewed |

## Split discipline

- **Development (36):** prompt and merge-policy diagnosis. It may be used to
  change the LLM prompt, merge gates, or fixture annotations.
- **Holdout (12):** no tuning. Run only after a frozen development decision to
  check that the result generalises.
- **Core E2E / semantic scorecard (42 / 40 overlay):** regression acceptance.
  Do not use a passing workflow result to conceal a failed scorecard check.

## Multi-turn status

`tests/e2e/multi_turn/` has 24 sequences and 49 turns. It validates carried
business state (complaint, handoff, and consent) and workflow safety. E now
has an opt-in B0 bounded recent-public-turn context path. The real evaluator
can run it with `--include-multi-turn --understanding-mode fuse
--context-memory`, using the same `recent_public_context` construction as the
API path. The 18 `semantic_context` sequences retain their second-turn legacy
`expected` values as the context-disabled scripted regression oracle. Each now
has a separate `semantic_oracle.b0_expected` record (`b0_oracle_ready`):
expected action/reason, whether contextual resolution is required or
forbidden, and a review rationale. With `--context-memory`, the real evaluator
scores this B0 record separately as `CONTEXT_PASS`, `CONTEXT_GAP`, or
`CONTEXT_SAFETY_FAILURE`; it never substitutes it into the legacy scripted
contract. This is the bounded B0 acceptance population, not a claim of
long-history coverage.

The current bounded semantic freeze is
[`b0_multi_turn_semantic_freeze_v1`](../artifacts/evaluation/b0_multi_turn_semantic_freeze_v1/report.json):
`18/18` contextual follow-up oracles passed in one real Fuse run. Its report
also retains latency, optional-LLM fallback, token, and full decision-trace
measurements.

`tests/fixtures/evaluation/multi_turn_semantic/v1/expanded_e2e.json` is a
separate candidate population: 13 three-turn sequences (39 turns)
covering longer follow-ups, selective continuation, topic return, complaints,
risk interruption, recommendation gating, contradiction, and history
injection. Its companion
`expanded_e2e_annotations.json` supplies a complete per-turn C/E overlay. All
13 sequences (39 turns) have candidate decision/state, evidence-call, and
where applicable response-fact oracles that are `approved_for_freeze`.
Damaged-card turns are ordinary evidence-based replacement support, not a
safety escalation; a lost-card handoff remains active through later policy
sub-questions; and a pending-transfer follow-up uses the reviewed
`NB-v1_1-pending_transfer-001` evidence rather than assuming an answer is
unsupported. Both files are approved for freeze and may enter the official
multi-turn denominator. The prior 12-sequence
candidate run passed 36/36 turns in
[`expanded_multi_turn_real_fuse_v4`](../artifacts/evaluation/expanded_multi_turn_real_fuse_v4/report.json);
the new MTX-013 clarification closure passed its targeted real-chain candidate
regression 3/3 in
[`expanded_multi_turn_mtx013_candidate_v2`](../artifacts/evaluation/expanded_multi_turn_mtx013_candidate_v2.json).
This is targeted evidence only, not a replacement 39-turn run.
The required C approval checklist is
[`multi_turn_annotation_review.md`](multi_turn_annotation_review.md).

`expanded_e2e_metric_tags.json` in the same fixture directory defines reviewed
diagnostic denominators for context-reference resolution, explicit topic
switch, stale-context prevention, and the MTX-013 clarification closure. It
does not replace the C/E turn oracle; metrics must use these tags rather than
infer categories from free-form rationale text.

## Planned full-system freeze acceptance

> **Status:** the unified runner, its representative smokes, and one complete
> three-repeat frozen run are available. The run's raw attempts are retained
> locally; its multi-turn summary must keep state/workflow, B0 context,
> pre-context legacy-oracle diagnostics, and technical fixtures separate.
> The historical execution log is
> [`unified_freeze_20261023.md`](unified_freeze_20261023.md); its linked raw
> and re-aggregated reports remain local evaluation artifacts. The submission
> narrative, including legacy reconciliation, final-response semantics and the
> separate ASR smoke result, is
> [`unified_freeze_final_report_20261023.md`](unified_freeze_final_report_20261023.md).

### Scope and fixed population

The frozen run has three separately reported populations. They must not be
added together into one unqualified percentage:

| Population | Size | Headline it supports |
| --- | ---: | --- |
| Single-turn business acceptance | 88 distinct cases: 40 annotated core business cases + 48 disjoint complex-language cases | Overall single-turn end-to-end appropriateness |
| Single-turn technical checks | 2 core technical cases | Fail-closed technical reliability; excluded from business accuracy |
| Multi-turn workflow/state acceptance | 24 legacy sequences / 49 turns, plus 13 candidate semantic-memory sequences / 39 turns after C approval | Turn and sequence state/workflow correctness; report legacy state and contextual semantic populations separately |

Each single-turn case and each multi-turn sequence runs **three times** under
one frozen configuration. Report both attempt-level results and the stricter
case/sequence stability result, where all three repetitions must pass. The
complex development (36) and holdout (12) split stays visible in every table;
the holdout is never used to tune code, prompts, rules, fixtures, or config.

### Frozen delivery configuration

Before the run, record in a local, sanitized run manifest:

- Git commit and dirty-worktree status; fixture versions and case IDs;
- real A, B, C, D and E adapters, with their model/index versions where
  available;
- the exact provider/model, temperature, top-k, timeouts and retry limits;
- `fuse` enabled for the typed understanding path, if it remains the selected
  delivery configuration;
- the selected query-rewrite setting, final grounded-answer generator setting,
  and recommendation-presentation generator setting; and
- the B0 context-window size, context feature flag, and explicit reset/expiry
  policy.

No setting may change during a run. A provider or infrastructure failure may
be rerun only with the same manifest and recorded reason; it is not a reason
to discard a valid unfavourable outcome. Generated reports remain local and
must not be committed.

### Required measurements

The final report must retain the raw per-case records and calculate the
following separately.

| Measurement | Population | Pass definition |
| --- | --- | --- |
| End-to-End Appropriate Outcome Accuracy | 88 single-turn business cases | Final C action/reason/state, allowed module sequence, B/D outputs where applicable, and public delivery meet the reviewed fixture contract |
| Resolved Answer/Recommendation Accuracy | Cases whose gold outcome is `ANSWER` or `RECOMMEND` | The issue is actually answered/recommended, required facts or D product IDs/order/reasons are correct, and no forbidden claim appears |
| Safe Non-answer Delivery Accuracy | Gold `CLARIFY`, `ABSTAIN`, `BLOCK`, `ESCALATE`, or complaint-handling cases | The safe action is correct and its wording asks for the required missing information or gives the required next step without inventing facts |
| Understanding and fusion diagnostics | The 88 cases, split by core/complex and complex family | A intent/risk match, fused final C decision match, A-to-fuse correction count, fuse regression count, and fallback/disposition |
| Retrieval and grounding | `ANSWER` cases | Required evidence hit, forbidden/irrelevant evidence admission, C-approved evidence sufficiency, citations and required/forbidden final-answer facts |
| Recommendation delivery | `RECOMMEND` and recommendation-denial cases | C permission/gate, D invocation, exact returned product IDs/rank/reasons, and safe LLM-presentation fallback behavior |
| Reliability and cost | All attempts, technical cases separately | Technical fail-closed result, LLM fallback/error rate, module and end-to-end p50/p95 latency, attempts and token totals |

`CLARIFY` may count as an appropriate safe outcome, but never as a resolved
answer. This distinction prevents a high clarification rate from inflating the
user-problem-resolution result. A free-form LLM quality judge, if used, is
diagnostic only until its provider/format stability is independently accepted;
the frozen headline uses reviewed factual and behavioural constraints.

For multi-turn, report turn-level state/workflow pass rate, sequence-level
three-repeat pass rate, safety violations, and stale-context/incorrect-topic
carry-over rate. B0 `context_evaluation` results are a distinct context-enabled
population and must never be pooled with the context-disabled legacy
`expected` oracle or scripted technical-error fixtures. Once B0 fixtures are
present, additionally report context-reference resolution, explicit
topic-switch correctness, unresolved-reference clarification, and
context-assisted latency/token overhead. Do not claim general long-context,
cross-session, or preference memory from this run.

### Execution and acceptance gates

1. Run focused unit/integration/E2E tests for B0, recommendation presentation,
   grounded responses, rules safety, retrieval, and persistence/versioning.
2. Run the three-repeat full configuration against all three populations;
   preserve development and holdout subtotals rather than pooling them for
   tuning decisions.
3. Produce one Markdown summary and one sanitized JSON report with per-case
   traces, configuration manifest, metric denominators, and all failures.
4. Freeze only when there are zero safety violations, zero technical failures
   represented as successful business outcomes, no core workflow regression,
   and reviewed acceptable results for both development and holdout. Any
   failing category is diagnosed from the per-case record before another run;
   the result is not silently averaged away.

## Standard experiment sequence

1. Use the core evaluator in `off`, `shadow`, and experimental `fuse` modes.
   This is stable workflow regression and its 40-case semantic overlay.
2. Use the complex development set to diagnose wording and fusion changes.
   Keep its holdout untouched until the development policy is frozen.
3. The reviewed complex semantic overlays are now present at
   `tests/fixtures/evaluation/semantic/v1/complex_language_{development,holdout}.json`.
   They reference the existing 48 case IDs rather than duplicate inputs, and
   score final C route/state, B evidence, D results and response facts.
4. The planned delivery-level acceptance is the full-system freeze above. Its
   prerequisite is B0 bounded recent-turn memory and its focused evaluation;
   until then, the existing single-turn reports remain component acceptance,
   not a claim of complete agent delivery.

## Current delivery status

- The complex overlays are complete and the freeze evaluator consumes them.
  It keeps strict semantic acceptance while separately reporting downstream
  outcome, response and evidence-grounding results, so an intent/risk-label
  miss cannot be mistaken for a final-answer failure.
- B0 bounded recent-turn memory is implemented and its focused 18-turn
  regression passed. The expanded 13-sequence semantic-memory population is
  approved for freeze, and MTX-013's targeted candidate regression passed
  3/3; see `docs/multi_turn_annotation_review.md`.

All evaluation scripts write sanitized JSON reports to `artifacts/evaluation/`
by default. Generated reports remain local artifacts and must not be committed.
