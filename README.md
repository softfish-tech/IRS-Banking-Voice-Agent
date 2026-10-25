# IRS-Banking-Voice-Agent

## Overview

This repository contains a modular prototype for a safe banking service agent for a fictional Singapore retail bank. The intended workflow combines intent and risk understanding, evidence-grounded policy answers, complaint handling, responsible recommendations, and a future voice interface.

The prototype uses synthetic data only. It does not connect to real banking systems, process real customer records, execute transactions, or make binding financial decisions.

## Final evaluation summary

The submission-level result and its scope/limitations are in
[`docs/unified_freeze_final_report_20261023.md`](docs/unified_freeze_final_report_20261023.md).
It is the single narrative entry point for the text-agent structured freeze,
independent final-response semantic overlay, and separate local ASR smoke
evaluation. Detailed fixture denominators and methods remain in
[`docs/evaluation_catalog.md`](docs/evaluation_catalog.md) and
[`docs/semantic_evaluation.md`](docs/semantic_evaluation.md).

## Current phase

The project is currently a local, synthetic-data integration prototype.

- The repository skeleton, module boundaries, shared State schema, API contract, scenario acceptance table, and engineering conventions are in place.
- The current architecture covers UI/API/voice integration, orchestration, A/B/C/D module boundaries, and safe routing.
- The browser application, real A/B/C/D composition, provider gateway, and
  local ASR input boundary are available.
- Part A publishes a frozen `all-MiniLM-L6-v2` + logistic-regression BANKING77 artifact (test Macro-F1 0.9307), used by the default local production composition.

For the default local production browser application with synthetic account
registration/login and persisted conversation history, run:

```bash
PYTHONPATH=src python -m banking_agent.app.api.server
```

When this local server starts, it automatically reads a repository-root `.env`
file if present. The file is Git-ignored; process environment variables take
precedence over it. This loader is for local development only and is not used
by tests or library imports.

Then open `http://127.0.0.1:8000`. Create a local-only account with a test
password of at least 6 characters and select one clearly-labelled synthetic
demo profile; it is fixed for that account and snapshotted on new conversations
for D recommendation tests. The SQLite database is stored under
`data/processed/` and is ignored by Git. The default mode composes the delivered
MiniLM A adapter, real local B BM25-plus-Cross-Encoder retriever, C `RuleEngine`,
and D synthetic recommendation adapter. The UI uses its 1--2,000-character
free-text synthetic-test surface. Do not enter real personal or banking data.
The real A encoder and B reranker are local-files-only; startup fails closed if
either pinned model is unavailable.

For deterministic fixture development, opt in explicitly before starting:

```bash
BANKING_AGENT_MODULE_MODE=fixture PYTHONPATH=src python -m banking_agent.app.api.server
```

The developer trace page is disabled by default. For local diagnostics only,
start the server with an explicit registered developer username, then open
`http://127.0.0.1:8000/developer` after signing in as that account:

```bash
BANKING_AGENT_DEVELOPER_DASHBOARD=1 BANKING_AGENT_DEVELOPER_USERNAME=developer \
  PYTHONPATH="$PWD/src" python -m banking_agent.app.api.server
```

This local allow-list is not production authorization; a deployed system must
use real role-based access control.

## E2E integration data and checks

E owns the frozen, versioned text E2E fixtures and their runner. The current
hybrid suite contains 42 single-turn cases and 24 multi-turn sequences. It
uses real public B retrieval and real D recommendation through their public
interfaces, while A/C remain scripted contract envelopes until their owners
deliver implementations. The fixture status is explicitly
`draft_pending_c_approval`: it validates E sequencing, state hand-off,
citations, and safety integration, not A/C model quality or policy approval.

Run the no-network checks from the repository root:

```bash
PYTHONPATH=src:tests python -m unittest discover -s tests/unit -v
PYTHONPATH=src:tests python -m unittest discover -s tests/integration -v
PYTHONPATH=src:tests python -m unittest discover -s tests/e2e -v
```

The default E2E retriever uses a deterministic test reranker. In the prepared
`irs` environment, an optional replacement run uses B's already-cached fixed
Cross-Encoder and fails closed rather than downloading a model:

```bash
conda run -n irs env PYTHONPATH=src:tests BANKING_AGENT_E2E_RERANKER=cross_encoder \
  python -m unittest discover -s tests/e2e -v
```

## LLM gateway

`banking_agent.app.providers` is E-owned, injectable infrastructure for later
A/C implementations and optional evidence-grounded response wording; it is not
an authority for intents, actions, state patches, or final banking decisions.
The default provider is the deterministic
local `mock`, so neither the browser demo nor CI needs a key or makes a network
call. The optional server-only OpenAI-compatible transport is enabled with
`BANKING_AGENT_LLM_PROVIDER=openai_compatible`, an HTTPS
`BANKING_AGENT_LLM_BASE_URL`, and `BANKING_AGENT_LLM_API_KEY`; never place the
key in browser code or commit it to the repository.

The gateway validates structured responses, bounds retries/timeouts/concurrency
and rate, and returns sanitized transport errors. An optional opaque
idempotency key is passed unchanged across retries, coalesces concurrent
duplicates, and retains successful process-local results for a configured TTL;
a key reused with different request content fails with an idempotency conflict.
Before any provider call, credential-like data such as PINs, OTPs, passwords
and CVV/CVC is blocked. Recognised card, labelled account, phone, email and
NRIC-like values are replaced with request-local placeholders. This is baseline
data minimisation, not a substitute for provider contractual and regional-data
review.

To enable optional LLM wording for C-approved, evidence-backed `ANSWER`
 responses, also set `BANKING_AGENT_RESPONSE_GENERATOR=llm` and
`BANKING_AGENT_LLM_MODEL` (the model name supported by the chosen
OpenAI-compatible endpoint). It is off by default. The generator can only cite
documents C has approved; invalid or unavailable LLM output falls back to the
deterministic evidence response. It is never invoked for safety, complaint,
recommendation, clarification, or abstention decisions.

Recommendation presentation is a separate, opt-in delivery feature:
set `BANKING_AGENT_RECOMMENDATION_RESPONSE_GENERATOR=llm` together with
`BANKING_AGENT_LLM_MODEL`. It runs only after C has permitted `RECOMMEND` and
D has returned one or more eligible synthetic items. The model can supply only
a short non-factual introduction; E always renders D's product names, order,
and reasons unchanged. Invalid or unavailable output falls back to the same
deterministic recommendation list, so this setting cannot alter eligibility or
which product is shown.

For a normal offline demo or CI run, all optional LLM helpers remain off. To
run the reviewed full delivery chain, set the named profile below alongside the
provider/model configuration:

```bash
export BANKING_AGENT_DELIVERY_PROFILE=frozen-20261023
```

This selects the configuration used by the structured freeze: bounded recent
context, typed LLM understanding in guarded `fuse` mode, query rewrite,
clarification wording, evidence-grounded final-answer rendering, and
non-factual recommendation presentation. It does not supply a provider URL,
key, or model name: those must still be explicit server-side settings. Startup
therefore fails closed if the profile is selected without a usable model
configuration. Any individual `BANKING_AGENT_*` helper variable remains an
explicit override, including an override to `off` for diagnosis or rollback.

The B0 context window contains at most three completed public turns from the
same conversation. A context draft may clarify an explicit reference in the
current turn, but cannot create a C decision or state patch; unavailable,
ambiguous, or invalid context falls back to current-turn behavior.

After configuring a compatible provider in the ignored `.env`, run the small
paid, synthetic-only terminal smoke test with
`PYTHONPATH=src python scripts/smoke_llm_middle_loop.py`. It verifies LLM
understanding, query rewrite, clarification, and evidence-grounded answering;
it is intentionally separate from CI.

For the paid terminal five-path composition check (real MiniLM, B/C/D and
DeepSeek), run `PYTHONPATH=src python scripts/run_real_llm_e2e.py`.

## Optional local ASR demo

The ASR slice provides both a terminal demo and an optional local browser
input adapter. The browser feature is deliberately off by default and is
available only for an explicitly injected `production` module bundle. It
records through the browser microphone, creates a 16 kHz mono PCM WAV locally,
and sends it to the local process only. The returned transcript is editable;
the user must explicitly use the edited text before it enters the ordinary text
workflow. Audio and unconfirmed transcripts are never persisted or added to
agent traces.

The demo is fixed to the multilingual `large-v3-turbo-q5_0` Whisper model. It
is not committed to Git and must be installed by a developer or evaluator once;
the application does not ask end users to select or download a model. Its
measured ASCEND smoke-evaluation result on this project is 21.12% mixed-token
error rate on the 60 mixed-language clips, with all 80 selected generic public
clips transcribed successfully. This is not a banking-domain quality or safety
claim; the submission-level summary is in the final evaluation report above.

### Install the tested ASR model

Clone and build the official `whisper.cpp` source, then explicitly download
the tested multilingual `large-v3-turbo-q5_0` model into the ignored `models/`
directory. Model download is a developer setup step; the application never
downloads a model automatically. On Apple Silicon, build the tested Metal
configuration:

```bash
git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git /private/tmp/whisper-cpp
cmake -S /private/tmp/whisper-cpp -B /private/tmp/whisper-cpp/build \
  -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON
cmake --build /private/tmp/whisper-cpp/build --config Release -j 4
mkdir -p models
/private/tmp/whisper-cpp/models/download-ggml-model.sh large-v3-turbo-q5_0 "$PWD/models"
shasum -a 256 models/ggml-large-v3-turbo-q5_0.bin
```

The expected model SHA-256 is
`394221709cd5ad1f40c46e6031ca61bce88931e6e088c188294c6d5a55ffa7e2`.
If Metal cannot allocate memory, close memory-intensive applications and retry;
do not silently fall back to a different model.

For a Linux host with a supported NVIDIA CUDA toolchain, use the same source
and model but configure with `-DGGML_CUDA=ON`. CPU-only compatibility builds
omit the acceleration flag. CUDA and CPU are reference configurations, not CI
or project-machine-validated configurations.

Run a local WAV transcription with the explicit executable path:

```bash
PYTHONPATH=src python -m banking_agent.modules.voice.cli path/to/input.wav \
  --backend whisper_cpp \
  --executable /private/tmp/whisper-cpp/build/bin/whisper-cli \
  --model "$PWD/models/ggml-large-v3-turbo-q5_0.bin" \
  --language auto
```

### Enable the local browser microphone adapter

After installing the same executable and model, start an application that has
an owner-provided `production` `ModuleBundle` and set the following local
environment variables. The app never downloads a model automatically.

```bash
export BANKING_AGENT_ASR=enabled
export BANKING_AGENT_ASR_EXECUTABLE=/private/tmp/whisper-cpp/build/bin/whisper-cli
export BANKING_AGENT_ASR_MODEL="$PWD/models/ggml-large-v3-turbo-q5_0.bin"
export BANKING_AGENT_ASR_TIMEOUT_SECONDS=90
```

`GET /api/config` advertises `voice_input_available` only when the adapter is
configured and the module mode is `production`; fixture mode remains fully
deterministic and text-only. The browser does not include text-to-speech.

The initial input contract is PCM WAV, 16 kHz, mono, 16-bit, maximum 60 seconds
and 10 MiB. The public ASCEND smoke evaluation remains local because its
reports include public source transcripts and hypotheses; model binaries,
audio, and reports are ignored by Git.

The server defaults to `BANKING_AGENT_MODULE_MODE=production`. Its E-owned
composition root selects the delivered A/B/C/D adapters; fixture replay remains
available only through explicit `fixture` mode for deterministic development and
CI checks.

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
