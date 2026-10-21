# E integration delivery plan

> Status: active local delivery plan (2026-10-21). This document replaces the
> earlier plan that assumed A and C had not been integrated. It is an execution
> roadmap, not a parallel module contract. The executable schemas and enums,
> `docs/module_api_contract.md`, `docs/scenario_table.md`, and
> `docs/engineering_conventions.md` remain authoritative.

## 1. Current baseline

The text-agent path now composes the real A, B, C, and D public modules through
E's orchestrator. The default path uses A's trained intent adapter, C's rule
decision, B's retrieved evidence, and D's guarded recommendation path. E owns
the sequencing, validated state merge, public response assembly, persistence,
decision traces, and E2E evaluation; it does not replace the other modules'
domain decisions.

The current single-turn baseline has the following properties:

- normal E2E covers 42 single-turn fixtures (40 business cases and 2 technical
  cases), with workflow/call-order/trace checks;
- a semantic evaluation layer checks intent outcome, final action, permitted
  evidence, recommendation behavior, and answer constraints for the annotated
  business cases;
- the LLM can generate grounded final `ANSWER` and `CLARIFY` text, while the
  default route remains deterministic for understanding, retrieval permission,
  risk, business state, and recommendation permission;
- optional middle-loop LLM understanding and query rewriting exist only as an
  experimental, feature-flagged path;
- performance reports include request latency, LLM attempts, fallbacks,
  latency, and token usage. Time-to-first-token is intentionally `null` until
  a streaming provider transport is used;
- current multi-turn support preserves canonical complaint, handoff, consent,
  and conversation-version state, but does **not** yet provide robust semantic
  memory for references such as “that fee” or “the second option”.

This is a synthetic banking project. No customer data, credentials, account
numbers, raw voice recordings, model caches, or provider secrets may enter the
repository, test fixtures, traces, or browser bundle.

## 2. Non-negotiable integration rules

The next milestones must preserve the following boundaries.

| Concern | Authoritative owner | E's role |
| --- | --- | --- |
| Intent, entities, risk signals | A | invoke public adapter; evaluate and optionally combine typed drafts |
| Evidence retrieval and provenance | B | invoke only on permitted route; pass public documents onward |
| Action, reason code, canonical state patch, recommendation permission | C | invoke C before/after B; apply only valid allowed patches |
| Eligibility and ranking | D | invoke only after C permits `RECOMMEND`; render structured result |
| Sequencing, context delivery, API/UI, traces, evaluation | E | compose validated public contracts and fail closed |

- C remains the only authority for an action, canonical state transition, and
  recommendation permission. An LLM response never directly becomes a
  `Decision`, a complaint update, or a D invocation.
- A model may enrich a typed understanding draft. It may raise ambiguity or
  risk, but must not silently reduce an A/C high-risk outcome.
- An answer is rendered only after C permits `ANSWER`, and its claims are
  limited to B-returned evidence. Missing reliable evidence remains `ABSTAIN`;
  unclear intent or required information remains `CLARIFY`.
- Context is useful input, not a source of invented business facts. Canonical
  `AgentState` is still the source of truth for business state.
- Any shared schema, enum, public adapter output, or cross-module dependency
  change requires the canonical schema, contracts, scenarios, and tests to be
  updated together before implementation.

## 3. Workstream A — broaden LLM use safely

### Objective

Use the LLM first where it most improves natural-language understanding, while
retaining deterministic safety gates. The priority is not “call the LLM on
every step”; it is to make uncertain, conversational input understandable and
measurably improve the correct typed route.

### A1. Establish a measured understanding draft

For every eligible text request, the optional LLM should produce a strict,
validated `UnderstandingDraft`, not free-form control text. It may contain:

- an intent from A's operational taxonomy or `UNKNOWN`;
- normalized entities and missing slots;
- ambiguity/multi-intent indicators;
- a bounded, privacy-safe retrieval query suggestion; and
- a risk/escalation signal that can only make routing more conservative.

The existing deterministic A result stays alongside the draft. E records the
agreement/disagreement and the final fusion outcome in a sanitized trace. It
must not retain raw prompts, raw provider payloads, or secrets.

### A2. Shadow mode before route changes

Run the LLM draft for the expanded evaluation corpus without allowing it to
change the live route. Compare A-only versus proposed fusion by case family:

- intent and entity correctness;
- unnecessary clarifications;
- unsafe route attempts and missed high-risk indicators;
- retrieval evidence success after any suggested query rewrite;
- latency, provider failure/fallback rate, and token cost.

Shadow mode is accepted only when its report is reproducible from fixtures and
contains enough detail to identify regressions by case ID, without exposing raw
user text in normal traces.

### A3. Controlled activation policy

After shadow evidence is favorable, permit fusion only for explicitly bounded
conditions, initially:

1. A returns `UNKNOWN` or low confidence;
2. A identifies an incomplete, ambiguous, multi-intent, colloquial, or likely
   ASR-corrupted request;
3. the LLM and A disagree and the conflict requires a safe clarification; or
4. a safe query rewrite is needed after C has already allowed evidence search.

The fusion policy must be deterministic and explainable. C still receives a
canonical understanding envelope and can reject the route. High-risk signals
are combined conservatively: either source may cause escalation/clarification;
neither source may clear an existing high-risk result.

### A4. Expand in this order

1. Typed understanding draft in shadow mode.
2. Low-confidence/`UNKNOWN` and ambiguity fusion.
3. Bounded query rewriting after C permits retrieval.
4. Structured answer planning from selected evidence, followed by the existing
   grounded final renderer.
5. Streaming final-answer transport, once provider/API support is designed and
   tested, to expose time-to-first-token.

Do not use an LLM to choose C actions, update canonical state, grant a
recommendation, or cite documents it did not receive.

### A5. Acceptance criteria

- The normal E2E/safety suite has no regression and no added unauthorized D
  calls or unsafe high-risk routes.
- The hard-language evaluation improves or maintains semantic accuracy against
  A-only, with per-family results rather than a single aggregate score.
- Every LLM error, invalid structured response, timeout, or budget breach
  falls back to the deterministic safe path and is traceable by sanitized code.
- Reports show LLM coverage, disagreement rate, fusion selection, token usage,
  end-to-end latency, and (after streaming) TTFT.

## 4. Workstream B — multi-turn semantic context memory

### Objective

Allow follow-up turns to resolve references and continue a task without
confusing conversational context with regulated business state. Example: after
the assistant explains a replacement fee, “Can I waive that?” should resolve
the fee and card context; it must not invent a waiver policy or mutate state.

### B1. Memory model and boundaries

Introduce an E-owned, versioned conversation-context record separate from the
canonical `AgentState`. Its initial structured fields should be limited to:

- recent turn IDs and roles, with a bounded window;
- the last resolved operational intent and dialogue act;
- normalized, non-sensitive entities and explicitly supplied constraints;
- active subject/referents (for example, card, fee, transfer, recommendation);
- pending clarification slots and the question that requested them;
- selected evidence/document identifiers and answer/recommendation references;
- a compact, validated conversation summary when the window must roll over;
- context version, creation time, expiry/retention metadata, and provenance
  (`deterministic` or `llm_assisted`).

Do not store raw audio. Avoid keeping full prompts in traces. Do not copy a
free-form LLM summary into canonical business fields. Complaint, handoff, and
consent values continue to come only from C's validated state patch.

### B2. Turn processing design

Each new turn follows this sequence:

```text
load canonical AgentState + compatible context version
  -> deterministic reference/slot resolver
  -> optional constrained LLM ContextDraft for unresolved references
  -> A / guarded LLM-understanding fusion
  -> C -> B -> C -> optional D
  -> response rendering
  -> atomically persist allowed AgentState patch + next context snapshot
```

The resolver must attach provenance to every carried fact: current-turn text,
prior user confirmation, prior selected evidence, or a pending clarification.
If a pronoun, time reference, entity, or user preference cannot be resolved
reliably, the system asks a targeted `CLARIFY`; it never picks the most recent
topic merely to avoid asking.

Conversation writes retain the existing expected-version conflict behavior.
On a concurrent update or stale context, reload and re-resolve rather than
merging two summaries blindly.

### B3. Incremental implementation

1. Implement deterministic memory for last intent, active subject, pending
   clarification slots, selected document IDs, and current synthetic product
   references.
2. Add multi-turn fixtures with explicit gold context dependencies and test
   atomic persistence/version conflicts.
3. Add a typed `ContextDraft` in shadow mode only for references the
   deterministic resolver marks unresolved.
4. Activate LLM-assisted resolution behind a flag after comparison with the
   deterministic baseline; the draft can propose context links or `CLARIFY`,
   never a business action/state patch.
5. Add expiry, reset/new-topic behavior, and user-visible recovery when context
   is stale or wrong.

### B4. Multi-turn acceptance measures

Report by sequence and turn number:

- context-reference resolution accuracy;
- correct carry-over of pending slots and selected evidence;
- incorrect carry-over / stale-context rate;
- action, evidence, and recommendation semantic correctness after turn 2+;
- safe-clarification rate for deliberately ambiguous follow-ups;
- state-version conflict and recovery results; and
- added LLM latency/tokens where context assistance was used.

No multi-turn scenario passes merely because its final text sounds plausible:
the expected referent, allowed modules, final C action, state patch, evidence,
and response constraints must all match the fixture.

## 5. Workstream C — harder user-input and semantic evaluation data

### Objective

Keep the existing 42 single-turn E2E fixtures as stable workflow regression
coverage, and grow a reviewed semantic corpus around them. The new corpus does
not replace basic E2E: it adds cases where a simple intent label is insufficient
to show that the agent understood the user.

### C1. Dataset layers

| Layer | Purpose | Execution expectation |
| --- | --- | --- |
| Core workflow regression | stable S01–S11/technical fixtures | deterministic CI or local smoke |
| Semantic single-turn set | action, evidence, recommendation, response constraints | regular real-module/LLM evaluation |
| Complex-language challenge set | difficult wording and mixed constraints | scheduled/manual comparison; not tuned as a hidden test |
| Multi-turn semantic set | context dependencies across turns | integration/E2E evaluation |
| Voice-to-text set | transcript quality plus equivalent text behavior | ASR and frontend integration evaluation |

Keep test and development cases separate by underlying business fact and seed
utterance family. Do not turn Banking77 labels into NovaBank action/evidence
truth. Public datasets may inspire phrasing only; every final label is derived
from the Scenario Table and synthetic corpus.

### C2. Priority case families

Expand reviewed input cases in balanced groups rather than adding only easy
paraphrases.

| Family | Examples of difficulty | Required gold checks |
| --- | --- | --- |
| Natural variation | terse, colloquial, typo-heavy, code-switched, ASR-like wording | intended intent/entities or safe ambiguity handling |
| Multi-intent and priority | complaint plus policy question; fraud plus recommendation request | C-safe priority, prohibited calls, final action |
| Ambiguity and references | “that charge”, “do it again”, missing card/transaction | expected referent or `CLARIFY` |
| Constraint-rich requests | product preferences, budget/eligibility constraints, exclusions | C permission and D result boundaries |
| Grounding traps | topical but wrong documents, conflicting wording, absent policy | required/forbidden evidence and `ABSTAIN` behavior |
| Safety/adversarial text | prompt injection, irrelevant instructions, sensitive-data bait | no control takeover, safe public response |
| Complex response needs | explanation plus next steps, citations, denied recommendation | factual response groups and forbidden claims |

For each record, annotate at least: case ID/version/split, input or turn
sequence, initial canonical state, required context if any, expected final
action/reason, permitted module calls/order, required and forbidden document
IDs, recommendation expectation, response facts/forbidden claims, and whether
LLM use is expected/allowed/ignored for comparison.

### C3. Evaluation output

Replace a single “pass rate” headline with a report containing:

- workflow/call-order/trace correctness;
- semantic correctness overall and by scenario/family;
- A-only, LLM-draft, and fusion comparison where applicable;
- B evidence precision/required-document recovery at the selected-answer level;
- C/D safety results (high-risk routes, unauthorized recommendation calls,
  forbidden evidence/claims);
- final answer constraint score, with examples of failures by case ID;
- multi-turn context measures after Workstream B; and
- operational metrics: requests, LLM coverage, retries/fallbacks, tokens,
  full request latency, and TTFT when streaming exists.

Human review is still required for new gold labels and for sampled generative
answers whose acceptability cannot be represented safely by explicit rules. Do
not mark a response correct merely because the LLM itself judged it correct.

## 6. Workstream D — frontend, speech-to-text, and answer presentation

This plan interprets “语义转文字” as speech-to-text (ASR). The UI should make
the resulting text and its semantic handling visible and correctable before it
drives the banking-agent flow.

### D1. Text-chat vertical slice first

Build a frontend against E's versioned public API before coupling it to live
audio. It needs:

- conversation list/new/reset and optimistic-safe turn submission;
- clearly separated user/assistant chat bubbles;
- structured rendering of answers, citations, recommendations, clarifications,
  abstentions, escalations, loading, retry, and sanitized technical errors;
- source cards and recommendation cards using public DTO fields only;
- a visible synthetic/demo notice and no browser access to provider secrets,
  internal reason codes, raw RAG scores, internal document IDs, or traces;
- session/conversation version handling, including a recoverable stale-turn
  message; and
- accessibility basics: keyboard send, focus behavior, readable status, and
  non-color-only error/risk cues.

The UI must render what C/E produced, not reinterpret an answer as permission
to show a product or transition a business state.

### D2. Speech-to-text interaction

Add ASR as an input adapter, not a second agent path:

```text
record/upload -> validate audio -> ASR -> editable transcript + confidence
  -> user confirms/edits -> normal text conversation request
```

Required behavior:

- enforce client/server type, size, duration, and timeout limits;
- show transcription progress, failure, and retry/cancel states;
- display the transcript in an editable field before submit;
- make low-confidence or critical-token uncertainty require review rather than
  automatically submitting a guessed financial instruction;
- send only confirmed text into the normal agent API;
- delete temporary server audio on success/failure and do not persist raw audio
  by default;
- never place audio, provider keys, or full internal traces in browser storage.

The existing voice module remains the public ASR extension point. E consumes
its public transcription result and reports ASR status/metrics without importing
voice internals into the orchestrator.

### D3. Answer rendering and streaming

Initially render a completed response. When streaming is introduced, use a
separate, typed event protocol that distinguishes `status`, safe text chunks,
structured citations/recommendations, `complete`, and sanitized `error`.
Never render unfinished content as an approved product recommendation or a
confirmed business-state change. The final structured result is authoritative.

Streaming enables a real TTFT measurement. The trace/report needs request start,
first safe content event, final completion, provider/model identifier, retry and
fallback indicators, and token totals where supplied by the provider.

### D4. Frontend/voice acceptance

- Text input produces the same public result as the tested backend case.
- Citations and recommendations appear only when the final public DTO permits
  them; `CLARIFY`, `ABSTAIN`, and `ESCALATE` do not leak stale cards.
- A user can edit a transcript and the edited text—not hidden ASR text—is the
  recorded agent input.
- Equivalent approved audio and text fixtures have matching safe action and
  evidence/recommendation behavior.
- UI integration tests cover loading, failure, stale version, low ASR
  confidence, clarification follow-up, citation rendering, and recommendation
  denial.

## 7. Recommended execution order

The workstreams deliberately overlap, but activation is gated by evaluation.

| Milestone | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| M0: baseline freeze | current report/trace schema and stable core fixtures | current modules | reproducible single-turn report and clean trace checks |
| M1: complex evaluation | reviewed hard single-turn cases and per-family report | M0 | deterministic labels, dev/test separation, failure examples |
| M2: deterministic context | structured semantic-memory store and multi-turn fixtures | M0 | reference/slot/version tests pass without LLM |
| M3: LLM shadow | typed understanding/context drafts and A-only comparison | M1; M2 for context cases | metrics, cost, latency, and safety comparison |
| M4: guarded LLM activation | low-confidence fusion and bounded query rewrite | M3 | no safety regression; documented enable/rollback flag |
| M5: text frontend | public API chat, response/source/recommendation rendering | M0 | browser/API integration tests and error-state coverage |
| M6: ASR frontend | reviewable transcript flow and audio evaluation | M5; voice public adapter | ASR limits, transcript edit, audio/text equivalence tests |
| M7: streaming polish | streaming events and TTFT reporting | stable M5/M6 transport | final-event correctness plus TTFT metrics |

M1 and M5 can proceed in parallel. M2 should precede LLM-assisted context.
M3 must precede any broader LLM route control. A feature flag/rollback path is
required for every provider-dependent activation.

## 8. Trace, privacy, and experiment requirements

Every evaluated turn must emit an ordered, sanitized trace sufficient to answer
what happened without recording sensitive content:

1. request/conversation/case identifiers and elapsed timing;
2. context availability, resolver outcome, provenance category, and version;
3. A output summary and, when enabled, LLM draft/fusion outcome;
4. C decisions, permitted B/D calls, selected evidence/recommendation IDs;
5. final response mode, fallback/retry/technical status; and
6. performance counters: total latency, per-provider latency, input/output/
   total tokens when available, and TTFT only for streaming.

Trace completeness and permitted event ordering remain hard evaluation gates.
Metrics are reported in aggregate and by fixture family. Raw prompts, full
transcripts, audio, credentials, and secret configuration are excluded.

## 9. Definition of delivery readiness

Before claiming a broader LLM-enabled, multi-turn, voice-capable agent path:

- [ ] Core single-turn workflow/trace regressions pass with real A/B/C/D.
- [ ] Complex semantic data is reviewed, versioned, and reported by family.
- [ ] Deterministic multi-turn context passes its referent, pending-slot, reset,
      stale-version, and safety cases.
- [ ] Any LLM fusion/context route has shadow comparison evidence, a feature
      flag, deterministic fallback, and no safety regression.
- [ ] C remains the source of all canonical actions/state/recommendation gates.
- [ ] Frontend displays only public structured outputs and handles retry,
      clarification, no-evidence, escalation, and stale conversation versions.
- [ ] ASR requires editable/confirmed text, obeys retention limits, and matches
      equivalent text-case outcomes.
- [ ] Evaluation output includes workflow, semantic, evidence, context, safety,
      token/cost proxy, full latency, and—when streaming—TTFT metrics.

## 10. Immediate next implementation slice

The next recommended slice is deliberately small and measurable:

1. Add the first reviewed complex-language and multi-turn fixture families,
   including ambiguity, multi-intent priority, a context reference, and a
   safety/injection case.
2. Implement deterministic context storage/resolution for active subject and
   pending clarification slots; add public-contract and persistence tests.
3. Run the existing LLM understanding draft in shadow mode over that corpus and
   publish A-only versus draft/fusion diagnostics.
4. In parallel, establish the text-chat public API contract and a frontend
   shell that renders completed structured responses before adding ASR.

Only after these measurements should E enable LLM fusion for bounded
low-confidence/ambiguous traffic or expand it into query rewriting and richer
context resolution.
