# IRS-Banking-Voice-Agent

## Overview

This repository contains a modular prototype for a safe banking service agent for a fictional Singapore retail bank. The intended workflow combines intent and risk understanding, evidence-grounded policy answers, complaint handling, responsible recommendations, and a future voice interface.

The prototype uses synthetic data only. It does not connect to real banking systems, process real customer records, execute transactions, or make binding financial decisions.

## Current phase

The project is currently in Phase 1: text-first integration design and mock readiness.

- The repository skeleton, module boundaries, shared State schema, API contract, scenario acceptance table, and engineering conventions are in place.
- The current architecture covers UI/API/voice integration, orchestration, A/B/C/D module boundaries, and safe routing.
- The browser application, real B/D integration bridges, provider gateway, and
  terminal-only local ASR boundary are available. A/C production
  implementations and an audio browser interface remain future work.

For a local, fixture-backed browser application with synthetic account
registration/login and persisted conversation history, run:

```bash
PYTHONPATH=src python -m banking_agent.app.api.server
```

Then open `http://127.0.0.1:8000`. Create a local-only account with a test
password of at least 6 characters and select one clearly-labelled synthetic
demo profile; it is fixed for that account and snapshotted on new conversations
for D recommendation tests. The SQLite database is stored under
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

## E2E integration data and checks

E owns the frozen, versioned text E2E fixtures and their runner. The current
hybrid suite contains 42 single-turn cases and 16 multi-turn sequences. It
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
A/C implementations; it is not an authority for intents, actions, state
patches, or final banking responses. The default provider is the deterministic
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

## Optional local ASR demo

The browser application does not yet accept audio. The ASR slice is a
terminal-only local demo: it produces a candidate transcript which a later
voice UI must show and have the user confirm before it enters the banking
workflow. Audio is never sent to a remote provider or persisted by the ASR
adapter.

The demo is fixed to the multilingual `large-v3-turbo-q5_0` Whisper model. It
is not committed to Git and must be installed by a developer or evaluator once;
the application does not ask end users to select or download a model. Its
measured ASCEND smoke-evaluation result on this project is 22.26% mixed-token
error rate (80 generic public clips). This is not a banking-domain quality or
safety claim.

Clone and build the official `whisper.cpp` source, then download the model into
the ignored `models/` directory. On Apple Silicon, build the tested Metal
configuration:

```bash
git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git /private/tmp/whisper-cpp
cmake -S /private/tmp/whisper-cpp -B /private/tmp/whisper-cpp/build \
  -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON
cmake --build /private/tmp/whisper-cpp/build --config Release -j 4
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

The initial input contract is PCM WAV, 16 kHz, mono, 16-bit, maximum 60 seconds
and 10 MiB. The public ASCEND smoke evaluation remains local because its
reports include public source transcripts and hypotheses; model binaries,
audio, and reports are ignored by Git.

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
