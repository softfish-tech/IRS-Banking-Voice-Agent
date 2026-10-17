# D recommendation handoff

This phase-one implementation filters and ranks explicitly synthetic products after C permits recommendation. It uses existing Pydantic models, standard-library tests and no external service.

## Public entry points

- Pure function: `recommend(request, *, customer_profiles, products)`.
- E adapter: `RecommendationAdapter(dataset)` with async `recommend(session_id, complaint_status, handoff_status, consent)`.
- Loader: `load_fixture(path)`, called once at application initialization.

```python
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture

fixture = load_fixture('data/fixtures/recommendation.json')
adapter = RecommendationAdapter(fixture)
# Call only after C returns RECOMMEND.
result = await adapter.recommend('session-001', 'RESOLVED', 'NOT_REQUIRED', 'GRANTED')
```

The adapter snapshots validated configuration and returns fresh result objects. Recommendation calls perform no file/network I/O. Shared AgentState/enums are unchanged; D imports no other domain module or E implementation.

## Data and ranking

The versioned fixture has 4 fictional customers and 3 fictional products. Age, residence and available deposit are eligibility filters. Amounts are nonnegative integer SGD cents; strings, floats, booleans and missing amounts are rejected. Product IDs must be unique. A corrupt catalog fails as a whole.

Rank eligible candidates by matching goal first, ascending demo_priority next, then product_id. Ranks start at 1 and are consecutive. An eligible alternative explicitly states when it does not match the requested goal.

The synthetic SG residence/minimum adult age agrees with B's basic account context. The three savings/emergency products and their product-specific minimum deposits/priorities are demonstration data. B's current corpus defines one personal account and does not authorize this product catalog. Do not use D's fixture as bank policy or claim an interest rate, return, account opening or actual transaction.

## Business and technical outcomes

| Case | Result |
| --- | --- |
| Eligible products | ok / allowed=true / ELIGIBLE_WITH_CONSENT |
| Valid catalog, no eligible products | ok / allowed=false / NO_ELIGIBLE_PRODUCT / items=[] |
| OPEN or UNDER_REVIEW complaint | ok / allowed=false / UNRESOLVED_COMPLAINT / items=[] |
| Consent UNKNOWN or DENIED | ok / allowed=false / CONSENT_REQUIRED / items=[] |
| Active handoff, invalid request/catalog or missing session profile | error |

Active handoff rejection takes priority. Complaint rejection precedes consent rejection. Defensive checks can only reject; they do not grant C permission. The request has no risk field or C-decision proof. Risk routing and initial recommendation permission remain C/E-owned. Consent cannot be patched by C under the canonical RuleStatePatch.

The pure function preserves `{"status":"error","data":{}}`. The async adapter returns `{"status":"error"}` because E's typed envelope rejects an empty RecommendationData object. Expected validation errors expose no raw profiles or exceptions. Loader failures, invalid adapter configuration and unexpected implementation exceptions propagate; E must use its safe technical-error path.

## Session association and E composition

The fixture keys session-001 through session-004 are explicit teaching associations. They are not identities or authentication. E's core S06 uses session-s06 and the local UI creates conversation UUIDs; neither automatically matches D's fixture.

For the E replacement test only, session-s06 is explicitly associated with the adult session-001 profile before constructing the adapter. Unknown runtime sessions still fail. E must agree a synthetic profile provider/session association and inject the adapter in its ModuleBundle. Do not map all unknown sessions to one customer.

After E's composition files are available, the intended composition is:

```python
from banking_agent.app.bootstrap import ModuleBundle, StaticModuleFactory

# a_adapter, b_adapter and c_adapter are supplied by their owners.
bundle = ModuleBundle(a_adapter, b_adapter, c_adapter, adapter)
factory = StaticModuleFactory(bundle)
```

This PR supplies D only. It does not switch E's default fixture mode or claim the browser uses real D. Production mode is E's existing factory name, not a claim of production-ready banking logic.

## Scenarios and tests

- Direct fixtures: S05 complaint defense, S06 ranked products, S09 consent defense, S10 no eligible product.
- Unit tests cover data validation, filtering boundaries, deterministic ordering, malformed input, fail-closed behavior, async interface and result/configuration isolation.
- Shared-state integration verifies canonical items, JSON round trip and preservation of C's decision.
- The explicit E replacement check runs S01-S08 with real D and scripted A/B/C; D is invoked only on S06. It also covers safe denial, no products, unknown profiles, controlled C patches and rejection of forged consent.

E's original S06 mock returns one product. Real D returns three demo candidates in a fixed order. The replacement test records this expected difference without editing E's original core.json.

## Reproduce

Use Python 3.11+ and the dependencies in pyproject.toml:

```powershell
python -m pip install -e .
python scripts/check_recommendation.py
python scripts/demo_recommendation.py --scenario S06
python scripts/demo_recommendation.py --scenario S10
# Requires E's implementation and public test helpers:
python scripts/check_recommendation.py --e-integration
```

The check discovers each populated test layer separately, rejects failures/skips, and compiles source without caches. If E is absent, normal checks report that limitation; explicitly requesting E verification fails instead of skipping it.

## Review before final integration

1. C confirms permission and defensive-denial reason-code usage.
2. E approves the async adapter and configures synthetic session/profile association.
3. B/C/E confirm the demonstration catalog or replace it with an agreed synthetic policy-backed catalog.
4. E integrates D at the composition root and updates real-module scenario fixtures; all original E tests continue to pass.

The local implementation and compatibility tests are complete. Team approval, browser composition with real modules, real C rules, real retrieval/model metrics and ASR/TTS remain separate work. See d_recommendation_validation.md for measured evidence.
