# Tests

- `unit/`: isolated module behavior.
- `integration/`: interactions across modules.
- `e2e/`: scenario-driven text workflow checks.
- `fixtures/`: synthetic test data.

## Text-mock integration checks

From the repository root, with the prepared virtual environment:

```bash
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/unit -v
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/e2e -v
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/integration -v
```

The E2E suite executes the draft scenario fixtures as hybrid runs: A/C use
scripted owner envelopes until their implementations arrive, while B uses the
delivered BM25 backend with a deterministic test reranker and D uses the
delivered synthetic recommendation adapter. It checks decisions, state patches,
module call order, citations and recommendations. Integration tests cover technical failures,
invalid rule patches, missing evidence, D denial and previous-turn output isolation.
No external service or API key is required. They also include the reusable
`helpers/adapter_contracts.py` harness: A/B/C/D owners can call its async
`assert_*_adapter_contract` functions against their adapters before handing them
to E. The harness checks envelope shape and integration safety, not domain-model
quality or policy correctness.

In the prepared local `irs` environment, run the same E2E suite through B's
cached fixed Cross-Encoder instead of the deterministic reranker:

```bash
conda run -n irs env PYTHONPATH=src:tests BANKING_AGENT_E2E_RERANKER=cross_encoder \
  python -m unittest discover -s tests/e2e -v
```

The Cross-Encoder mode is local-files-only and will fail rather than download a
model if the fixed revision is not cached. CI intentionally keeps the
deterministic reranker mode.
