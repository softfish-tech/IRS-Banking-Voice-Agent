# Module C: rules, complaint arbitration and evidence permission

This module owns deterministic business decisions. It uses only the canonical
`AgentState`, `Decision`, `RuleStatePatch` and enums. It does not generate final
customer text, rank products, retrieve documents, or execute transactions.
All examples use fictional data.

## Public interfaces

E's implementation on `main` calls the async protocol:

```python
from banking_agent.modules.rules import RuleEngine

rules = RuleEngine()
result = await rules.decide(state)  # {"status": "ok", "data": Decision}
```

`RuleEngine.decide` returns a plain mapping because E parses it with its own
`schemas.module_results.RulesResult` model. E clears `state.decision` before
the first C call. If C initially returns `ANSWER`, E calls B, stores its docs
and calls C again while the first decision remains in State. The adapter uses
that prior `ANSWER` as its post-retrieval marker. B technical errors go through
E's technical-error path; a successful empty retrieval becomes `ABSTAIN`.

For isolated use, `RuleEngine.evaluate(state, rag_status=...)` and
`evaluate_rules(...)` return C's local typed `RulesResult`. `rag_status=None`
is a pre-retrieval check; `ok`, `empty`, or `error` denotes the B outcome.

## Arbitration order

1. **Urgent risk:** HIGH risk, explicit fraud/unauthorized/lost-card intents,
   or narrow customer-report patterns yield `ESCALATE`. Low A confidence
   cannot suppress this route. Text reports about a card, account or
   credentials retain distinct security reason codes. An existing OPEN or
   UNDER_REVIEW complaint is preserved; otherwise an OPEN case is requested.
   Handoff becomes ESCALATED.
2. **Hard constraints:** recommendation is blocked for unresolved complaint,
   active handoff, absent trusted resolution, missing consent, or risk other
   than LOW. Account-specific reads and transaction commands are blocked
   because current State has no authentication or transaction capability.
   Narrow explicit request patterns also guard these routes when A supplies
   the wrong intent label.
3. **Uncertainty:** low or missing intent confidence, unknown intent or
   unknown risk yields `CLARIFY`.
4. **Normal routing:** fee/other complaints are opened or kept active;
   recommendation merely permits E to call D; policy questions reach B and
   require a second C check before `ANSWER`.

The default confidence threshold is `0.70`. This is a phase-one mock policy,
not a calibrated model threshold or grading target. C never changes consent.

## Complaint lifecycle

`ComplaintArbitrator` decides complaint and urgent-risk actions. It reuses
`ComplaintStateMachine` for opening, so a repeated complaint cannot create a
second active case. A new report after RESOLVED reopens a case; customer text
alone cannot mark a case RESOLVED.

`ComplaintStateMachine.transition_case` supports `OPEN`, `START_REVIEW`,
`ESCALATE`, and `RESOLVE` on an immutable `ComplaintSnapshot`. It rejects
stale revisions, repeated most-recent event IDs, invalid jumps and automated
review/resolution. A human-agent resolution requires an opaque evidence
reference; an active handoff also requires authenticated human clearance.
The simpler `transition` method remains for status-only callers.

E must authenticate human roles, persist `ComplaintSnapshot` and the event
history, enforce global event-ID uniqueness, and store resolution evidence.
The current shared AgentState contains only complaint and handoff status, so
it cannot itself prove a preloaded `RESOLVED` state. S06 is a trusted
synthetic fixture until E adds those case-management capabilities.

## Evidence permission

B's `ok` and ranking score mean candidate retrieval, not answer permission.
`EvidenceArbitrator` checks every document because E currently renders every
retrieved excerpt. It rejects empty/malformed documents, non-finite scores,
topic mismatch and missing requested details or values. It requires each
rendered excerpt to cover all salient request terms after a small set of
normalizations, so paraphrases outside that set can cause safe abstention.
For fee questions it also requires a monetary value tied to the requested
subject within the same short clause; delivery times and separate shipping
charges do not count, including when joined by a comma or conjunction.
It does not use a cross-backend score threshold. A generic card-replacement fee question is
clarified when the evidence only states a reason-specific price; a specified
lost-card fee can be answered from matching evidence.

This deterministic gate cannot prove arbitrary natural-language entailment,
resolve all conflicting policy conditions, or certify real-bank accuracy. It
is deliberately conservative. A richer evidence verifier or a C-approved
document-ID field would need E/B contract coordination. Until then, no
retrieved candidates and obvious unsupported questions yield `ABSTAIN`.

## D and E integration

`RECOMMEND` means only that E may invoke D. D owns customer/product eligibility
and ranking, and may still return `allowed=false`. E must not invoke D after
BLOCK, CLARIFY, ESCALATE, HANDLE_COMPLAINT, ANSWER, or ABSTAIN. D's fixture
session IDs need an explicit synthetic mapping at E's composition root; they
must never be treated as authentication.

The C package does not import A/B/D internals or edit shared State/contracts.
See `docs/c_integration_handoff.md` for the tested `main` version and open
cross-owner decisions.

## Reproduce

Use Python 3.11+ with Pydantic 2 from `pyproject.toml`:

```sh
PYTHONPATH=src python -m unittest discover -s tests/unit -v
PYTHONPATH=src:tests python -m unittest discover -s tests/integration -v
PYTHONPATH=src python -m banking_agent.modules.rules.evaluate_rules
```

The 31-case synthetic decision matrix reports exact action/reason accuracy,
safe escalation rate, recommendation violation rate and unsupported-answer
rate, with a deliberately naive classifier-only baseline. These figures are
regression checks on synthetic cases, not generalization estimates.
