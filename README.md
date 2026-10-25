# IRS Banking Voice Agent

## Project title

**NovaGuide — a safe, evidence-grounded banking service-agent prototype**

## Executive summary

NovaGuide is a text-first banking-service prototype for a fictional Singapore
retail bank. It combines intent and risk understanding, C-owned complaint and
safety rules, retrieval-grounded policy answers, controlled synthetic product
recommendations, and an optional local-only ASR boundary. The project uses
synthetic data only: it does not connect to banking systems, process customer
records, or execute transactions.

The agent fails closed for unavailable modules, unsupported account operations,
unsafe recommendations, insufficient evidence, and high-risk reports. The
current submission layout keeps all implementation, tests, fixtures, technical
documentation, evaluation tooling, and synthetic corpora together under
[`SystemCode/IRS-Banking-Voice-Agent`](SystemCode/IRS-Banking-Voice-Agent).

## Repository layout

```text
SystemCode/IRS-Banking-Voice-Agent/  runnable project, tests, fixtures and technical docs
ProjectReport/                       optional submission report material
Video/                               optional demo recording
Miscellaneous/                       optional supplementary material
```

## Run locally

From the system-code directory:

```bash
cd SystemCode/IRS-Banking-Voice-Agent
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
PYTHONPATH=src .venv/bin/python -m banking_agent.app.api.server
```

The local synthetic application then listens on `http://127.0.0.1:8000`.
Do not enter real personal, account, or banking data.

## Validation

```bash
cd SystemCode/IRS-Banking-Voice-Agent
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/unit -v
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/integration -v
PYTHONPATH=src:tests .venv/bin/python -m unittest discover -s tests/e2e -v
```

Detailed contracts, C-rule safety behavior, evaluation scope, local browser
acceptance, and ASR constraints are retained with the runnable project under
`SystemCode/IRS-Banking-Voice-Agent/docs/`.

## Submission notes

The local ASR implementation is an optional terminal boundary: it accepts only
short 16kHz mono PCM WAV input, processes it through an explicitly configured
local backend, and removes temporary audio after transcription. Historical LLM
and hardware-specific evaluation artifacts are not committed; their documented
hashes and limitations remain in the system-code documentation.
