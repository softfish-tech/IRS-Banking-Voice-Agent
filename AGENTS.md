# Development Guide

For team-wide collaboration, testing, configuration, and trace requirements, see `docs/engineering_conventions.md`.

## Authoritative project references

Before implementing or changing a module, read the relevant project references:

- `docs/module_ownership.md` defines ownership and responsibility boundaries.
- `docs/module_api_contract.md` defines module inputs, outputs, failure behavior, and E/C integration rules.
- `docs/scenario_table.md` defines required business behavior, safety constraints, and E2E acceptance scenarios.
- `src/banking_agent/schemas/state.py` and `src/banking_agent/schemas/enums.py` are the canonical executable State and enum definitions.
- `docs/engineering_conventions.md` defines Git, testing, configuration, decision-trace, and completion rules.

When these sources overlap, the executable schema and enums take precedence for field names and allowed values, followed by the API contract and Scenario Table. Do not duplicate their detailed contents in this file.

## Repository rules

- Use the existing checkout; do not create Git worktrees.
- Keep application code under `src/banking_agent/`.
- Keep shared state and interface contracts in `src/banking_agent/schemas/`; `state.py` is the canonical AgentState definition.
- Do not commit secrets, `.env` files, raw sensitive data, model binaries, or generated caches.

## Module boundaries

- `app/orchestrator/` owns module sequencing and final-response assembly.
- High-risk routing and recommendation permission must go through `modules/rules/`.
- Use `ABSTAIN` when a question is understood but lacks reliable evidence; use `CLARIFY` only when user intent or required information is unclear.
- Modules must use public contracts and must not import another module's internals.
- `modules/voice/` is an extension point and is outside the phase-one text mock path.

## Changes and tests

- Put tests in `tests/unit/`, `tests/integration/`, or `tests/e2e/`.
- Before changing shared schemas or orchestration, update the relevant contracts and scenario documentation.
- Do not introduce shared fields, enum values, module outputs, or cross-module dependencies without updating the canonical schema and all affected contracts, scenarios, and tests.
- Preserve module ownership and coordinate cross-module contract changes with the integration owner.
