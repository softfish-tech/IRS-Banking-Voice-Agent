### [ Practice Module ] Project Submission

---

## SECTION 1 : PROJECT TITLE

## NovaGuide — Safe Evidence-Grounded Banking Voice Agent

NovaGuide is a text-first banking service-agent prototype for a fictional
Singapore retail bank. It is a synthetic-data project and does not connect to
real banking systems, process customer records, or execute transactions.

---

## SECTION 2 : EXECUTIVE SUMMARY / PAPER ABSTRACT

NovaGuide combines intent and risk understanding, C-owned complaint and safety
rules, retrieval-grounded policy answers, controlled synthetic product
recommendations, bounded conversation context, and an optional local-only ASR
boundary. The design prioritises safe handling over unsupported completion:
high-risk reports are escalated, recommendations require resolution and
consent, unsupported account operations are blocked, and insufficient evidence
produces abstention or clarification rather than a fabricated answer.

The project is organised as a submission repository. All runnable application
code, synthetic corpora, tests, evaluation fixtures, ASR implementation and
technical documentation are retained together in
[`SystemCode/IRS-Banking-Voice-Agent`](SystemCode/IRS-Banking-Voice-Agent).

---

## SECTION 3 : CREDITS / PROJECT CONTRIBUTION

| Team member | Contribution |
| :--- | :--- |
| Team members | Add final names, student IDs and individual contributions before submission. |

The current repository records module ownership and integration boundaries in
`SystemCode/IRS-Banking-Voice-Agent/docs/module_ownership.md`.

---

## SECTION 4 : VIDEO OF SYSTEM MODELLING & USE CASE DEMO

Place the final demonstration recording in [`Video/`](Video/), or replace this
section with the approved hosted-video link before submission.

Suggested demonstration paths and browser acceptance steps are documented in
`SystemCode/IRS-Banking-Voice-Agent/docs/video_demo_use_cases.md` and
`SystemCode/IRS-Banking-Voice-Agent/docs/local_browser_acceptance.md`.

---

## SECTION 5 : USER GUIDE

### 5.1 Scope and requirements

NovaGuide is a local demonstration prototype using synthetic data only. It
requires Python 3.11 or later, a modern browser and sufficient local storage
for downloaded models. It does not connect to real banking systems and must
not be used with real customer or banking information.

The text application requires the intent encoder and retrieval reranker. Local
ASR and LLM-assisted delivery are optional extensions. Text-to-speech is not
implemented.

| Component | Model or dependency | Purpose | Required for text demo |
|---|---|---|---|
| Intent understanding | `sentence-transformers/all-MiniLM-L6-v2` | Frozen sentence encoder used by the intent classifier | Yes |
| Retrieval reranking | `cross-encoder/ms-marco-MiniLM-L6-v2` | Reranks BM25 policy-document candidates | Yes |
| Voice input | Whisper `large-v3-turbo-q5_0` with `whisper.cpp` | Optional local speech-to-text | No |
| LLM delivery | OpenAI-compatible endpoint and configured model | Guarded semantic assistance and response delivery | No |

### 5.2 Install and start the text application

Install the project dependencies in an isolated Python environment. The
repository provides the pinned retrieval dependency list used for the local
production composition.

```bash
cd SystemCode/IRS-Banking-Voice-Agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/banking_agent/modules/rag/requirements.txt
python -m pip install -e . --no-deps
```

Download and cache the required Hugging Face models before starting the
production application. The exact download method depends on the installed
Hugging Face tooling; for example:

```bash
hf download sentence-transformers/all-MiniLM-L6-v2
hf download cross-encoder/ms-marco-MiniLM-L6-v2
```

Start the local server from the system-code directory:

```bash
PYTHONPATH=src python -m banking_agent.app.api.server
```

Open `http://127.0.0.1:8000` in a browser. The application uses a local SQLite
database for synthetic accounts, sessions and conversations. If either
required local model is unavailable, the production composition fails closed
rather than downloading a replacement automatically.

### 5.3 Configure optional local ASR

The ASR feature is optional and provides speech-to-text input only. It records
a short browser microphone input, converts it to 16 kHz mono PCM WAV, sends it
to a local `whisper.cpp` process, and returns an editable transcript. Audio
and unconfirmed transcripts are not persisted.

#### Install the pinned ASR model

Build `whisper.cpp` and download the tested multilingual Whisper model. The
following example is the tested Apple-Silicon Metal configuration:

```bash
git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git /private/tmp/whisper-cpp
cmake -S /private/tmp/whisper-cpp -B /private/tmp/whisper-cpp/build \
  -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON
cmake --build /private/tmp/whisper-cpp/build --config Release -j 4
mkdir -p models
/private/tmp/whisper-cpp/models/download-ggml-model.sh large-v3-turbo-q5_0 "$PWD/models"
shasum -a 256 models/ggml-large-v3-turbo-q5_0.bin
```

The expected SHA-256 for `ggml-large-v3-turbo-q5_0.bin` is:

```text
394221709cd5ad1f40c46e6031ca61bce88931e6e088c188294c6d5a55ffa7e2
```

For a compatible Linux NVIDIA CUDA environment, build the same source with
`-DGGML_CUDA=ON`. A CPU-only build can omit the acceleration option. The tested
model and executable are local developer dependencies; the browser never
downloads them automatically.

#### Enable ASR in local configuration

Add the following values to a `SystemCode/IRS-Banking-Voice-Agent/.env` file,
or export them in the shell before starting the server. Do not commit `.env` or
model binaries to version control.

```bash
BANKING_AGENT_ASR=enabled
BANKING_AGENT_ASR_EXECUTABLE=/private/tmp/whisper-cpp/build/bin/whisper-cli
BANKING_AGENT_ASR_MODEL=/absolute/path/to/IRS-Banking-Voice-Agent/models/ggml-large-v3-turbo-q5_0.bin
BANKING_AGENT_ASR_TIMEOUT_SECONDS=90
```

Restart the server after changing the configuration. When ASR is available,
the browser displays a **Voice** button. Select it to record a request, review
or edit the returned transcript, then select **Use text** before sending. A
recording is limited to 60 seconds and 10 MiB.

### 5.4 Configure LLM-assisted delivery

LLM assistance uses a server-side OpenAI-compatible gateway. The browser never
receives the provider URL or API key. The LLM can support typed understanding,
query rewriting, clarification wording, grounded answer wording and
recommendation presentation; it cannot choose a RuleEngine action, alter
state, approve evidence, change eligibility or execute operations.

Create a `SystemCode/IRS-Banking-Voice-Agent/.env` file and add the provider
settings below. Replace the placeholder values with the endpoint, credential
and model provided by the selected LLM service.

```bash
BANKING_AGENT_LLM_PROVIDER=openai_compatible
BANKING_AGENT_LLM_BASE_URL=https://your-llm-provider.example/v1
BANKING_AGENT_LLM_API_KEY=replace_with_server_side_api_key
BANKING_AGENT_LLM_MODEL=deepseek-flash
```

After saving `.env`, restart the server from `SystemCode/IRS-Banking-Voice-Agent`:

```bash
PYTHONPATH=src python -m banking_agent.app.api.server
```

The configured delivery pipeline uses bounded recent-turn context, guarded
`fuse` understanding, query rewriting, clarification wording,
evidence-grounded final-answer rendering and non-factual recommendation
presentation. The gateway blocks credential-like content, replaces recognised
identifiers with request-local placeholders before provider transmission,
validates structured output, and returns deterministic fallback delivery if the
provider times out or returns invalid output.

### 5.5 Web application user guide

1. Open `http://127.0.0.1:8000` and select **Create account**.
2. Enter a local username and password, then choose a synthetic demo profile.
3. Sign in and start a new conversation, or select a previous local conversation.
4. Enter a service question and select **Send**. Depending on the safety rules
   and available evidence, the system may answer, ask for clarification,
   abstain, provide escalation or complaint guidance, or present eligible
   product recommendations.
5. For grounded answers, select **View evidence** to inspect the supporting
   policy excerpts and citations.
6. If ASR is enabled, select **Voice**, review or edit the transcript, then
   select **Use text** before sending it as an ordinary text request.

The prototype does not execute transactions, access real accounts or make
binding financial decisions.

---

## SECTION 6 : PROJECT REPORT / PAPER

Place the final report and user-guide PDF files in [`ProjectReport/`](ProjectReport/).

The runnable project includes technical contracts, safety rules, evaluation
scope, data provenance and recorded limitations in
`SystemCode/IRS-Banking-Voice-Agent/docs/`.

---

## SECTION 7 : MISCELLANEOUS

Use [`Miscellaneous/`](Miscellaneous/) for approved supplementary submission
material that is not executable system code, a report, or a demonstration
video.

Historical LLM and hardware-specific ASR evaluation artifacts are intentionally
not committed. Their documented hashes, scope and limitations remain in the
system-code technical documentation.
