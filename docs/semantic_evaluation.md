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
one or more case-insensitive regular-expression alternatives. A response must
match one alternative in every required group. This checks facts such as the
lost-card replacement amount and express-delivery amount without demanding one
fixed LLM sentence. `forbidden_patterns` reject unsafe claims. The evaluator
does not write raw responses or prompts into the report.

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
