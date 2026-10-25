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

### Run the local synthetic application

```bash
cd SystemCode/IRS-Banking-Voice-Agent
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
PYTHONPATH=src .venv/bin/python -m banking_agent.app.api.server
```

Open `http://127.0.0.1:8000` in a local browser. The application uses
synthetic accounts and fixtures only. Do not enter real personal, account or
banking data.

### Validate the project

```bash
cd SystemCode/IRS-Banking-Voice-Agent
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/unit -v
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/integration -v
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/e2e -v
```

The local ASR boundary is optional. It accepts only short 16kHz mono PCM WAV
input, uses an explicitly configured local backend, and removes temporary
audio after transcription.

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
