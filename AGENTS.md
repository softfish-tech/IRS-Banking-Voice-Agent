# Development Guide

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
- Preserve module ownership and coordinate cross-module contract changes with the integration owner.
