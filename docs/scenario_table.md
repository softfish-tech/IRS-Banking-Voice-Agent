# Scenario Table

## Purpose

This table defines the phase-one business-acceptance scenarios for the text-only workflow. It is the shared reference for C's rules tests, A/B/D representative inputs, and E's future end-to-end fixtures.

The table specifies expected workflow behavior, not exact final-response wording.

## Shared rules

- All state and action values follow `src/banking_agent/schemas/`.
- High-risk signals take precedence over low intent confidence.
- An unresolved complaint blocks Recommendation before D is called.
- C controls whether the Recommendation flow is permitted; D performs product-level eligibility filtering and ranking.
- An unsupported answer must not be generated without reliable evidence.
- `CLARIFY` means the request is unclear or missing required information. `ABSTAIN` means the request is understood but lacks reliable evidence.
- Reason codes below are the proposed first set for C to confirm.

## Core scenarios

| ID | Scenario and input | Initial state | Mock understanding / retrieval | Expected final decision | Required orchestration behavior | Acceptance checks |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | **Grounded policy enquiry** — “What is the replacement fee for my card?” | `complaint=NONE`, `handoff=NOT_REQUIRED`, `consent=UNKNOWN` | A: `card_fee_enquiry`, `0.94`, `LOW`; B: reliable policy evidence | `ANSWER`, `POLICY_EVIDENCE_FOUND` | C pre-check allows answer route; E calls B; E asks C for post-evidence confirmation; D is not called | Final response is grounded in returned evidence and includes a citation/source |
| S02 | **Fee complaint** — “I was charged a fee I do not understand.” | `complaint=NONE`, `handoff=NOT_REQUIRED`, `consent=UNKNOWN` | A: `fee_complaint`, `0.92`, `MEDIUM` | `HANDLE_COMPLAINT`, `FEE_COMPLAINT`; patch: `complaint=OPEN` | E calls A then C; D is not called | State is `OPEN`; response acknowledges simulated complaint handling; no recommendation |
| S03 | **Unauthorized transaction** — “Someone used my card without my permission.” | `complaint=NONE`, `handoff=NOT_REQUIRED`, `consent=UNKNOWN` | A: `unauthorized_transaction`, `0.97`, `HIGH` | `ESCALATE`, `HIGH_RISK_TRANSACTION`; patch: `complaint=OPEN`, `handoff=ESCALATED` | E calls A and C only; B and D are not called | Safe handoff response; complaint remains unresolved; no evidence answer or recommendation |
| S04 | **Fraud suspicion** — “I think this transfer may be a scam.” | `complaint=NONE`, `handoff=NOT_REQUIRED`, `consent=UNKNOWN` | A: `fraud_suspicion`, `0.95`, `HIGH` | `ESCALATE`, `FRAUD_SUSPICION`; patch: `complaint=OPEN`, `handoff=ESCALATED` | E calls A and C only; B and D are not called | Safe handoff response; complaint remains unresolved; no recommendation |
| S05 | **Open complaint blocks recommendation** — “Can you recommend a savings product while my fee complaint is still open?” | `complaint=OPEN`, `handoff=NOT_REQUIRED`, `consent=GRANTED` | A: `product_recommendation`, `0.91`, `LOW` | `BLOCK`, `UNRESOLVED_COMPLAINT` | D is not called | Response explains recommendation is unavailable until resolution; `recommendations=[]` |
| S06 | **Recommendation after resolution** — “My complaint is resolved. Can you recommend a suitable savings product?” | `complaint=RESOLVED`, `handoff=NOT_REQUIRED`, `consent=GRANTED` | A: `product_recommendation`, `0.93`, `LOW`; D: allowed, ranked items | `RECOMMEND`, `RECOMMENDATION_PERMITTED` | C permits D; D filters eligible synthetic products and ranks them | D is called; recommendations are non-empty; response presents permitted recommendation(s) |
| S07 | **Low confidence** — “I need help with that thing from before.” | `complaint=NONE`, `handoff=NOT_REQUIRED`, `consent=UNKNOWN` | A: `UNKNOWN`, `0.31`, `UNKNOWN` | `CLARIFY`, `LOW_INTENT_CONFIDENCE` | B and D are not called | Response asks a targeted clarification; no unsupported assumption |
| S08 | **No reliable evidence** — “What is the bank policy for crypto wallet recovery?” | `complaint=NONE`, `handoff=NOT_REQUIRED`, `consent=UNKNOWN` | A: `policy_enquiry`, `0.88`, `LOW`; B: `status=empty`, `docs=[]` | `ABSTAIN`, `INSUFFICIENT_EVIDENCE` | C pre-check allows retrieval; E calls B; C post-check returns `ABSTAIN`; D is not called | No unsupported policy answer; response states reliable information is unavailable and offers further assistance |

## Rule-precedence case

The low-confidence route must not suppress a high-risk route. C must apply this order:

```text
HIGH_RISK
> hard business constraints
> low confidence / uncertainty
> normal routing
```

This priority is covered by C's rule tests. A future E2E scenario should include a low-confidence, high-risk utterance and expect `ESCALATE`.

## Planned focused scenarios

These scenarios are valuable but are not required for the first text-mock demonstration:

| ID | Focus | Expected result | Primary owner |
| --- | --- | --- | --- |
| S09 | Resolved complaint without consent | `BLOCK`, `CONSENT_REQUIRED`; D not called | C + E |
| S10 | No eligible product after C permits Recommendation | D returns `allowed=false`, `NO_ELIGIBLE_PRODUCT` | D + E |
| S11 | Complaint lifecycle | `OPEN → UNDER_REVIEW → RESOLVED` | C |

## Future E2E fixture mapping

When implementation begins, each core scenario maps to a fixture under `tests/fixtures/scenarios/` and a test under `tests/e2e/`, using the same `S01`–`S08` identifier.

## D reference fixtures and replacement verification

D's synthetic S05/S06/S09/S10 cases live in
`tests/fixtures/scenarios/recommendation.json`.
Direct S05/S09 calls test defensive rejection only; C/E must prevent those calls
in an integrated workflow. S09/S10 remain optional focused scenarios.

`scripts/check_recommendation_e.py` requires E's public test harness and
orchestrator, replaces only D with the real recommendation implementation,
and replays S01-S08 with scripted A/B/C. S06 returns three demo products instead
of E's one scripted product; the acceptance requirement remains non-empty,
eligible, ranked recommendations. The existing core fixture is unchanged.
The same check covers no eligible products, unknown sessions, defensive denial,
C's complaint patch before D, and rejection of a consent patch.
This establishes E/D compatibility, not real A/B/C quality or voice completion.
