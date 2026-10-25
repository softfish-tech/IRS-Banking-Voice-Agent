"""Run the three-repeat, post-reconciliation legacy multi-turn freeze only."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts import evaluate_real_llm_e2e as core
from scripts.run_unified_freeze import _git, _pct, _rate
from banking_agent.app.local_env import load_local_env

DEFAULT_OUTPUT = ROOT / "artifacts/evaluation/legacy_reconciliation_v2"


def _passed(row: dict) -> bool:
    return row["category"] == "PASS" and row["trace_complete"] and row["module_call_order_matches"]


def _metrics(rows: list[dict], passed) -> dict:
    attempts = [bool(passed(row)) for row in rows]
    sequences: dict[str, list[bool]] = defaultdict(list)
    for row, ok in zip(rows, attempts, strict=True):
        sequences[row["sequence_id"]].append(ok)
    return {
        "turn_pass": _rate(sum(attempts), len(attempts)),
        "sequence_all_configured_repeats_pass": _rate(
            sum(all(values) for values in sequences.values()), len(sequences)
        ),
    }


def _summarize(rows: list[dict]) -> dict:
    state = [row for row in rows if row["sequence_id"].startswith("E2E-MT-STATE") and row["expected"]["status"] != "error"]
    technical = [row for row in rows if row["sequence_id"].startswith("E2E-MT-STATE") and row["expected"]["status"] == "error"]
    b0 = [row for row in rows if "context_evaluation" in row]
    pre_context = [row for row in rows if row["sequence_id"].startswith("E2E-MT-SEM") and "context_evaluation" not in row]
    events = [event for row in rows for event in row["modules"]]
    llm = [event for event in events if event["module"].startswith("E.LLM.")]
    return {
        "state_workflow": _metrics(state, _passed),
        "b0_context_follow_up": _metrics(b0, lambda row: row["context_evaluation"]["passed"]),
        "pre_context_legacy_oracle_diagnostic": _metrics(pre_context, _passed),
        "technical_fixture": {"attempts": len(technical), "note": "not a real-module success denominator"},
        "safety_violations": sum(row["category"].endswith("SAFETY_FAILURE") for row in rows),
        "reliability_cost": {
            "llm_fallbacks": sum(event["status"] == "fallback" for event in llm),
            "llm_calls": len(llm),
            "latency_ms": {"p50": _pct([row["duration_ms"] for row in rows], 50), "p95": _pct([row["duration_ms"] for row in rows], 95)},
        },
    }


async def evaluate(repetitions: int) -> dict:
    if repetitions <= 0:
        raise ValueError("repetitions_must_be_positive")
    load_local_env()
    rows: list[dict] = []
    for repeat in range(1, repetitions + 1):
        run = await core.evaluate(
            True, case_ids=set(), understanding_mode="fuse", context_memory=True,
            full_llm_assistance=True, expanded_multi_turn=False,
        )
        for row in run["rows"]:
            row["repeat"] = repeat
        rows.extend(run["rows"])
    report = {
        "evaluation": "legacy_reconciliation_freeze_v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest": {
            "git": {"revision": _git("rev-parse", "HEAD"), "dirty": bool(_git("status", "--porcelain"))},
            "configuration": {"understanding_mode": "fuse", "context_memory": True, "context_window_public_turns": 3, "query_rewrite": True, "grounded_final_answer": True, "recommendation_presentation": True},
            "fixture": "tests/e2e/multi_turn/**/*.json",
            "repetitions": repetitions,
            "source_full_run": "artifacts/evaluation/unified_freeze_20261023_182527/report_rescored.json",
            "scope": "legacy 24 sequences / 49 turns only; do not pool with the source full run as a same-revision total",
        },
        "rows": rows,
    }
    report["summary"] = _summarize(rows)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = asyncio.run(evaluate(args.repetitions))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_json": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
