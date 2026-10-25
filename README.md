### [ Practice Module ] Project Submission

---

## SECTION 1 : NovaBank Intelligent RAG Customer Agent 

NovaGuide is a text-first banking service-agent prototype for a fictional
Singapore retail bank. 

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

| Official Full Name  | Student ID (MTech Applicable)  | Work Items (Who Did What) | Email (Optional) |
| :------------ |:---------------:| :-----| :-----|
| Shao Junzhe | A0356163A |  B modules, RAG,	Knowledge base construction, and RAG evaluation| shaojunzhe@u.nus.edu |
| Lin zhi | A0356103N | D modules, product recommendation, eligibility filtering, ranking, and module testing| zhi_lin@u.nus.edu |
| Zhao Xinyu | A0352367Y | xxxxxxxxxx yyyyyyyyyy zzzzzzzzzz| A1234567C@outlook.com |
| Xie Yuchen | A0350890B | xxxxxxxxxx yyyyyyyyyy zzzzzzzzzz| A1234567D@yahoo.com |
| Ruan Yu | A0351861A | E modules, system integration, backend/ui development, LLM integration| ruanyu@u.nus.edu |


---

## SECTION 4 : VIDEO OF SYSTEM MODELLING & USE CASE DEMO

Place the final demonstration recording in [`Video/`](Video/), or replace this
section with the approved hosted-video link before submission.

Suggested demonstration paths and browser acceptance steps are documented in
`SystemCode/IRS-Banking-Voice-Agent/docs/video_demo_use_cases.md` and
`SystemCode/IRS-Banking-Voice-Agent/docs/local_browser_acceptance.md`.

---

## SECTION 5 : USER GUIDE

NovaGuide is a local, synthetic-data demonstration. It requires Python 3.11+
and a modern browser; do not enter real customer, account or banking data.

### Start the text application

```bash
cd SystemCode/IRS-Banking-Voice-Agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/banking_agent/modules/rag/requirements.txt
python -m pip install -e . --no-deps
hf download sentence-transformers/all-MiniLM-L6-v2
hf download cross-encoder/ms-marco-MiniLM-L6-v2
PYTHONPATH=src python -m banking_agent.app.api.server
```

Open `http://127.0.0.1:8000`, create a local synthetic account, select a demo
profile, and send a question. For grounded answers, use **View evidence** to
inspect policy excerpts and citations. The system may also ask for clarification,
abstain, or provide escalation guidance according to its safety rules.

### Use the browser application

1. Open `http://127.0.0.1:8000` and select **Create account**.
2. Enter a local username and password, then choose one of the synthetic demo
   profiles. No real account or personal information is required.
3. Sign in and start a new conversation, or choose an existing local
   conversation from the sidebar.
4. Enter a banking-service question and select **Send**. The agent may answer
   with cited policy evidence, ask for clarification, abstain where evidence is
   insufficient, or provide escalation or complaint guidance.
5. For a grounded answer, select **View evidence** to inspect the supporting
   policy excerpts and citation identifiers.
6. If ASR is configured, select **Voice**, record a request, review or edit the
   transcript, then select **Use text** to send it as a normal text request.

The prototype never executes transactions, accesses real accounts, or makes
binding financial decisions.

### Optional local ASR

ASR is disabled by default. It uses a developer-installed local `whisper.cpp`
executable and the tested `large-v3-turbo-q5_0` model; the application never
downloads a model or sends audio remotely. After installing them, configure the
following in `SystemCode/IRS-Banking-Voice-Agent/.env` (or export them):

```bash
BANKING_AGENT_ASR=enabled
BANKING_AGENT_ASR_EXECUTABLE=/path/to/whisper-cli
BANKING_AGENT_ASR_MODEL=/absolute/path/to/ggml-large-v3-turbo-q5_0.bin
BANKING_AGENT_ASR_TIMEOUT_SECONDS=90
```

The browser accepts only 16 kHz mono PCM WAV recordings, up to 60 seconds and
10 MiB. It displays an editable transcript; only text confirmed with **Use
text** enters the normal conversation workflow. Full ASR setup, the pinned
model hash, and platform-specific build commands are in the
[system-code README](SystemCode/IRS-Banking-Voice-Agent/README.md#optional-local-asr-demo).

---

## SECTION 6 : PROJECT REPORT / PAPER

Place the final report and user-guide PDF files in [`ProjectReport/`](ProjectReport/).

The runnable project includes technical contracts, safety rules, evaluation
scope, data provenance and recorded limitations in
`SystemCode/IRS-Banking-Voice-Agent/docs/`.

---

## SECTION 7 : MISCELLANEOUS

Historical LLM and hardware-specific ASR evaluation artifacts are intentionally
not committed. Their documented hashes, scope and limitations remain in the
system-code technical documentation.
