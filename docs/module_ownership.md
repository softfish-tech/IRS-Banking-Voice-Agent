# Module Ownership and Boundaries

This document defines ownership for the modular banking-agent prototype. It is the team-level source of truth for responsibilities; executable shared contracts will be added separately.

| Owner | Primary area | Responsibility | Boundary |
| --- | --- | --- | --- |
| A | `modules/intent/` | Intent classification, risk signals, and entity extraction | Does not make business actions or final responses. |
| B | `modules/rag/` | Retrieve policy evidence and source metadata | Does not decide whether an answer is permitted. |
| C | `modules/rules/` | Complaint state machine, deterministic safety rules, and action decisions | Does not generate natural-language responses. |
| D | `modules/recommendation/` | Filter and rank recommendations after permission is granted | Does not bypass consent, eligibility, risk, or complaint rules. |
| E | `app/orchestrator/`, `schemas/` | Integration, orchestration, shared contracts, text E2E tests, and observability | Does not replace owners' domain algorithms. |

## Shared rules

- The orchestrator coordinates modules and assembles the final response.
- Any high-risk route or recommendation permission must be decided by the Rules module.
- Shared state and interface changes require integration-owner coordination and corresponding scenario/test updates.
- Voice/ASR/TTS is a later extension. Phase one validates a text-only mock end-to-end path.
