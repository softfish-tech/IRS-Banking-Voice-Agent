# Semantic evaluation scorecard

[`../tests/fixtures/evaluation/semantic/v1/single_turn.json`](../tests/fixtures/evaluation/semantic/v1/single_turn.json)
and the companion `single_turn_variants.json` form a versioned 40-case
scorecard for evaluating real-module semantics. The 11-case file remains the
reviewed representative core; the companion covers maintained wording and
state variants. Together they cover every non-technical single-turn E2E case.
It complements, but does not replace, the workflow E2E suite.

Each record references an existing single-turn E2E case and separates:

- understanding gold: operational intent and risk level;
- retrieval gold: required, candidate, or forbidden B document IDs and the
  C-selected evidence count;
- C/D gold: allowed action, reason, state, and recommendation IDs; and
- response constraints: required and forbidden supported facts.

Response facts use reviewed `required_fact_groups`: each group has an ID and
one or more case-insensitive regular-expression alternatives. `forbidden_patterns`
reject unsafe claims. The evaluator does not write raw responses or prompts into
the report.

The response supplement also contains 25 declared `ANSWER`/`CLARIFY` turns
from the legacy 24-sequence fixture. They use only the existing reviewed
minimum rubrics (`replacement_reason` or focused `clarification`) and can be
judged from a recorded reconciliation report without rerunning A/B/C/D/E.
Technical fixtures and turns whose expected route is a structural non-answer
remain outside the text-quality denominator, even if an erroneous runtime
route happened to emit a clarification.

For the full-agent complex-language freeze, regex checks are retained only as
`response_lexical_*` diagnostics. The final `response_passed` value instead
comes from the evaluation-only `llm_semantic_v1` judge, at temperature zero. It
receives the question, a reviewed fact rubric keyed by the existing group IDs,
the forbidden-claim rubric, and the in-memory final answer. It accepts genuine
paraphrases rather than template wording. Its structured output is a
fact-ID-to-boolean object plus a safety boolean; it never stores customer text,
prompts, or answer text by default. Credential values are redacted before an
evaluation prompt is sent to the provider.
If that independent call is unavailable or malformed, the answer dimension is
explicitly unscored (`null`) and strict acceptance is false; it never silently
falls back to the regex score. This alters only final-answer assessment—the
A-understanding, C route, B evidence, D recommendation, safety-boundary,
latency, and agent-token measurements are unchanged. Use
`--lexical-response-evaluation` only to reproduce legacy regex diagnostics.

The freeze runner records the judge status and provider error code for every
answer-evaluation attempt, and makes one fresh compact retry after an
unavailable or malformed verdict. It still does not store answer text by
default. When a reviewed synthetic experiment needs later re-scoring, pass
`--record-response-text`; this writes each final answer as
`final_response_text` in that local artifact. Do not use that flag with real
customer conversations or commit an artifact containing response text.
Such an artifact can later be judged again without invoking A/B/C/D/E via:

```bash
PYTHONPATH=src python scripts/rescore_final_responses.py \
  --report-json <recorded-report.json> \
  --output <rescored-report.json>
```

`passed` remains the strict acceptance result: every applicable operational
understanding, decision, state, evidence, recommendation and response check
must pass. To make failures diagnosable without weakening that gate, reports
also record `outcome_passed` (all downstream C/B/D/response checks, excluding
exact intent/risk), `response_passed` (applicable required/forbidden response
facts), and `grounding_passed` (applicable required/forbidden/selected
evidence). A `null` response or grounding value means that dimension was not
applicable to the annotated case; it is not a pass.

Where several A outputs are semantically safe for the same scenario, an
understanding record may declare `allowed` intent/risk pairs instead of one
exact pair. This is used only when C's required decision remains identical.
The evaluator separately checks required C state patches and trace evidence
that B or D was called or was not called when the gold requires that
constraint. `selected_document_count: 0` is used for questions where B may
retrieve candidates but C must withhold all evidence and ask for clarification
or abstain.

`review_status` is part of the data contract. `confirmed_corpus`,
`confirmed_scenario_rule`, `confirmed_d_fixture`, and
`confirmed_project_decision` are usable deterministic gold. The latter is a
project-level operational label, not a native BANKING77 label, and therefore
must not be used to claim BANKING77-only A accuracy. The one
`confirmed_project_decision_pending_c_evidence_rule` row is a confirmed target
behaviour whose current C evidence-overlap implementation cannot yet realise;
report it separately as an implementation gap rather than a model error.

The product-recommendation cases are deterministic gold for C/D permission and
D ranking, but are project scenario labels rather than native BANKING77 labels.
They are therefore not evidence for a BANKING77-only A accuracy claim.

The lost-card fee case is deliberately corrected to the maintained B policy:
the source says a lost-card replacement costs SGD 15 and express shipping costs
SGD 10. It does not reuse the obsolete generic SGD 10 E2E mock assertion.

The crypto-wallet case is also explicit: the only allowed supported answer is
that NovaBank does not provide cryptocurrency balance, wallet, or recovery
service, cited to `NB-v1_1-fiat_currency_support-001`. It must not invent a
recovery process. This requires a C-owned bounded evidence rule because the
current generic term-overlap gate does not treat an unsupported-service policy
as evidence for the more specific word `recovery`.

## A-only complex-language development evaluation

[`../tests/fixtures/evaluation/a_only_complex/v1/development.json`](../tests/fixtures/evaluation/a_only_complex/v1/development.json)
adds 36 reviewed synthetic inputs that are deliberately separate from the
stable 42-case workflow suite: 12 natural variations, 6 multi-intent priority
cases, 6 ambiguous requests, 4 recommendation-constraint cases, 4 grounding
traps, and 4 safety/adversarial inputs. It assesses the real trained A adapter
and C's pre-retrieval route without an LLM, provider, B retrieval, or answer
generation. Run it with:

```bash
PYTHONPATH=src python scripts/evaluate_a_only_semantic.py
```

Every invocation writes a timestamped JSON artifact under
`artifacts/evaluation/a_only_semantic/` by default and also prints its path at
the end. Use `--output <path>` only when a fixed report location is required.

The companion semantic overlays
[`complex_language_development.json`](../tests/fixtures/evaluation/semantic/v1/complex_language_development.json)
and
[`complex_language_holdout.json`](../tests/fixtures/evaluation/semantic/v1/complex_language_holdout.json)
reference the complex case IDs without duplicating inputs. They provide final
C-route, B-evidence, D-product and response-fact constraints for the complete
orchestration experiment. Development annotations may evolve with reviewed
corpus/rule changes; holdout annotations are frozen and must not be changed in
response to fuse results.

With an explicitly configured provider, add `--shadow` to record typed LLM
drafts while verifying that A's output and C's pre-route are unchanged.

Its JSON report contains only case IDs and structured outcomes, not prompt
text. It reports A understanding and C route accuracy separately by family;
the development set is for diagnosis and must not be treated as a held-out
model-quality claim.

### Recorded A-only baseline (2026-10-22)

The real frozen MiniLM/logistic-regression A adapter was evaluated in the
prepared `irs` environment with no LLM/provider, B retrieval, or generated
response. The resulting sanitized report is a local evaluation artifact; the
following aggregate is the versioned project record.

| Family | Cases | A intent/risk match | C pre-retrieval route match |
| --- | ---: | ---: | ---: |
| Natural variation | 12 | 6 | 7 |
| Multi-intent priority | 6 | 3 | 4 |
| Ambiguity | 6 | 0 | 2 |
| Recommendation constraints | 4 | 4 | 4 |
| Grounding traps | 4 | 2 | 4 |
| Safety/adversarial | 4 | 1 | 3 |
| **Total** | **36** | **16** | **24** |

This is evidence to run a typed LLM-understanding comparison in shadow mode,
not evidence to activate LLM route control. In particular, four of six
context-free ambiguity cases were classified with sufficient confidence to
reach the policy-answer pre-route rather than `CLARIFY`. C's rule guards still
blocked several other misclassifications; no LLM may weaken those guards.

### Recorded LLM shadow experiment, round 1 (2026-10-22)

The same 36 synthetic cases were run with a configured LLM provider in
`shadow` mode and the cached encoder forced offline. All 36 typed drafts
validated, no request fell back, and mean draft latency was 2,449 ms. A's
output and C's pre-route were verified unchanged for every case. The drafts
returned `UNKNOWN` for all six context-free ambiguity cases, but reported
`ambiguous=false` in every case. This exposed a prompt-contract gap rather
than a safe fusion result: the prompt was amended to explicitly require the
boolean ambiguity signal for unresolved references and missing subjects. A
post-amendment rerun is required before considering `fuse`.

### Recorded LLM shadow experiment, round 2 holdout (2026-10-22)

After the ambiguity prompt amendment, all 12 holdout drafts validated with no
fallback; mean draft latency was 3,289 ms. Both holdout ambiguity cases changed
from A's high-confidence policy-answer pre-route to an LLM draft of
`UNKNOWN` with `ambiguous=true`. However, the draft also set `ambiguous=true`
for two multi-intent high-risk cases and one adversarial transfer case. The
signal therefore has useful recall but insufficient standalone precision. The
fusion gate consequently requires both an explicit reference phrase in the
current text and an LLM ambiguity/UNKNOWN confirmation; a high-risk draft is
handled only by the separate one-way risk-increase rule. This holdout result is
still shadow evidence, not authorization to activate `fuse`.

The separate 12-case `holdout.json` must not be used to tune the ambiguity
prompt or fusion thresholds. A candidate fusion policy must improve both the
development and holdout ambiguity results without increasing missed escalations
or unauthorised B/D calls.

### Recorded fuse-candidate comparison (2026-10-22)

`--compare-fuse` is an offline comparison only: it uses the same typed merge
function as the optional live path, then sends the candidate understanding to
C. It does not change the configured runtime mode. Crucially, its summary
counts every fixture row; an unavailable LLM draft is explicitly scored as the
unchanged A baseline rather than being removed from the denominator.

The final holdout run recorded 11 successful drafts and one safe fallback
(mean draft latency 3,638 ms). A/C's baseline pre-route matched 9/12 rows;
the candidate matched 11/12, with the two context-free ambiguity rows changed
from `ANSWER` to `CLARIFY`. It had no route regressions. The remaining failed
row was a natural-language fee complaint whose confident A result is retained
by the intentionally narrow merge gate.

The development comparison exposed two issues before this holdout result was
recorded: a bare `it` falsely treated a self-contained card-fee question as a
reference, and a raised LLM risk could previously precede C's account-read
hard block. The fusion gate now does not replace a confident A intent merely
because LLM risk is higher; it raises risk only. C now evaluates explicit
account-read and transaction-execution constraints before urgent-risk routing,
with unit coverage for both.

### Frozen 36-case development fuse rerun (2026-10-22)

After those corrections, the current code was rerun once on the complete
development fixture. It recorded 31 validated drafts, 5 safe A-only fallbacks,
and mean draft latency of 3,951 ms. Exact intent/risk matching rose from 16/36
to 17/36; more importantly, C pre-retrieval route matching rose from 25/36 to
29/36 with no route regressions in this run.

| Family | Cases | A-only route | Fuse route | Net change |
| --- | ---: | ---: | ---: | ---: |
| Natural variation | 12 | 7 | 8 | +1 |
| Multi-intent priority | 6 | 4 | 4 | 0 |
| Ambiguity | 6 | 2 | 5 | +3 |
| Recommendation constraints | 4 | 4 | 4 | 0 |
| Grounding traps | 4 | 4 | 4 | 0 |
| Safety/adversarial | 4 | 4 | 4 | 0 |
| **Total** | **36** | **25** | **29** | **+4** |

The four route improvements are `AOC-NAT-06` and ambiguity cases
`AOC-AMB-03`, `AOC-AMB-04`, and `AOC-AMB-06`. The ambiguity gains are safe
`ANSWER → CLARIFY` changes. The exact-label metric remains deliberately
conservative because fuse retains an existing A risk level when it selects
`UNKNOWN`; C still reaches the correct clarification route.

This is encouraging shadow evidence, but not authorisation to make `fuse` the
default: the development LLM is variable (31/36 successful drafts in the
frozen rerun, mean 3,951 ms), and only 17/36 exact intent/risk labels matched.
Keep production configuration in `shadow` and collect a larger, fixed-seed
reviewed set before an explicit, opt-in fuse rollout.

## Formal isolated understanding acceptance (2026-10-22)

The formal harness is
[`../scripts/evaluate_real_llm_e2e.py`](../scripts/evaluate_real_llm_e2e.py).
It accepts `--understanding-mode off|shadow|fuse` and deliberately keeps LLM
query rewrite, clarification wording, and answer wording disabled. This makes
the comparison solely about the typed A-to-C understanding hand-off. Each run
uses real A/B/C/D and E, including B's pinned local Cross-Encoder reranker,
and synthetic fixtures. A missing cached B model is reported as a technical
failure; the harness does not silently use deterministic ranking.
Reports are local, sanitized evaluation artifacts; they contain case IDs and
structured outcomes only.

The separate
[`../scripts/run_single_turn_fuse_freeze.py`](../scripts/run_single_turn_fuse_freeze.py)
uses the complete delivery profile for the 48 reviewed complex-language cases:
real A, optional Fuse, LLM query rewrite, B's local BM25-plus-Cross-Encoder
retrieval, real C and D, LLM clarification, and C-evidence-constrained LLM
answers. It records every `E.LLM.*` stage's validated/fallback count, token
usage when supplied by the provider, and latency, while retaining the existing
semantic, safety, evidence, recommendation and response-quality checks.

For a retrieval-only diagnosis before another full Agent run, use
`python -m banking_agent.modules.rag.diagnose_complex_e2e_ranking`. It compares
the same 48 reviewed complex-language inputs across B's BM25 Top-20 and
Cross-Encoder Top-5, recording only case IDs, document IDs and rank positions.
Use that report to distinguish a missing BM25 candidate from a reranking loss;
do not infer either from the final-answer score alone. The delivery profile
passes C-approved Top-5 evidence to the grounded response generator. That
generator accepts only source IDs from the supplied evidence and makes at most
one render-only retry on invalid or uncitable model output before the safe
deterministic fallback.

The 42 single-turn fixtures produced the following results:

| Mode | Business fixtures | Business result | LLM fallback | LLM p95 | Safety failures | Unauthorised D calls |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `off` | 40 (+2 technical fixtures not applicable) | 40/40 pass | n/a | n/a | 0 | 0 |
| `shadow` | 40 (+2 not applicable) | 40/40 pass; exact A-only route match | 4/42 | 5,084 ms | 0 | 0 |
| `fuse` | 40 (+2 not applicable) | 39/40 pass; 1 `CLARIFY` reason-code change | 7/42 | 8,001 ms | 0 | 0 |

Before the shadow rerun, one slow provider request exceeded E's ten-second
module budget and produced a technical failure. `LLMUnderstanding` now has an
eight-second total draft budget. On expiry it returns no draft, so the fused
adapter uses A's original result. The rerun had no technical failure; this is
covered by `test_understanding_timeout_falls_back_before_orchestrator_timeout`.

The sole single-turn fuse difference was `E2E-S07-002`: the action remained
`CLARIFY`, but C's reason changed from `LOW_INTENT_CONFIDENCE` to
`UNKNOWN_INTENT`. It is not a safety regression, but it fails the strict
zero-functional-regression gate.

## Final-response semantic overlay (2026-10-23)

[`../scripts/evaluate_final_response_semantics.py`](../scripts/evaluate_final_response_semantics.py)
judges the already-recorded final text; it never reruns the agent or alters a
structured-freeze artifact. Only `ANSWER` and `CLARIFY` are in the independent
text-quality denominator. Other actions remain in their structured safety
metrics, since a text-quality verdict is not a substitute for an action or
permission check.

The reviewed baseline scorecards plus
[`response_supplements_v1.json`](../tests/fixtures/evaluation/semantic/v1/response_supplements_v1.json)
now cover the original 52 distinct `ANSWER`/`CLARIFY` case-or-turns (156
recorded attempts across the three repeats: core 33, complex 57 and expanded
multi-turn 66), plus 25 declared legacy turns. In the post-B0 reconciliation,
72 legacy attempts actually reached `ANSWER`/`CLARIFY` with reviewed text gold.
The remaining legacy rows are structural-only: three technical-fixture attempts,
one unexpected complaint-path clarification, and turns whose actual route was
not text-eligible. The supplements add minimum fact/clarification constraints;
they do not make a prose-style quality claim.

Before a provider run, validate the frozen input and denominator with:

```bash
PYTHONPATH=src python scripts/evaluate_final_response_semantics.py \
  --dry-run --output /private/tmp/final_response_semantic_dry_run.json
```

When the post-B0 legacy report is supplied with `--legacy-report`, its dry run
has 228 `dry_run` candidates (the original 156 plus 72 legacy attempts) and
300 structural-only rows. The actual provider command removes `--dry-run` and
must write a new artifact under `artifacts/evaluation/`; it records the judge
verdict and metadata per attempt while keeping response text only in the source
freeze traces.

The stateful regression run contains 24 multi-turn sequences and 49 turns.
It compares real A/B/C/D/E with state carried from each preceding C decision.
Fuse introduced no new `SAFETY_FAILURE`, no unauthorised D call, and six
action/reason differences relative to `off`; four replaced an unsafe A-only
`ANSWER` with `CLARIFY`. This is not a multi-turn semantic-understanding
claim: `semantic_context` fixtures currently carry business state only and
explicitly mark their context contract as not implemented.

**Acceptance conclusion:** shadow passes and remains the delivery default.
Fuse may remain an explicit offline/experimental switch, but does not pass
formal rollout acceptance because the strict single-turn route/reason parity
gate has one regression, provider fallback remains variable, and true
conversation-context resolution has not yet been implemented or evaluated.
