# Intent / Risk / Entity module (Part A)

Owner: A. Code: `src/banking_agent/modules/intent/`.

This module is the perception step of the pipeline. E calls it once per user
turn with `{session_id, user_text}`; the result seeds the Rules module (C). It
does **not** return an action, a reason code, or a final response, and it never
reads business state such as the complaint status or consent.

## Interface

| Function | Purpose |
| --- | --- |
| `classify(text) -> UnderstandingResult` | Main entry point. |
| `classify_by_rules(text) -> UnderstandingResult` | Rule layer only (no pinned scenario values). |
| `analyze(payload) -> {"status", "data"}` | Contract adapter for `docs/module_api_contract.md` section A. |
| `IntentModuleAdapter().analyze(session_id, user_text)` | Async adapter for E's `IntentModule` protocol. |
| `score_intent(text)` / `detect_risk(text, intent)` / `extract_entities(text)` | Testable building blocks. |
| `TrainedIntentClassifier.load(path).classify(text)` | Opt-in Phase-two entry point with the same result shape. |

`docs/module_api_contract.md` remains the authority for the payload shape;
`src/banking_agent/schemas/state.py` remains the authority for field names.

### E integration

E injects the async adapter into `ModuleBundle` and calls:

```python
adapter = IntentModuleAdapter()
result = await adapter.analyze(session_id, user_text)
```

The returned mapping validates as `IntentResult` (`ModuleResult[UnderstandingResult]`).
`session_id` is accepted for protocol compatibility and deliberately ignored:
A neither reads nor writes conversation state. To use the trained classifier,
inject it without changing E's call site:

```python
adapter = IntentModuleAdapter(
    classifier=TrainedIntentClassifier.load(path).classify
)
```

### Phase-one behaviour

`mock.py` contains two layers on purpose:

1. `SCENARIO_EXAMPLES` pins the exact `intent` / `confidence` / `risk_level`
   agreed for S01-S08 in `docs/scenario_table.md`. Phase one is a mock
   integration phase, so those values are the contract rather than a model
   result.
2. Weighted keyword rules generalise to arbitrary text and already reproduce
   the intent and risk of all eight scenario examples.

`status` is `ok` for every successful analysis. The `UNKNOWN` intent is
returned with a low confidence (0.31, matching S07) so that C can apply its
low-confidence rule. `empty` is reserved for "no usable result"; `error` is
reserved for technical failures such as a missing `user_text`.

## Risk signals

BANKING77 carries no risk labels, so risk is an explicit, auditable rule layer
rather than a learned output. The reported level is the **more severe** of:

- a high-risk phrase (`without my permission`, `unauthorised`, `scam`, `fraud`,
  `stolen`, `hacked`, `suspicious`, `not me`, `someone used`, `otp`, ...);
- a medium-risk phrase (`charged twice`, `overcharged`, `wrong amount`,
  `dispute`, `refund`, `declined`, `failed`, `pending`, ...);
- the intent baseline (high for fraud/unauthorised, medium for fee complaints,
  low for the remaining routes).

Two invariants follow from the scenario table and must not be weakened:

- a high-risk phrase is never downgraded by low intent confidence;
- `RiskLevel.UNKNOWN` means "risk could not be assessed" and is not
  `RiskLevel.LOW`. S07 returns `UNKNOWN` risk on purpose.

## Entity types

`Entity.type` is a free string in the schema, so the module freezes a
controlled vocabulary in `taxonomy.py`; downstream code may rely on these nine
values only:

`payment_method`, `amount`, `currency`, `date`, `relative_time`,
`account_type`, `product`, `channel`, `transaction_reference`.

Extraction is gazetteer plus regular expressions (no model, no network).
Gazetteer phrases are matched longest-first so `credit card` is not also
reported as `card`. Gazetted matches carry confidence 0.90 and pattern matches
0.85. Sensitive types (amount, date, account references) are deliberately
conservative, because E confirms those with the customer before acting.
Month names are extracted only with a day, a year, or a date preposition, so
the modal "may" and the verb "march" are not reported as dates.

A fine-grained mistake does not automatically change the safety outcome: the
route-level view above shows errors such as `card_payment_not_recognised` being
predicted as `compromised_card`, which still lands on a high-risk escalation
route.

> **Needs E/C sign-off:** the nine entity types are new shared vocabulary. They
> should be added to `docs/module_api_contract.md` section A by the
> integration owner before other modules depend on them.

## BANKING77

`banking77.py` holds the fine-grained label space (77 intents, published order)
and the mapping to operational routes. The mapping is intentionally coarse: it
is a routing bridge, not the evaluation task. Macro-F1 is measured on the 77
classes; the mapping only decides which route a predicted label feeds.

Three fine-grained groups are routed to risk paths (`compromised_card`,
`lost_or_stolen_card`, `lost_or_stolen_phone` -> `fraud_suspicion`;
`*_not_recognised` -> `unauthorized_transaction`); fee and charge queries map to
`card_fee_enquiry` / `fee_complaint`; the remaining long tail defaults to
`policy_enquiry`. **BANKING77 has no fraud, complaint, or recommendation
intent**, so `fraud_suspicion`, `fee_complaint`, and `product_recommendation`
are reached through rules and scenario text, not through the dataset.

Run `python scripts/validate_intent_mapping.py --check` to prove the mapping is
complete before training or reporting.

### Relationship to B's label registry

B owns `src/banking_agent/modules/rag/banking77_mapping.json`, which maps the
same 77 labels to 13 knowledge-base categories plus related intents. It is a
retrieval registry, not an operational-route map: its `Category` values
(`card_lifecycle`, `bank_transfers`, ...) are not intents A emits. Keep the two
files separate. The label space is shared, so the validation script also fails
when B's registry and `BANKING77_LABELS` drift apart.

## Macro-F1 experiment

`scripts/train_intent_baseline.py` runs the BANKING77 baseline ladder over the
gitignored CSVs in `data/raw/banking77/`, and writes
`data/processed/intent_baseline_metrics.json` together with the generated
report `docs/results_intent_baseline.md`.

Protocol: a stratified 12% holdout of the train split is the dev set used to
select the model and its hyper-parameters; the test split is scored once, after
refitting on the full train split.

| rung | dev Macro-F1 | test Macro-F1 |
| --- | --- | --- |
| majority class | 0.0005 | 0.0003 |
| TF-IDF + ComplementNB | 0.8014 | 0.7934 |
| TF-IDF + LogisticRegression | 0.8584 | 0.8726 |
| TF-IDF + LinearSVC (`C=1.0`) | 0.8891 | 0.8940 |
| TF-IDF + sigmoid-calibrated LinearSVC (`C=5.0`) | 0.8895 | 0.8903 |
| frozen `all-MiniLM-L6-v2` + LogisticRegression | 0.9213 | **0.9307** |

Mapped to the operational routes, the selected encoder reaches Macro-F1
**0.9604** and accuracy 0.9838 over the five routes present in the BANKING77 test
gold. Fine-tuning a transformer is the next rung; it is not part of this run.

Setup and reproduction:

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install scikit-learn pydantic sentence-transformers
# place the two CSVs in data/raw/banking77/ (see below)
.venv/Scripts/python.exe scripts/train_intent_baseline.py            # TF-IDF ladder, ~20s
.venv/Scripts/python.exe scripts/train_intent_baseline.py --encoder  # adds the encoder rung
```

`--save-model` serialises the dev-selected pipeline. When the encoder rung wins
it is not a joblib pipeline, so the script saves the best pipeline rung instead
and says so; the recorded run writes
`models/intent_tfidf_linear_svc_calibrated.joblib`, whose sigmoid calibration
provides `predict_proba` for the confidence field. `models/` is gitignored.

The raw CSVs come from the BANKING77 release and are not committed
(`data/raw/` is gitignored):

```
https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/train.csv
https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv
```

## Trained path: confidence and abstention

`TrainedIntentClassifier` maps the fine-grained label through
`operational_intent_for` and reports the **route probability mass** — the summed
probability of every label that maps to the chosen route — rather than the
77-way arg-max probability. On BANKING77 the arg-max probability is frequently
below 0.4 even when the route is correct (a native multinomial
`LogisticRegression` behaves the same way), which would make C clarify nearly
everything. The route mass is usable: 0.92 for a clear fraud utterance and
0.50-0.69 for fee questions on the saved calibrated model.

Two behaviours are deliberate and need C's agreement:

- the trained path never abstains: it always returns a route, so low confidence
  has to be handled by C's threshold rule. `UNKNOWN` is a mock-only output;
- the risk layer is independent of the intent layer. "I think this transfer may
  be a scam." is routed to a weak `policy_enquiry` by the model but still
  reports `HIGH` risk from the phrase rule, so C escalates instead of answering.

## Tests

`tests/unit/test_intent_module.py` covers the pinned scenario values, rule
generalisation, risk precedence, entity extraction, the contract envelope, and
full BANKING77 mapping coverage. Run from the repository root:

```
python -m unittest tests.unit.test_intent_module tests.unit.test_state_schema
```

## Known limitations

- The rule layer is a Phase-one stand-in; Phase two swaps `score_intent` for a
  trained classifier behind the same `classify()` signature.
- `TrainedIntentClassifier` is opt-in and not wired into `classify()`: the
  default stays deterministic. Choosing a runtime dependency (scikit-learn, or
  torch for the encoder rung) is a team decision.
- The encoder rung is not serialised; loading it would need torch at runtime.
- Confidence from the rule layer is a heuristic score, not a calibrated
  probability.
- Intents outside the six operational routes plus `UNKNOWN` are not emitted; a
  BANKING77 label with no stronger route becomes `policy_enquiry`.
