# IRS-Banking-Voice-Agent

## Overview

This repository contains a modular prototype for a safe banking service agent for a fictional Singapore retail bank. The intended workflow combines intent and risk understanding, evidence-grounded policy answers, complaint handling, responsible recommendations, and a future voice interface.

The prototype uses synthetic data only. It does not connect to real banking systems, process real customer records, execute transactions, or make binding financial decisions.

## Current phase

The project is currently in Phase 1: text-first integration design and mock readiness.

- The repository skeleton, module boundaries, shared State schema, API contract, scenario acceptance table, and engineering conventions are in place.
- The current architecture covers UI/API/voice integration, orchestration, A/B/C/D module boundaries, and safe routing.
- Production intent models, RAG infrastructure, rules implementation, recommendation logic, API/UI, and ASR/TTS are not yet implemented.

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
- [Development guide for coding agents](AGENTS.md)

The executable State and enum definitions in `src/banking_agent/schemas/` are the source of truth for shared field names and allowed values.

## Development workflow

Develop on focused `feature/`, `integration/`, `docs/`, `fix/`, or `chore/` branches and merge changes into `main` through pull requests. Module behavior, shared contracts, scenario acceptance, testing responsibilities, data handling, and decision-trace requirements are defined in [Engineering Conventions](docs/engineering_conventions.md).

## Roadmap

1. A/B/C/D provide deterministic module mocks that follow the shared contract.
2. E implements the Orchestrator and the text mock end-to-end workflow.
3. The team adds module-specific evaluation, integration tests, and scenario-driven E2E tests.
4. Later phases add API/UI delivery and ASR/TTS voice adapters without changing the core module boundaries.
