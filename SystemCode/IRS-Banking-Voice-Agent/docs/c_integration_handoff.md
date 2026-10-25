# C integration handoff (local proposal, 2026-10-20)

## Basis and scope

This C patch was rebased locally onto team `main` commit
`517d32a893edf6606e76a6d954fd0ea63110bdf0`. The reconstructed local
snapshot's 53 files changed since the earlier ZIP were checked against their
GitHub blob hashes. On 2026-10-20, the complete current-main GitHub tree was
checked again: all 170 remote blobs matched the local baseline by Git blob
SHA, with no missing or extra files. Nothing was committed or pushed.

The patch changes C's rules package, C unit/evaluation fixtures, two C/E
integration tests, and the Scenario Table/API Contract explanations. It does
not change A, B, D, E executable code or the canonical State/enums.

## What was run

- `tests/unit`: 107 tests passed (C, D, E and shared-schema tests).
- `tests/integration`: 37 tests passed, including 11 new C/E composition and
  API smoke tests. The actual `RuleEngine` was injected into E's current
  `Orchestrator` and `DemoApplication`; B's maintained-corpus
  `MockRetriever` and D's `RecommendationAdapter` were used.
- `tests/e2e`: 1 existing fixture-scenario test passed. That existing test
  uses scripted C; the new integration tests exercise the real C adapter.
- C's 31-case synthetic matrix passed: all 7 marked urgent cases escalated;
  none of 6 denied-recommendation or 13 unsupported-answer cases violated the
  expected gate. These are regression cases, not a population estimate.
- The patch was checked and applied to a pristine local snapshot of the above
  `main` commit.
- A direct WSGI-entrypoint smoke run with the injected production `ModuleBundle`
  passed registration/login, generic replacement-fee CLARIFY, specific
  lost-card fee ANSWER with citation, complaint OPEN persistence, and a
  subsequent blocked recommendation. This exercised the same WSGI route
  handling without opening a local TCP socket; the sandbox denied socket
  binding before an HTTP listener could start.

The API smoke tests cover generic replacement-fee clarification, a specific
lost-card fee with citation, misclassified scam escalation with persisted
OPEN/ESCALATED state, and a complaint that blocks a misclassified offer on
the next turn. The orchestrator tests cover S01-S08, no/irrelevant evidence,
consent blocking, and actual D ranking with an explicit synthetic session
mapping. One additional E orchestration test verifies that a shipping price
joined by a comma or conjunction to an unresolved replacement-fee statement
does not appear in the final answer or citations.
Misclassified account-hack and credential-leak reports also reach the urgent
route with distinct reason codes.

## Current interface

E can inject `RuleEngine()` as the `rules` member of its
`ModuleBundle`. C implements `async decide(state)` and returns the shared
envelope as a mapping. E clears request-local outputs before the first C call
and retains the initial ANSWER before the second call after B; C relies on
that marker. E applies only the whitelisted `next_state` patch and calls D
only after RECOMMEND.

C checks every retrieved excerpt because E's response builder renders all
retrieved excerpts on ANSWER. Ranking scores are not treated as answerability
probabilities. A generic replacement-fee question is clarified when B only
returns a reason-specific price. An explicit lost-card condition is routed to
card-security escalation before retrieval, including a fee question. A delivery time or a separate
shipping charge does not satisfy a replacement-fee question.

## Joint work before claiming full end-to-end alignment

1. **A production adapter is absent on current main.** The tests inject a
   synthetic understanding adapter or E's scenario fixtures. Real A intent
   labels and risk confidence need joint evaluation with C's gates.
2. **B real retrieval was not exercised in this environment.** The bundled
   Python has no `rank_bm25`, `sentence_transformers` or `torch`, and B's
   real model has no calibrated evidence-rejection gate. Run held-out
   supported and no-evidence questions with the configured real B backend,
   then inspect C abstention/clarification and E's rendered text together.
3. **S01 policy wording differs.** E's S01 fixture gives a generic SGD 10
   card-replacement fee; B's maintained lost-card evidence gives SGD 15
   replacement plus SGD 10 express shipping. Align fixture/policy wording.
   E's current CLARIFY text is generic; it should ask which replacement
   reason applies for `REPLACEMENT_REASON_REQUIRED`.
4. **Complaint closure is not yet an application workflow.** E persists
   conversation status, version and decision traces, but has no authenticated
   human review/resolution event history or stored resolution evidence.
   C's `ComplaintStateMachine.transition_case` validates those events when
   E supplies them. A customer sentence alone cannot resolve a case.
5. **D session association is still synthetic configuration.** D rejects
   unknown session IDs. E's generated conversation UUIDs need an explicit
   synthetic profile association before permitted recommendations can be
   demonstrated through the normal production-mode API.
6. **The default API mode uses fixture modules.** Testing the actual C
   adapter requires an explicit production `ModuleBundle`. This was done
   in the new composition tests; default demo mode does not automatically
   load C, B real retrieval or D.

C's evidence gate is conservative lexical matching, not a proof of arbitrary
entailment. The current joint smoke tests establish contract compatibility
and the listed safe paths; they do not establish real-model answer quality.
