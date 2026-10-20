# E integration implementation plan — local working document

> Status: local planning document only. Do not stage, commit, or push this
> file. It is not an authoritative contract. Canonical shared definitions remain
> `src/banking_agent/schemas/`, `docs/module_api_contract.md`,
> `docs/scenario_table.md`, and `docs/engineering_conventions.md`.

## 1. Purpose and current boundary

E owns system integration: module composition, controlled `AgentState` merges,
public API/UI delivery, persistence, observability, and end-to-end validation.
E does not replace A's understanding algorithms, B's retrieval logic, C's
business decisions, or D's product eligibility/ranking logic.

Current capabilities:

- E orchestration, fixture API, SQLite persistence, response rendering, DTOs,
  versioned conversation writes, and sanitized decision traces exist.
- B has a synchronous public retriever plus E's async bridge. The real B dev
  evaluation is reproducible in `irs` after loading the verified PyTorch model
  weights: Recall@5 95.07%, Hit@5 95.77%, MRR@5 85.31%, and zero technical
  errors on the 76-item development set.
- D exposes an async adapter and synthetic profile binding. Its current
  assurance is scenario, safety, and ordering verification rather than a
  model-quality metric.
- Real A and C implementations are not available. Scripted A/C adapters can
  validate E orchestration, but cannot validate actual intent/risk quality or
  business safety policy.

## 2. Delivery strategy

Do not wait idly for A/C. Divide work into two tracks.

| Track | Can proceed now | Requires real A/C |
| --- | --- | --- |
| Evaluation | E2E fixture schema, scenario expansion, runner, reports | actual quality and policy acceptance |
| Module integration | real B/D replacement runs below scripted A/C | production `ModuleBundle` |
| LLM | provider gateway, mock, secret/config/error handling | A/C prompts and decision behavior |
| Voice | ASR adapter, transcription dataset, transcript metrics | audio-to-action acceptance |
| Application | UI, API, DB, trace, migrations, rate limits | production decision rollout |

The delivery order is:

1. Freeze E2E evaluation data and reporting.
2. Retain B/D real-module replacement checks.
3. Build LLM provider infrastructure without owning decisions.
4. Build ASR as a transcript-first vertical slice.
5. Improve application quality in parallel.
6. Integrate real A/C and run frozen text, then voice, acceptance.

## 3. Phase 1 — E2E evaluation data and runner

### Goal

Create a test suite that answers: given a user request and persisted business
state, did the system take the permitted module path and end with the correct
safe action? It must assess behavior rather than exact natural-language wording.

### Dataset layout and record

Create a versioned local fixture layout:

```text
tests/fixtures/evaluation/e2e/v1/
├── manifest.json
├── scenario_blueprints.json
├── dev.jsonl
├── test.jsonl
└── review_log.md
```

The first published version remains synthetic-only. Each JSONL case records:

```json
{
  "case_id": "E2E-S03-004",
  "split": "test",
  "user_text": "That card purchase was not mine.",
  "initial_state": {
    "complaint_status": "NONE",
    "handoff_status": "NOT_REQUIRED",
    "consent": "UNKNOWN"
  },
  "expected": {
    "action": "ESCALATE",
    "modules_called": ["A", "C"],
    "complaint_status": "OPEN",
    "handoff_status": "ESCALATED",
    "citation_count": 0,
    "recommendation_count": 0
  }
}
```

For fixture-driven runs, a case can also point to expected A/C/B/D envelopes.
The runner uses those envelopes only through public adapter protocols; it must
not implement action policy itself.

### Coverage

Start with S01–S11, then add a high-risk/low-confidence precedence case. Each
family needs normal, paraphrased, incomplete, and stateful variants.

| Family | Required behavior |
| --- | --- |
| Grounded policy answer | `A → C → B → C`; citation only after final `ANSWER` |
| Complaint | C patches complaint state; no D call |
| Fraud/unauthorized transaction | high risk wins; `ESCALATE`; no B/D call |
| Unclear request | `CLARIFY`; no unsupported assumption |
| Missing evidence | B can return empty; final C action is `ABSTAIN` |
| Recommendation blocked | unresolved complaint or no consent; D not called |
| Recommendation permitted | C `RECOMMEND` before D; valid ranked output only |
| Multi-turn state | previous complaint/handoff/consent state influences next turn |
| Technical failure | no technical error becomes a business success |

### Data creation process

Do not write every sentence manually and do not adopt public datasets as policy
truth.

1. Manually author scenario blueprints from the Scenario Table and NovaBank
   synthetic policies. These define gold business behavior.
2. Write two or three reviewed seed utterances per blueprint.
3. Generate paraphrases with templates, public intent wording, or an LLM.
4. Human-review each candidate for intended meaning, safety label, and split.
5. Freeze test cases, hash them in `manifest.json`, and never tune against them.

Banking77 can provide English phrasing ideas for A's intent expressions. It is
not gold evidence for B, action policy for C, or ranking truth for D. NovaBank
policy/recommendation labels must be created and reviewed inside this project.

### Initial scope and split policy

- 12 scenario families;
- 3 reviewed seed utterances per family;
- 4–5 reviewed variants per seed or family as appropriate;
- approximately 80–100 single-turn cases;
- 15–20 multi-turn state sequences;
- dev/test split by paraphrase family, not random utterance splitting.

All paraphrases of the same seed and business fact remain in one split. This
prevents the system from seeing test wording during tuning.

### Metrics

The runner outputs machine-readable JSON plus a short Markdown summary.

| Area | Metric | Desired interpretation |
| --- | --- | --- |
| Workflow | scenario pass rate | expected end-to-end behavior completed |
| Module routing | call-order pass rate | E called only permitted modules |
| Safety | high-risk unsafe-route count | must be zero |
| Grounding | expected citation pass rate | answer contains only permitted evidence |
| Abstention | expected-ABSTAIN pass rate | unsupported information is not fabricated |
| Recommendation | unauthorized-D-call count | must be zero |
| Reliability | technical-failure pass rate | errors never become business success |
| State | transition pass rate | C patches are preserved without invention |

Do not score exact final prose. Test action, citations, recommendation presence,
public error shape, and state instead.

## 4. Phase 2 — real B/D integration below scripted A/C

Maintain replacement configurations:

```text
Scripted A + real B + scripted C + real D
Scripted A + real B + scripted C + D technical failure
Scripted A + B empty + scripted C + no D
```

These tests prove that E:

- invokes B only after C permits the answer route;
- sends B canonical retrieved documents to C's second decision;
- renders citations only when final C action is `ANSWER`;
- invokes D only after C returns `RECOMMEND`;
- resolves conversation ID to a validated synthetic D profile server-side;
- hides recommendations on denial/error;
- keeps state and public output safe on invalid envelopes, timeouts, and
  technical failures.

They do not prove that C rule semantics are correct.

### B operational rule

E can use an asynchronous bridge around B's public synchronous retriever. Build
the real backend once at application startup. B scores are ranking logits, not
answer-confidence probabilities. E must never turn B `ok` into `ANSWER`; C's
second decision is still required.

When reading B evaluation:

- Recall@K is the average fraction of all gold evidence recovered in top K;
- Hit@K is whether any gold evidence appears in top K;
- all-gold recall checks every required chunk for multi-evidence questions;
- MRR@K rewards earlier first correct evidence;
- technical errors must be zero before interpreting a metric.

No-evidence false-positive retrieval is not automatically an E failure; C must
reject topically similar but insufficient evidence.

## 5. Phase 3 — LLM provider gateway

### Scope

E supplies safe, injectable transport. E does not own domain prompts, intent/
risk semantics, rule decisions, or product recommendations.

Suggested structure:

```text
app/providers/
├── interfaces.py       # async LLMClient protocol
├── provider_x.py       # vendor transport adapter
├── mock.py             # deterministic CI client
├── settings.py         # non-secret configuration parsing
└── errors.py           # sanitized provider failure mapping
```

Suggested protocol:

```python
class LLMClient(Protocol):
    async def generate(self, request: LLMRequest) -> LLMResult: ...
```

### E-owned responsibilities

- server-only configuration and secret lookup;
- timeout, bounded retry, cancellation, concurrency and rate limits;
- provider-independent request IDs and sanitized error codes;
- mock provider with no external network use in CI;
- structured-output/Pydantic transport validation;
- telemetry excluding keys, full prompts, raw transcripts and sensitive data.

Secrets must not enter browser code, SQLite records, source control, or traces.

### Module ownership

| Responsibility | Owner |
| --- | --- |
| provider client/configuration/timeout/retry/logging | E |
| intent/entity/risk candidate interpretation | A |
| action/reason/state patch/recommendation permission | C |
| eligibility filtering and product ranking | D |
| evidence retrieval and provenance | B |
| controlled invocation/state merge/API/UI response | E |

E must never parse free-form LLM prose into `OPEN`, `ESCALATED`, `RECOMMEND`,
or other canonical business state. If C uses an LLM internally, C validates the
output and returns canonical `Decision`; E applies only `RuleStatePatch`.

Initially retain deterministic response templates. A later LLM renderer may run
only after C permits the action and may only use B-returned evidence.

## 6. Phase 4 — ASR vertical slice

### Initial architecture

Keep ASR separate from the text agent until text E2E is stable:

```text
audio upload/recording
  → input validation
  → async ASR adapter
  → transcript + confidence
  → user review/confirmation
  → existing text request path
```

An initial local contract can be:

```text
transcribe(audio, language) -> {status, text, confidence, duration_ms}
```

Do not add raw audio to `AgentState`. Keep transcript state transient until the
normal text request begins; do not persist raw recordings by default.

### Safety and operations

- limit MIME type, byte size, duration and request timeout;
- delete temporary audio files on success and failure;
- do not log raw audio, complete transcripts, credentials, account numbers or
  voiceprint-style data;
- use confirmation/clarification for low confidence;
- never infer financial facts not reliably transcribed.

### ASR data and metrics

Use public speech data only for generic recognition quality. Use internally
created synthetic banking utterances for bank-domain tests, derived from already
approved text cases and never from real customer recordings.

| Layer | Metric |
| --- | --- |
| General transcription | WER/CER |
| Banking terminology | amount/date/product/security-keyword preservation |
| User intent | transcript-to-intent agreement once A exists |
| Full workflow | audio-to-final-action agreement once A/C exist |

## 7. Phase 5 — API, frontend, persistence and observability

### Backend/API

- version public DTOs and keep internal State/reason codes hidden;
- validate payloads, enforce request limits and retain idempotency;
- retain atomic expected-version turn commits;
- add health/readiness checks without secret/provider details;
- make provider/ASR/module mode explicit feature flags;
- retain generic public technical errors and sanitized internal traces.

### Persistence

- retain synthetic-only user/profile data;
- migration-test every schema change;
- index conversation, message, trace and ownership lookup paths;
- define trace/audio retention before persistent voice features;
- prevent payloads from selecting or overriding a D profile key.

### Frontend

- display citations and recommendations as separate structured components;
- provide loading, retry and technical-error states with safe wording;
- label fixtures, policies, accounts and recommendations as synthetic/demo;
- add recording, upload failure and low-confidence transcript review states;
- never expose provider keys, internal traces, reason codes, document IDs or
  raw RAG scores.

## 8. Phase 6 — integrate once real A/C arrive

1. Run E's adapter-contract harness for each real adapter.
2. Inject all four real adapters through `ModuleBundle`.
3. Run frozen text E2E dev/test data without scripted A/C.
4. Measure A intent/risk and C rule coverage separately from aggregate E2E.
5. Verify C high-risk precedence, complaint lifecycle, evidence post-check and
   recommendation permission route.
6. Add ASR audio-to-action cases only after text behavior is accepted.
7. Enable a production-like non-fixture UI only after these checks pass.

## 9. Completion checklist

### Ready for real text integration

- [ ] E2E fixtures have manifest, dev/test split and review history.
- [ ] Real B/D replacement tests pass below scripted A/C.
- [ ] B real retrieval has zero technical errors in selected environment.
- [ ] LLM provider failures are sanitized and fail closed.
- [ ] API, trace, persistence and frontend do not expose sensitive data.

### Ready for real A/C integration

- [ ] A/C adapters satisfy public contracts.
- [ ] Frozen text E2E cases pass with non-scripted A/C.
- [ ] High-risk unsafe-route and unauthorized-D-call counts are zero.
- [ ] C patches are the only source of business-state transitions.
- [ ] B evidence reaches C's second decision and never independently permits an
      answer.

### Ready for voice acceptance

- [ ] ASR input limits and temporary-data deletion are tested.
- [ ] Synthetic audio evaluation has reference transcripts and review records.
- [ ] Critical banking terms meet an agreed preservation target.
- [ ] Audio and equivalent text cases produce the same safe C action.
- [ ] No raw audio or sensitive information is persisted by default.
