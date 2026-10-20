# Local development plan — E integration

> Local working plan only. Do not stage, commit, or treat this document as an
> authoritative module contract. The canonical shared contracts remain
> `docs/module_api_contract.md`, `docs/scenario_table.md`, and
> `src/banking_agent/schemas/`.

## Current position

- E orchestration, persistence, API, observability, fixture workflow, B async
  bridge, and D profile-binding integration are available.
- B's BM25 evaluation can run locally. The recorded optimized BM25 plus
  Cross-Encoder dev result must be reproduced only in an environment with a
  compatible scientific-Python stack and the fixed model revision cached.
- D is a deterministic synthetic eligibility-and-ranking component. Its current
  assurance is scenario, safety, and ordering verification rather than a
  model-quality metric.
- Real A and C implementations are not yet available. Therefore, no full
  production Agent flow or final safety claim can be made.

## Working principle

Do not block all E work on A and C. Split delivery into two tracks:

1. Work that uses scripted A/C adapters and is independently useful now.
2. Work that must wait for real A/C before it can be called production-ready.

Scripted A/C validate orchestration only; they do not validate intent quality,
risk routing, complaint policy, or recommendation permission.

## Plan while A and C are unavailable

### 1. Freeze a text E2E evaluation harness

Extend S01–S11 into versioned development and frozen test fixtures. Each case
should contain:

- user text and initial `AgentState` business fields;
- expected A envelope, first C decision, B envelope where applicable, and
  second C decision where applicable;
- expected D invocation/result where applicable;
- final action, safe citations, recommendation count, and state transition;
- expected module-call order and failure behavior.

Use `ScriptedModules` while A/C are absent. When their adapters arrive, replace
only the scripted implementation and run the same frozen cases. Keep dev and
test data distinct, hash the frozen files, and never tune against test.

Metrics to publish from this harness:

| Area | Metric |
| --- | --- |
| Workflow | scenario pass rate and module-call-order pass rate |
| Safety | high-risk unsafe-route count (must be zero) |
| Grounding | citation/evidence contract pass rate |
| Abstention | unsupported-answer rate and expected-ABSTAIN pass rate |
| Recommendation | unauthorized-D-call count (must be zero) |

Public data can help with wording, but not replace project labels:

- Banking77 is suitable as an English intent-expression reference for A, not as
  NovaBank policy evidence or recommendation ground truth.
- Bank policy, complaint lifecycle, high-risk, and recommendation labels must
  remain synthetic and project-reviewed.

### 2. Exercise real B and D beneath scripted A/C

Maintain replacement integration cases such as:

```text
Scripted A + real B + scripted C + real D
```

This validates that E passes B evidence to C's second decision, calls D only
after a scripted C `RECOMMEND`, preserves canonical State, produces safe public
responses, and fails closed on module errors. It does not validate A/C domain
correctness.

### 3. Prepare a provider gateway, not an E-owned decision engine

Create an E-owned injectable asynchronous `LLMClient` protocol and provider
adapters. It should cover server-side configuration, timeouts, bounded retries,
rate limiting, response-schema validation, mock clients, sanitized technical
errors, and non-sensitive telemetry.

Secrets must be supplied by the server environment or a future secret manager.
They must not enter browser code, SQLite records, source control, or decision
traces.

Provider composition is E's responsibility. Prompts and domain interpretation
remain A/C responsibilities:

| Concern | Owner |
| --- | --- |
| provider client, configuration, timeout, retry, logging | E |
| intent/entity/risk interpretation | A |
| action, reason code, complaint/handoff patch, recommendation permission | C |
| product eligibility and rank | D |
| module invocation, envelope validation, state merge, API response | E |

E must never parse free-form LLM prose into `OPEN`, `ESCALATED`, `RECOMMEND`,
or any other business state. C may use a model internally in the future, but
must validate and return the existing canonical `Decision`. E only applies its
whitelisted `RuleStatePatch`.

Keep the current deterministic response renderer initially. Any future LLM
answer renderer must run only after C permits the action and must use only B's
returned evidence.

### 4. Build ASR as a separate vertical slice

Keep voice outside the text workflow until text integration is stable:

```text
audio -> ASR adapter -> transcript + confidence -> UI confirmation
```

Define an async voice contract such as:

```text
transcribe(audio, language) -> {status, text, confidence, duration_ms}
```

The initial ASR adapter should enforce upload format, duration, size, timeout,
and temporary-file deletion limits. Do not persist raw recordings by default.
Low-confidence transcription must lead to confirmation/clarification, not a
guessed bank instruction.

Use public speech data only for general ASR quality and self-created synthetic
banking utterances for domain evaluation. A practical evaluation suite includes:

- WER/CER on general speech;
- critical-token preservation for amounts, dates, product names and security
  terms;
- intent preservation after transcription;
- after A/C exist, audio-to-final-action agreement with the equivalent text
  case.

Never add real customer recordings, account data, card numbers, credentials, or
voiceprints to the repository.

### 5. Continue application quality work

These improvements do not require A/C:

- API versioning, DTO validation, consistent public errors, request limits, and
  idempotency;
- conversation versioning, database migration tests, indexes, and atomic turn
  commits;
- sanitized traces, health checks, and feature flags;
- frontend states for citations, recommendations, technical errors, retry,
  loading, recording, and explicit synthetic-data notices;
- test isolation and CI commands that never require provider credentials or
  external banking services.

## Work that waits for A and C

- Compose the actual production `ModuleBundle`.
- Measure real A intent/risk quality.
- Validate C's safety precedence, complaint lifecycle, and recommendation gate.
- Run genuine text-to-action and voice-to-action E2E acceptance.
- Enable any production-like UI mode backed by non-fixture A/C decisions.

## Recommended delivery order

1. Build and freeze E2E fixtures plus evaluation reporting.
2. Stabilize the B real-model evaluation environment and retain the B/D
   replacement integration checks.
3. Implement the provider gateway and its mock/secret/error handling.
4. Implement the ASR adapter and transcript-level evaluation.
5. Improve frontend, API, persistence, and observability in parallel.
6. Once A/C arrive, inject them, run frozen text E2E, then add audio-to-action
   acceptance before claiming a complete voice agent.

## Definition of readiness for real A/C integration

- Adapter contracts for A/C pass with real owner-provided adapters.
- Frozen E2E cases run without fixture A/C replacements.
- High-risk and recommendation-gate safety checks have no unsafe route.
- B evidence and D output continue to use their public interfaces only.
- Provider and ASR failures fail closed and disclose no sensitive information.
- All unit, integration, and E2E tests pass without secrets or external banking
  systems.
