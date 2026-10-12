# Engineering Conventions

## 1. Purpose and scope

This document defines repository collaboration practices. It complements, but does not replace, the module ownership, API contract, scenario, and executable schema documents.

Phase one is a text-first mock integration workflow using synthetic data. The project must not connect to real banking systems, process real customer records, or make binding financial decisions.

These conventions are framework-neutral. API/UI frameworks, deployment platforms, CI tools, and model providers can be selected later without changing the rules below.

## 2. Git workflow

### Branches

`main` is the stable integration branch. Do not develop or push directly to it. Make focused changes on a branch and merge through a pull request.

| Pattern | Use |
| --- | --- |
| `feature/a-<topic>` | A's intent, risk, or entity work. |
| `feature/b-<topic>` | B's RAG or knowledge-base work. |
| `feature/c-<topic>` | C's rules or state-machine work. |
| `feature/d-<topic>` | D's recommendation or synthetic-data work. |
| `integration/e-<topic>` | E's schema, orchestration, API, UI, voice, or E2E work. |
| `docs/<topic>` | Documentation-only changes. |
| `fix/<topic>` | Focused bug fixes. |
| `chore/<topic>` | Tooling, maintenance, or repository housekeeping. |

### Commits and pull requests

Use concise, imperative commit messages with a category prefix, for example `feat: add rule-engine mock`, `test: add fraud escalation scenario`, or `fix: block recommendation for open complaint`.

Every pull request should state its purpose, affected modules/contracts, validation performed, shared-schema or scenario changes, and any remaining limitation or follow-up work.

### Continuous integration

GitHub Actions runs `.github/workflows/verify.yml` on every push and pull
request. The workflow uses Python 3.11 and runs unit, integration (including
adapter-contract), and E2E tests without secrets or external banking services.
Changes to test commands must keep this workflow and `tests/README.md` aligned.

## 3. Module boundaries and shared contracts

Modules follow the ownership boundaries in `module_ownership.md`. A, B, C, and D must not import another domain module's internal implementation. Cross-module data uses the public models in `src/banking_agent/schemas/` and the contracts in `module_api_contract.md`.

`state.py` and `enums.py` are the canonical executable definitions for shared State and enum values. Documentation, mocks, and tests must use the same names and values.

E owns module invocation, controlled State integration, API/UI/voice delivery, logging, and end-to-end validation. C owns action semantics, reason codes, complaint-state rules, escalation conditions, and the recommendation permission gate. D owns product-level eligibility filtering and ranking after C has permitted the recommendation flow.

Any shared schema, enum, or contract change must include compatible test updates, a review of `scenario_table.md`, API-contract updates when I/O changes, and E coordination for cross-module compatibility.

## 4. Configuration, secrets, and data

Do not commit secrets, credentials, tokens, real `.env` files, private URLs, or local machine configuration. Environment-variable names and safe example values may be committed in `.env.example` or `configs/examples/`; secret values must never be included.

| Location | Allowed contents |
| --- | --- |
| `configs/` | Versioned, non-secret configuration and safe examples. |
| `data/raw/` | Local source data; ignored by Git except for its placeholder. |
| `data/processed/` | Regenerable outputs; ignored by Git except for its placeholder. |
| `data/fixtures/`, `tests/fixtures/` | Small, synthetic, versioned test fixtures. |
| `models/`, `artifacts/`, caches | Local generated files; do not commit unless explicitly agreed. |

Only synthetic, public, or explicitly licensed data may be committed. Do not commit real customer records, account information, transaction records, raw voice recordings, or personally identifiable information.

## 5. Logging and decision traces

E maintains structured decision traces for debugging, demonstrations, and auditability. A trace should explain the system path without exposing sensitive content.

The minimum trace fields are `request_id`, `session_id`, `modules_called`, `intent`, `intent_confidence`, `risk_level`, `complaint_status`, `handoff_status`, `action`, `reason_code`, `retrieved_document_ids`, and `recommendation_count`.

Do not log secrets, authentication data, full raw voice recordings, or real personal data. Avoid logging full user transcripts by default; synthetic test fixtures may use their defined text inputs. Logs support audit and debugging but do not replace authoritative `AgentState` or a future persistence layer.

## 6. Testing responsibilities

Tests are layered. Passing end-to-end tests does not replace module quality evaluation, and a strong module metric does not prove that the integrated workflow is safe.

| Test type | Primary owner | Scope |
| --- | --- | --- |
| A unit and evaluation tests | A | Intent, risk, entities, and BANKING77 evaluation such as Macro-F1. |
| B unit and evaluation tests | B | Retrieval, source metadata, and Recall@5. |
| C rules and state-machine tests | C | Action, reason code, rule precedence, complaint transitions, and escalation. |
| D unit and evaluation tests | D | Synthetic-data handling, product filtering, ranking, and recommendation violations. |
| Contract and integration tests | E, with module owners | Schema compatibility, module replacement, and integration behavior. |
| End-to-end tests | E, with C support | Scenario-driven text workflow from user input to final response. |

Use `tests/unit/` for isolated module and schema tests, `tests/integration/` for contract and multi-module tests, `tests/e2e/` for Scenario Table-driven workflow tests, and `tests/fixtures/` for small synthetic inputs and expected outputs.

Behavior changes require corresponding tests. Changes to business actions, state transitions, or safety behavior must update the relevant Scenario Table entry and the C/E tests that enforce it.

## 7. Documentation and architecture updates

Documentation is part of the integration contract.

| Change | Required updates |
| --- | --- |
| Shared State or enum | Schema code, affected tests, API contract, and relevant scenarios. |
| Module input or output | API contract and module tests. |
| Business action or state-machine rule | Scenario Table, C rule documentation, and tests. |
| System call boundary or new integration | Architecture diagram and API contract. |
| Development workflow rule | This document and, where relevant, `AGENTS.md`. |

Architecture diagrams must retain an editable source file, such as `.drawio`, alongside any PNG preview. The source file is authoritative; exported images are for viewing and review.

## 8. Definition of done

A change is ready for pull-request review when all applicable conditions are met:

- it has a focused purpose and respects module boundaries;
- relevant tests have passed, or an explicit reason for missing coverage is documented;
- it contains no secret, real customer data, generated cache, or unintended large artifact;
- shared schema and contract changes are compatible with dependent modules;
- Scenario Table and E2E expectations are updated when business behavior changes; and
- the pull request records validation results and any remaining limitation.

## 9. Deferred decisions

This document does not yet prescribe a Web/API framework, deployment platform,
formatter/linter, model provider, or mandatory reviewer count. GitHub Actions is
the selected CI provider for the current Python verification workflow. The team
should add remaining decisions when selected without weakening the boundaries and
safety rules above.
