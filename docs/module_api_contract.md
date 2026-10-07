# Module API Contract

## Purpose

This document defines the integration boundary between the four domain modules and the E-owned application layer. It specifies what each module receives and returns; it does not prescribe models, databases, or implementation frameworks.

The canonical shared fields and enums will be defined in `agent_state_schema.md`.

## Shared conventions

- Modules return structured results, not final UI text.
- All modules use the shared enums and field names once the state schema is agreed.
- A normal empty result is different from a technical failure and must be reported clearly.
- Implementations must be replaceable: phase-one mocks and later production implementations keep the same contract.

## Core module contracts

| Module | Owner | Called by E when | Input | Structured output |
| --- | --- | --- | --- | --- |
| Intent / Risk / Entity | A | A user text request starts | `user_text` | `intent`, `confidence`, `risk_level`, `entities` |
| Rules / State Machine | C | Understanding results are available; may be rechecked after later results | `AgentState` | `action`, `reason_code`, `next_state` |
| RAG / Knowledge Base | B | Rules allow an evidence-based answer | Query/context from `AgentState` | `docs`, `source`, `score` |
| Recommendation | D | Rules explicitly allow a recommendation | `AgentState` | `allowed`, `items`, `reason_code` |

## Integration flow

1. E accepts a request and creates or restores the session state.
2. E calls A and records the understanding result in `AgentState`.
3. E calls C. C returns the permitted business action and state transition.
4. E follows that action: call B for `ANSWER`, D for `RECOMMEND`, or render the required safe path for `ESCALATE`, `CLARIFY`, `BLOCK`, or `HANDLE_COMPLAINT`.
5. E returns the unified API/UI response and records a decision trace.

## Empty results and failures

| Module | Normal empty result | Safe integration behavior |
| --- | --- | --- |
| A | Unknown intent or low confidence | C selects a clarification or escalation path. |
| B | No reliable evidence | Do not generate an unsupported answer; use a safe clarification or handoff path. |
| C | Not applicable: a valid action and reason are required | E fails closed: no recommendation or unsupported automatic action. |
| D | `allowed=false` and no items | Do not show a recommendation. |

Technical errors are logged by E with the request trace. They must not be represented as successful business outcomes.

## C and E boundary

C owns business decision semantics: action, reason code, complaint-state rules, escalation conditions, and recommendation permission.

E owns system execution semantics: module invocation, state integration, API/UI/voice delivery, logging, and end-to-end validation. E applies a valid transition returned by C but does not invent or override a business decision.

## Phase-one mock requirement

Each module provides a deterministic mock implementation that returns the structured result above for the agreed scenarios. This allows the text-only end-to-end workflow to run before production models, retrieval infrastructure, recommendation logic, or voice adapters are introduced.
