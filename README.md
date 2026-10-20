# IRS-Banking-Voice-Agent

## Overview

This repository contains a modular prototype for a safe banking service agent for a fictional Singapore retail bank. The intended workflow combines intent and risk understanding, evidence-grounded policy answers, complaint handling, responsible recommendations, and a future voice interface.

The prototype uses synthetic data only. It does not connect to real banking systems, process real customer records, execute transactions, or make binding financial decisions.

## Current phase

The project is currently in Phase 1: text-first integration design and mock readiness.

- The repository skeleton, module boundaries, shared State schema, API contract, scenario acceptance table, and engineering conventions are in place.
- The current architecture covers UI/API/voice integration, orchestration, A/B/C/D module boundaries, and safe routing.
- Part A publishes a frozen `all-MiniLM-L6-v2` + logistic-regression BANKING77 artifact (test Macro-F1 0.9307) behind the opt-in `EncoderIntentClassifier`; the default path remains deterministic rules.
- RAG infrastructure, rules implementation, recommendation logic, API/UI, and ASR/TTS are not yet implemented.

For a local, fixture-backed browser application with synthetic account
registration/login and persisted conversation history, run:

```bash
PYTHONPATH=src python -m banking_agent.app.api.server
```

Then open `http://127.0.0.1:8000`. Create a local-only account with a test
password of at least 6 characters. The SQLite database is stored under
`data/processed/` and is ignored by Git. The default fixture mode runs synthetic
S01--S08 fixtures through the real orchestrator; its scenario adapters are not
A/B/C/D production implementations. When E explicitly injects a complete
production `ModuleBundle`, the local UI switches to a 1--2,000-character
free-text synthetic-test surface. Do not enter real personal or banking data.

The developer trace page is disabled by default. For local diagnostics only,
start the server with an explicit registered developer username, then open
`http://127.0.0.1:8000/developer` after signing in as that account:

```bash
BANKING_AGENT_DEVELOPER_DASHBOARD=1 BANKING_AGENT_DEVELOPER_USERNAME=developer \
  PYTHONPATH="$PWD/src" python -m banking_agent.app.api.server
```

This local allow-list is not production authorization; a deployed system must
use real role-based access control.

The server defaults to `BANKING_AGENT_MODULE_MODE=fixture`. Its E-owned module
composition layer is intentionally separate from the API: future owner-provided
A/B/C/D adapters are injected as a `production` `ModuleBundle`, while fixtures
remain available for deterministic development and CI checks.

## Architecture

The current integration architecture is available at [docs/architecture/system_architecture_draft.png](docs/architecture/system_architecture_draft.png).

E owns application integration, API/UI/voice delivery, state integration, logging, and end-to-end testing. A, B, C, and D own their respective domain modules. See [module ownership](docs/module_ownership.md) for the full responsibility boundaries.

## Repository layout

```text
src/banking_agent/       application package
├── app/                 API and orchestration boundaries
├── modules/             intent, RAG, rules, recommendation, and voice modules
├── schemas/             canonical State and enum definitions
└── shared/              cross-cutting utilities

configs/                 non-secret configuration and examples
data/                    synthetic fixtures and local data locations
docs/                    architecture, contracts, scenarios, and conventions
tests/                   unit, integration, E2E, and fixture locations
scripts/                 repeatable development and validation scripts
```

## Project documentation

- [Module ownership and boundaries](docs/module_ownership.md)
- [Module API contract](docs/module_api_contract.md)
- [Scenario Table](docs/scenario_table.md)
- [Engineering conventions](docs/engineering_conventions.md)
- [Canonical AgentState](src/banking_agent/schemas/state.py)
- [Intent model artifact](src/banking_agent/modules/intent/model_artifacts/README.md)
- [Development guide for coding agents](AGENTS.md)

The executable State and enum definitions in `src/banking_agent/schemas/` are the source of truth for shared field names and allowed values.

## Development workflow

Develop on focused `feature/`, `integration/`, `docs/`, `fix/`, or `chore/` branches and merge changes into `main` through pull requests. Module behavior, shared contracts, scenario acceptance, testing responsibilities, data handling, and decision-trace requirements are defined in [Engineering Conventions](docs/engineering_conventions.md).

GitHub Actions runs unit, integration (including adapter contract), and E2E
scenario tests on every push and pull request. The workflow uses Python 3.11,
contains no secrets, and does not call external banking services.

## Roadmap

1. A/B/C/D provide deterministic module mocks that follow the shared contract.
2. E implements the Orchestrator and the text mock end-to-end workflow.
3. The team adds module-specific evaluation, integration tests, and scenario-driven E2E tests.
4. Later phases add API/UI delivery and ASR/TTS voice adapters without changing the core module boundaries.
