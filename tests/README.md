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

The E2E suite executes all eight S01–S08 fixtures as subtests and checks decisions,
state patches, module call order, citations and recommendations. It uses scripted
module outputs, not real models. Integration tests cover technical failures,
invalid rule patches, missing evidence, D denial and previous-turn output isolation.
No external service or API key is required. Trace and API tests will follow when
those components are implemented.
