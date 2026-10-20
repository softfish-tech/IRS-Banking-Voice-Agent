# Documentation

Project contracts, scenarios, module ownership, and architecture materials live here.

| Resource | Purpose |
| --- | --- |
| `module_ownership.md` | Team roles and module boundaries. |
| `module_api_contract.md` | Structured contracts between E and A/B/C/D. |
| `scenario_table.md` | Shared business-acceptance scenarios and future E2E fixture mapping. |
| `architecture/local_application_flow.mmd` | Editable local account, conversation, and agent-integration flow. |
| `engineering_conventions.md` | Team workflow, configuration, logging, testing, and completion standards. |
| `intent_module.md` | Part A module: interface, risk rules, entity types, BANKING77 mapping. |
| `results_intent_baseline.md` | Generated BANKING77 Macro-F1 results for intent classification. |
| `part_a_deliverables.md` | Part A completion report: scope, deliverables, results, tests, and limitations. |
| `architecture/system_architecture_draft.png` | Current integration architecture draft. |
| `../src/banking_agent/schemas/state.py` | Canonical executable `AgentState` schema. |

`state.py` is the source of truth for State fields and enums. Documentation examples must follow it rather than create a parallel schema.
