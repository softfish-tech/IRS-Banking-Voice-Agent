# Module API Contract

## Purpose

This document defines the integration boundary between the four domain modules and the E-owned application layer. It specifies the structured data each module receives and returns; it does not prescribe HTTP routes, models, databases, or implementation frameworks.

The canonical shared fields and enums are implemented in [`../src/banking_agent/schemas/state.py`](../src/banking_agent/schemas/state.py) and [`../src/banking_agent/schemas/enums.py`](../src/banking_agent/schemas/enums.py).

## Shared conventions

- Modules return structured results, not final UI text.
- Phase-one mocks and later production implementations use the same contract.
- `status` distinguishes a valid result, a normal empty result, and a technical error.
- All modules use the shared enums and field names once the state schema is agreed.

```json
{
  "status": "ok",
  "data": {}
}
```

| Status | Meaning |
| --- | --- |
| `ok` | A valid business result is available. |
| `empty` | The call succeeded but has no usable result, such as no reliable RAG evidence. |
| `error` | A technical failure occurred; it is not a business decision. |

## A — Intent / Risk / Entity

**Owner:** A
**Called by E:** At the start of each user text request.

### Input

| Field | Description |
| --- | --- |
| `session_id` | Current session identifier. |
| `user_text` | Text to analyse. |

E may optionally invoke its context-aware Fusion adapter with an E-owned,
bounded `ConversationContext` in addition to this unchanged A public input.
The baseline A adapter always receives the current `user_text` alone. The
context window contains at most three complete, successful, public
user/assistant pairs from the same conversation.  Each retained user text is
bounded to 2,000 characters and each retained assistant text to 8,000
characters.  The window is enabled only by
`BANKING_AGENT_CONTEXT_MEMORY=enabled`. It is untrusted context, not a new
instruction or a source of business state.

```json
{
  "session_id": "session-001",
  "user_text": "Someone used my card without my permission."
}
```

### Output

```json
{
  "status": "ok",
  "data": {
    "intent": "unauthorized_transaction",
    "confidence": 0.97,
    "risk_level": "HIGH",
    "entities": [
      {
        "type": "payment_method",
        "value": "card",
        "confidence": 0.96
      }
    ]
  }
}
```

- `confidence` is a number from `0.0` to `1.0`.
- `risk_level` uses the shared risk enum.
- `entities` may be an empty array.
- A does not return `action` or `final_response`.

## B — RAG / Knowledge Base

**Owner:** B
**Called by E:** When C allows an evidence-based answer.

### Input

```json
{
  "query": "What are the bank's card replacement fees?",
  "top_k": 5
}
```

### Output

```json
{
  "status": "ok",
  "data": {
    "docs": [
      {
        "document_id": "policy-card-fees-v1",
        "title": "Card Fees Policy",
        "source": "Synthetic Bank Policy",
        "score": 0.89,
        "excerpt": "Replacement card fees are ..."
      }
    ]
  }
}
```

No reliable evidence is a normal result:

```json
{
  "status": "empty",
  "data": { "docs": [] }
}
```

B provides evidence and citations; it does not decide whether the system may answer.

## C — Rules / State Machine

**Owner:** C
**Called by E:** After understanding results are available, and again when a later rule check is required.

### Input

C receives the business-decision view of `AgentState`, not UI, API, or logging details.

```json
{
  "session_id": "session-001",
  "user_text": "Someone used my card without my permission.",
  "understanding": {
    "intent": "unauthorized_transaction",
    "confidence": 0.97,
    "risk_level": "HIGH",
    "entities": []
  },
  "complaint_status": "NONE",
  "handoff_status": "NOT_REQUIRED",
  "consent": "UNKNOWN"
}
```

For B0 context memory, `AgentState` also carries E-owned request-local fields:
`conversation_context`, `context_reference_resolved`, and
`resolved_user_text`. C must continue to apply all urgent-risk, complaint,
account-operation, handoff and recommendation-permission rules against the
current raw `user_text`. It may use `context_reference_resolved` only to avoid
treating a previously context-free follow-up as context-free when E's typed
resolver has high-confidence, non-ambiguous support. `resolved_user_text` is
available only in that condition and may be used for B query/evidence scope;
it never updates canonical business state or replaces the raw text for safety
checks.

### Output

```json
{
  "status": "ok",
  "data": {
    "action": "ESCALATE",
    "reason_code": "HIGH_RISK_TRANSACTION",
    "next_state": {
      "complaint_status": "OPEN",
      "handoff_status": "ESCALATED"
    }
  }
}
```

- C must return a valid `action` and `reason_code`.
- `next_state` is a state-patch object, not an unstructured message.
- C does not return a final UI response.

The current E implementation calls C through `async decide(state: AgentState)`.
E clears request-local `decision` and `retrieved_docs` before the first call.
After an initial `ANSWER`, E stores B's documents and calls C again while the
first `ANSWER` remains in `state.decision`. C uses that state to distinguish
the pre-retrieval permission check from the final evidence decision. A change
to this sequencing needs a coordinated C/E interface update.

The real C implementation also exposes an optional public
`select_relevant_evidence(question, docs)` hook. E may call it between B and
the second C check to remove malformed or duplicate candidates, but it does
not perform semantic ranking or collapse ordinary B results to one document.
The sole current narrow exception is crypto-wallet recovery: C retains only
its reviewed unsupported-service boundary document, because no other document
is admissible evidence for that conclusion.
E passes the bounded, C-admissible evidence set to the grounded response
generator. C's mandatory second `decide` still owns answer permission and
checks that at least one admissible document supports the requested policy
fact; it retains hard business conditions such as requiring a replacement
reason before applying a reason-specific card fee. The response model must
cite only document IDs from this C-admissible set and must not combine facts
from mutually conditional sources.

## D — Recommendation / Synthetic Data

**Owner:** D
**Called by E:** Only when C explicitly permits recommendation.

### Input

```json
{
  "session_id": "session-001",
  "complaint_status": "RESOLVED",
  "handoff_status": "NOT_REQUIRED",
  "consent": "GRANTED"
}
```

### Output: permitted

```json
{
  "status": "ok",
  "data": {
    "allowed": true,
    "reason_code": "ELIGIBLE_WITH_CONSENT",
    "items": [
      {
        "product_id": "savings-account",
        "name": "Smart Savings Account",
        "rank": 1,
        "reason": "Matches eligible customer profile"
      }
    ]
  }
}
```

### Output: not permitted

```json
{
  "status": "ok",
  "data": {
    "allowed": false,
    "reason_code": "UNRESOLVED_COMPLAINT",
    "items": []
  }
}
```

D owns product-level eligibility filtering and ranking. It does not bypass C's consent, risk, or complaint gate.

## Orchestrator integration rules

1. E creates or restores `AgentState`, calls A, and records its result.
2. E calls C and applies a valid `next_state` patch; E does not create or override a business decision.
3. The initial `ANSWER` route permits E to call B. E records the retrieval result and calls C again before a final evidence-based answer is rendered.
4. The final C decision is `ANSWER` when evidence is sufficient, `ABSTAIN` when the understood question lacks reliable evidence, or `CLARIFY` when a required fact from the user is missing (for example, the reason for a card replacement). `RECOMMEND` permits E to call D. Other actions follow the safe path directly.
5. E returns the unified API/UI response and records the decision trace.

E may optionally use an LLM only as a typed assistant: alongside A to propose
an operational intent/entity/risk draft, after C permits `ANSWER` to rewrite a
retrieval query or render a grounded answer, after C returns `CLARIFY` to
phrase a question, and after C permits `RECOMMEND` and D has returned items to
write a non-factual introduction. E validates
each result and falls back to the existing input/template on failure. The LLM
cannot produce a `Decision`, state patch, or direct tool call; C remains the
business and safety authority.

When B0 context memory is enabled, the typed understanding draft may return a
boolean context-resolution declaration and a bounded restatement of the
current request. E accepts it only for an explicit current-text reference, a
non-ambiguous high-confidence draft, available same-session history, and no
high-risk signal. Provider failure, invalid output, an ambiguous reference, or
a missing history window leaves the existing current-turn path unchanged.

The delivery configuration keeps understanding fusion and retrieval-query
rewriting disabled unless `BANKING_AGENT_LLM_MIDDLE_LOOP=enabled` is explicitly
set. When LLM understanding is enabled, `BANKING_AGENT_LLM_UNDERSTANDING_MODE`
defaults to `shadow`: E validates and traces a draft but passes A's original
result to C. `fuse` is an additional explicit opt-in and may only use a draft
for A `UNKNOWN`/low-confidence results, an explicit context reference together
with an LLM draft marked `ambiguous=true` and `UNKNOWN` (which becomes safe
`UNKNOWN`), a higher risk signal supported by an explicit urgent text signal,
or a non-ambiguous, materially higher-
confidence correction within the bounded low-risk `policy_enquiry` /
`card_fee_enquiry` pair. C-approved clarification wording and
C-approved grounded answer rendering remain available independently. This
prevents an optional provider from silently changing A's route or B's query
during normal delivery runs.

When any of these helpers is enabled, E records a sanitized `E.LLM.understanding`,
`E.LLM.query_rewrite`, `E.LLM.clarification`, `E.LLM.grounded_response`, or
`E.LLM.recommendation_presentation`
trace event.  Its status is `ok` when a validated typed result is used or
`fallback` when the deterministic path is retained. A grounded-response
fallback may carry a bounded technical category such as `invalid_citation` or
`invalid_response`; prompts, provider output,
credentials, and customer text are never added to the trace.
Each LLM trace event may additionally contain numeric `attempts`,
`prompt_tokens`, `completion_tokens`, and `total_tokens` when the provider
returns them.  These are operational metrics only. The current non-streaming
transport records full-call duration, not time-to-first-token.

When a non-empty B0 window is supplied to a context-aware Fusion adapter, E
also emits `E.context_memory` with only the bounded window size category (for
example, `window_2`). It never records the dialogue content, resolved text, or
the model's raw output in a trace.

### E — grounded response generation (optional)

After C's second check returns `ANSWER`, E may invoke its server-side response
generator. It receives only the user question and B documents already approved
by C, and must return Pydantic-validated `answer` text plus one or more
`citation_ids` drawn from those documents. E appends the cited source metadata
itself. Invalid output, an unavailable provider, or an unrecognised citation
causes one bounded render-only retry against the same C-approved documents;
if that retry also fails, E falls back to its deterministic evidence renderer.
The retry never changes C's decision, State patch, B query, evidence set, or
tool sequence. The generator is not run for `ABSTAIN`, `CLARIFY`, `ESCALATE`,
`BLOCK`, complaint, or recommendation routes.

### E — recommendation presentation generation (optional)

After C permits `RECOMMEND` and D returns one or more items, E may invoke a
separate presentation generator only when
`BANKING_AGENT_RECOMMENDATION_RESPONSE_GENERATOR=llm`. It may return a short,
non-factual introduction. E rejects text containing product names, eligibility
conditions, customer facts, monetary values, rates, fees, risk, benefits, or
ranking claims, and falls back to the deterministic renderer on any failure.
E itself always inserts D's original product names, rank order and reasons;
the model never returns or selects product IDs. This helper cannot run before
C/D, change their results, or add product facts not represented in D's dataset.

The deterministic renderer may express a narrowly reviewed implication only
when C has selected its corresponding boundary evidence. For example, the
reviewed fiat-currency boundary document may be rendered as “crypto wallet
recovery is not supported” for a crypto-wallet recovery question because C's
public evidence assessment has already established that cryptocurrency itself
is unsupported. E must not infer comparable service boundaries from arbitrary
documents or use this rendering path after C declines `ANSWER`.

## Empty results and failures

| Module | Normal empty result | Safe integration behavior |
| --- | --- | --- |
| A | Unknown intent or low confidence | C selects a clarification or escalation path. |
| B | No reliable evidence | Recheck with C; do not generate an unsupported answer. The final path is normally `ABSTAIN`. |
| C | Not applicable: a valid action and reason are required | E fails closed: no recommendation or unsupported automatic action. |
| D | `allowed=false` and no items | Do not show a recommendation. |

Technical errors are logged by E with the request trace. They must not be represented as successful business outcomes.

## C and E boundary

C owns business-decision semantics: action, reason code, complaint-state rules, escalation conditions, and recommendation permission. D owns product-level eligibility filtering after C has allowed the recommendation flow.

E owns system-execution semantics: module invocation, state integration, API/UI/voice delivery, logging, and end-to-end validation. E applies a valid transition returned by C but does not invent or override a business decision.

## Phase-one mock requirement

Each module provides a deterministic mock implementation for the agreed scenarios. This allows the text-only end-to-end workflow to run before production models, retrieval infrastructure, recommendation logic, or voice adapters are introduced.

## E provider gateway

E may provide an injectable asynchronous LLM transport for future A/C owners.
It accepts provider-neutral messages and returns only Pydantic-validated
structured data or a sanitized transport error (`configuration`, `timeout`,
`rate_limited`, `unavailable`, `invalid_response`, or `idempotency_conflict`).
Callers may provide an opaque, non-sensitive idempotency key: E reuses it for
all transport retries, coalesces in-flight duplicates, and retains successful
results in process memory for a short configured TTL. It is server-side only:
provider keys, prompts, raw outputs, and vendor error bodies must not be stored
in browser code, persistence, or decision traces. E does not translate LLM
output into a `Decision`, `RuleStatePatch`, action, reason code, or any other
business state; A/C remain responsible for their public module contracts.

Before either mock or external-provider generation, E applies a conservative
outbound privacy guard. PINs, OTPs, passwords, CVV/CVC and comparable supplied
credentials fail closed with `sensitive_data_blocked`. Recognised full card
numbers (Luhn-valid), labelled account numbers, Singapore phone numbers, email
addresses and NRIC-like identifiers are replaced with stable request-local
placeholders. This is a baseline data-minimisation control, not a substitute
for provider retention, regional-processing and contractual review.

## D phase-one implementation and async handoff

D exposes the pure function `recommend(request, *, customer_profiles, products)`
and `RecommendationAdapter(dataset)`, whose async method is
`recommend(session_id, complaint_status, handoff_status, consent)`.
The async method matches E's proposed public Protocol and returns a mapping
compatible with E's RecommendationResult. Data is injected at initialization;
D does not import the orchestrator or any other domain module.

The pure function keeps its generic error envelope `{"status":"error","data":{}}`.
The async adapter omits data on errors (`{"status":"error"}`), because E's typed
RecommendationData rejects an empty object even when status is error.
Business denials always use ok, allowed=false and items=[], never empty.

Synthetic session/profile association is explicit and is not authentication.
For the local application, a user selects a validated synthetic profile only at
registration. E snapshots that key onto every new conversation and, only in
production composition, `ConversationProfileRecommendationAdapter` resolves the
conversation UUID to that snapshot before calling D. Conversation and message
requests cannot supply or override the key. Legacy conversations without a
snapshot and unknown keys fail closed; D never supplies a default profile.
Demo product eligibility checks age, Singapore residence and integer SGD cents.
Ranking is goal match, ascending demo_priority, then product_id.
These three demo products are not authorized NovaBank offerings or interest-rate
policies. Their inclusion in the final bank catalog needs B/C/E review.

C remains responsible for risk and recommendation permission. E calls D only
after C returns RECOMMEND; the four-field input cannot independently prove that
permission. Defensive complaint/consent checks can only reject.
The canonical RuleStatePatch excludes consent; D does not create consent.

See [D handoff](d_recommendation_handoff.md) for data injection, error handling,
scenario expectations, reproduction commands and remaining team decisions.
## E text-mock adapter implementation

The first integration implementation uses async Python adapters in
`app/orchestrator/interfaces.py`. This is an initial integration contract for
module owners to review; existing business semantics and canonical enums are unchanged.

- A: `analyze(session_id, user_text)` → `IntentResult`.
- B: `retrieve(query, top_k)` → `RetrievalResult`.
- C: `decide(state)` → `RulesResult`. Receives an isolated `AgentState` snapshot;
  UI/logging fields are not business-decision inputs. Evidence is available in
  `retrieved_docs` on the second call.
- D: `recommend(session_id, complaint_status, handoff_status, consent)` →
  `RecommendationResult`.

### B synchronous implementation bridge

B's current public `Retriever` implementation is synchronous.  E composes it
through `app.retrieval_adapter.AsyncRetrievalAdapter`, which runs only the
public `Retriever.retrieve(query, top_k)` call in a worker thread and exposes
the existing async B protocol.  It does not inspect, rank, filter, or alter
evidence.  An unexpected synchronous backend exception becomes the sanitized
`{"status": "error"}` envelope, so the orchestrator fails closed under its
normal B error handling.  This preserves a single public adapter contract while
allowing future B implementations to provide a native async adapter directly.

Adapters may return a validated result model or a mapping conforming to that
model. Non-error envelopes require typed `data`; `error` may omit data. A normal
empty A result includes an unknown understanding; B includes an empty docs list;
D includes its permission result and items. C must return `ok` with a decision.
The orchestrator validates every envelope and applies only the canonical
`RuleStatePatch`. It does not implement business-policy conditions.

The default per-call timeout is 10 seconds and can be overridden at construction.
Timeouts, exceptions, invalid results and explicit module errors return an
application response with `status=error`, a sanitized module/error code, and no
final business decision, citations or recommendations. Partial state is retained
for internal inspection; it is not a successful business outcome. An evidence-free
final `ANSWER` from C is a contract error, not an E-created `ABSTAIN` decision.
The input state is not mutated; previous-turn evidence, decisions, recommendations
and response text are cleared before processing a new request.

`AgentResponse` is an internal application result, not a finalized public HTTP
schema. It includes state for testing. The local application explicitly converts
it into `ChatTurnResponseV1` in `app/api/dto.py`; the public model exposes only
the request ID, a user-facing message, action, safe citation metadata, rendered
recommendations, and a generic error code. It excludes State, reason codes,
state patches, technical module/error details, document IDs, scores, and excerpts.
Text rendering currently uses deterministic templates and synthetic evidence
excerpts. Request IDs are generated and sanitized decision traces are persisted
by the local application layer.

## Local text-mock application API

The dependency-free local application at `app/api/server.py` is an E-owned
development aid, not a production banking API. It exposes the browser page at
`/`, uses a local SQLite file of synthetic-only test accounts, and sends a
random opaque session token in a loopback-only HttpOnly cookie. Passwords are
salted and derived with `scrypt`; the database stores only hashes. It has these
same-origin JSON endpoints:

| Endpoint | Purpose | Request / response |
| --- | --- | --- |
| `POST /api/auth/register` | Creates a synthetic local account. | Username, 6+ character test password, and `synthetic_profile_key` selected from `GET /api/config`. The choice is local fixture configuration, not authentication. |
| `POST /api/auth/login` / `logout` | Starts or clears the local session. | Login returns an HttpOnly cookie. |
| `GET /api/me` | Returns the current synthetic account. | Requires authentication. |
| `GET /api/config` | Returns the active application module mode and valid local synthetic profiles. | `{ "module_mode": "fixture" | "production", "synthetic_profiles": [{"id":"session-001","label":"..."}] }`; used by the UI to select its input surface and registration profile. |
| `GET /api/scenarios` | Lists the selectable S01--S08 synthetic scenarios. | Fixture mode only; scenario IDs and fixture user text only. |
| `GET` / `POST /api/conversations` | Lists or creates the caller's conversations. | Fixture mode creates with `{"scenario_id":"S01"}`. Production mode creates and runs the first turn with `{"user_text":"synthetic test text"}`. The account's profile key is snapshotted server-side; payloads carrying `synthetic_profile_key` are rejected. |
| `GET /api/conversations/{id}` | Returns one caller-owned conversation and its history. | Other users receive `conversation_not_found`. |
| `POST /api/conversations/{id}/messages` | Runs one controlled turn through the real orchestrator. | Fixture mode requires `{"scenario_id":"S01","expected_version":0}`; production mode requires `{"user_text":"synthetic test text","expected_version":0}`. A profile override is rejected. It atomically persists the user/assistant turn and a successful C-controlled state update. A stale version returns `409 conversation_version_conflict`. |
| `GET /api/developer/conversations/{id}/traces` | Returns restricted developer trace metadata. | Disabled unless explicit local developer mode is enabled. |

The message endpoint returns this versioned public shape inside its `response`
field (alongside the separately defined conversation object):

```json
{
  "api_version": "v1",
  "request_id": "request-id",
  "status": "ok",
  "message": {"kind": "answer", "text": "..."},
  "decision": {"action": "ANSWER"},
  "citations": [{"title": "Card Fees Policy", "source": "Synthetic Bank Policy"}],
  "recommendations": [],
  "error": null
}
```

For an application failure, `message.kind` is `technical_error`, `decision`,
citations and recommendations are empty, and `error.code` is the stable public
value `agent_unavailable`. The internal module identity and technical code remain
only in the decision trace.

In fixture mode, the server uses `ScenarioModules`, which replays the fixture's
pre-scripted module envelopes and is deliberately not an A/B/C/D implementation.
Production mode accepts only 1--2,000-character synthetic test text after E has
explicitly injected a complete owner-provided `ModuleBundle`; it remains a loopback
development aid and must not be exposed as a production banking endpoint. The core
orchestrator remains storage-independent:
the application restores a state snapshot before a turn and saves only the
resulting valid state after a successful response. The persisted message history
contains the public response only; the independently stored conversation state
is not exposed in the per-turn response.

The API depends on the E-owned `ApplicationStore` Protocol rather than a
database implementation. `SQLiteStore` remains the local synthetic-data default;
`InMemoryStore` is used for application tests. A future durable implementation
must satisfy the same user, session, conversation, turn, and trace methods, including
an atomic `expected_version` conversation-turn commit, so changing databases does not
alter API routes or agent orchestration. `SQLiteStore` migrates local databases created
before this field by adding a version of zero. It also adds nullable profile
binding columns without assigning legacy users or conversations a default;
recommendation resolution therefore fails closed until a new bound conversation
is created.

## Module composition and migration

`app/bootstrap.py` is the E-owned composition root. Routes request a
`ModuleBundle` from its `ModuleFactory`; routes do not import or construct A/B/C/D
adapters. The default `fixture` mode creates a fresh `ScenarioModules` bundle for
each selected fixture, preserving deterministic scenario behavior. `production`
mode fails closed until E explicitly supplies a `ModuleBundle` of owner-provided
adapters implementing the existing public Protocols. Thus, replacing fixtures
with real implementations changes composition only—not the API, session store,
frontend, shared schema, or orchestrator.

## Voice / ASR extension (terminal MVP)

`modules/voice/` is an E-owned extension boundary and is deliberately not part
of the text-agent `ModuleBundle` yet. Its public contract is `ASRService` and
the `AudioUpload` / `TranscriptionResult` schemas. The first local format is
only `audio/wav`, PCM, 16 kHz, mono, 16-bit, with a maximum duration of 60
seconds and a maximum size of 10 MiB. Invalid input is rejected with a stable,
non-sensitive validation code before any backend is invoked.

`ASRService` writes an accepted payload only to a uniquely named temporary
directory, passes that path to an `ASRBackend`, and removes the directory on
both success and failure. Audio bytes, local file paths, and unconfirmed
transcripts must not be added to `AgentState`, SQLite, decision traces, or
application logs. `WhisperCppBackend` uses explicit local executable and model
paths, does not download models, and does not send audio remotely. The terminal
entry point is `python -m banking_agent.modules.voice.cli`; its default mock
backend exists for deterministic local verification.

A successful result is only a candidate transcript. A later voice controller
must display it and obtain an explicit user confirmation before supplying its
text to the existing A/C/B/D flow. ASR quality fields are diagnostics, not an
authorization or safety confidence signal; C remains the sole decision gate.

`modules.voice.ascend_eval` is a local evaluation utility, not an application
path. It deterministically selects 80 clips from the public ASCEND test split
(60 Mandarin-English mixed, 10 Mandarin, 10 English; evenly distributed among
the available source speakers within each stratum) and downloads only those clips into an ignored artifact
directory. Its report remains local because it contains source transcripts and
model hypotheses. The utility's mixed-token error rate is a smoke metric for
iteration, not a production-quality claim or an authorization decision.

## Decision traces

The E-owned `app/observability.py` produces one sanitized `DecisionTrace` for
every orchestrator request, including technical failures. It records request and
session identifiers, fixture/production mode, scenario ID when applicable,
module call order/status/duration, understanding summary, before/after complaint
and handoff states, final action/reason, retrieved document IDs, recommendation
count, controlled state patch, result status, a sanitized technical-error code,
and total duration. A SHA-256 hash may associate duplicate text without storing
the text itself.

The local SQLite store writes these traces to `decision_traces`. The only trace
route is protected by an explicit local developer-mode flag and configured local
developer username; it is disabled by default and is not linked from the user
chat UI. Full user text, assistant text, passwords, cookies, tokens, exception
details, and full evidence excerpts are excluded. Failure to write a trace never
changes an otherwise safe agent result. Production deployment requires proper
role-based access control rather than this local allow-list.

## Adapter contract test harness

`tests/helpers/adapter_contracts.py` is an E-owned reusable validation harness
for module handoff. It calls only the public adapter Protocols and validates the
result envelopes and integration invariants: A's normal empty understanding is
unknown; B's empty result has no documents; C has no normal empty result; and D
denial uses `ok`, `allowed=false`, and no items. Technical `error` envelopes are
valid for safe failure handling. The harness does not evaluate intent accuracy,
retrieval quality, rules policy, or recommendation ranking; those remain with
the relevant owner.

`tests/helpers/mock_modules.py` contains E-owned test doubles, not production
A/B/C/D implementations or domain policies. S01–S08 fixtures follow the Scenario
Table. `POLICY_RETRIEVAL_PERMITTED` is a provisional pre-evidence mock reason code
for C to confirm; final reason codes match the documented scenarios. Mock test
passes establish integration behavior, not domain-model accuracy or production readiness.
