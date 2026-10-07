# Module API Contract

## Purpose

This document defines the integration boundary between the four domain modules and the E-owned application layer. It specifies the structured data each module receives and returns; it does not prescribe HTTP routes, models, databases, or implementation frameworks.

The canonical shared fields and enums will be defined in `agent_state_schema.md`.

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
  "intent": "unauthorized_transaction",
  "intent_confidence": 0.97,
  "risk_level": "HIGH",
  "complaint_status": "NONE",
  "consent": false,
  "eligibility": null
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
      "complaint_status": "ESCALATED"
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
  "consent": true,
  "eligibility": {
    "eligible_products": ["savings_account"]
  }
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

D does not bypass consent, eligibility, risk, or complaint rules.

## Orchestrator integration rules

1. E creates or restores `AgentState`, calls A, and records its result.
2. E calls C and applies a valid `next_state` patch; E does not create or override a business decision.
3. `ANSWER` permits E to call B. `RECOMMEND` permits E to call D. Other actions follow the safe path directly.
4. E returns the unified API/UI response and records the decision trace.

## Empty results and failures

| Module | Normal empty result | Safe integration behavior |
| --- | --- | --- |
| A | Unknown intent or low confidence | C selects a clarification or escalation path. |
| B | No reliable evidence | Do not generate an unsupported answer; use a safe clarification or handoff path. |
| C | Not applicable: a valid action and reason are required | E fails closed: no recommendation or unsupported automatic action. |
| D | `allowed=false` and no items | Do not show a recommendation. |

Technical errors are logged by E with the request trace. They must not be represented as successful business outcomes.

## C and E boundary

C owns business-decision semantics: action, reason code, complaint-state rules, escalation conditions, and recommendation permission.

E owns system-execution semantics: module invocation, state integration, API/UI/voice delivery, logging, and end-to-end validation. E applies a valid transition returned by C but does not invent or override a business decision.

## Phase-one mock requirement

Each module provides a deterministic mock implementation for the agreed scenarios. This allows the text-only end-to-end workflow to run before production models, retrieval infrastructure, recommendation logic, or voice adapters are introduced.
