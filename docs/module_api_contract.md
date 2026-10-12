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
  "top_k": 3
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
4. The final C decision is `ANSWER` when evidence is sufficient, or `ABSTAIN` when it is not. `RECOMMEND` permits E to call D. Other actions follow the safe path directly.
5. E returns the unified API/UI response and records the decision trace.

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
| `POST /api/auth/register` | Creates a synthetic local account. | Username and 6+ character test password. |
| `POST /api/auth/login` / `logout` | Starts or clears the local session. | Login returns an HttpOnly cookie. |
| `GET /api/me` | Returns the current synthetic account. | Requires authentication. |
| `GET /api/scenarios` | Lists the selectable S01--S08 synthetic scenarios. | Scenario IDs and fixture user text only. |
| `GET` / `POST /api/conversations` | Lists or creates the caller's conversations. | Create with `{"scenario_id":"S01"}`. |
| `GET /api/conversations/{id}` | Returns one caller-owned conversation and its history. | Other users receive `conversation_not_found`. |
| `POST /api/conversations/{id}/messages` | Runs one selected fixture through the real orchestrator. | Persists the user/assistant turn and a successful C-controlled state update. |
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

The server uses `ScenarioModules`, which replays the fixture's pre-scripted
module envelopes and is deliberately not an A/B/C/D implementation. It accepts
no arbitrary customer text, listens on loopback only, and must not be exposed
as a production endpoint. The core orchestrator remains storage-independent:
the application restores a state snapshot before a turn and saves only the
resulting valid state after a successful response. The persisted message history
contains the public response only; the independently stored conversation state
is not exposed in the per-turn response.

The API depends on the E-owned `ApplicationStore` Protocol rather than a
database implementation. `SQLiteStore` remains the local synthetic-data default;
`InMemoryStore` is used for application tests. A future durable implementation
must satisfy the same user, session, conversation, turn, and trace methods, so
changing databases does not alter API routes or agent orchestration.

## Module composition and migration

`app/bootstrap.py` is the E-owned composition root. Routes request a
`ModuleBundle` from its `ModuleFactory`; routes do not import or construct A/B/C/D
adapters. The default `fixture` mode creates a fresh `ScenarioModules` bundle for
each selected fixture, preserving deterministic scenario behavior. `production`
mode fails closed until E explicitly supplies a `ModuleBundle` of owner-provided
adapters implementing the existing public Protocols. Thus, replacing fixtures
with real implementations changes composition only—not the API, session store,
frontend, shared schema, or orchestrator.

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
