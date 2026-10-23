"""Create legacy fixture-reconciliation v3 from recorded post-B0 attempts.

This is an offline re-aggregation only. It updates the twelve superseded
replacement-fee fixture expectations to C's approved clarification policy and
does not invoke A/B/C/D/E or an LLM provider.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_legacy_reconciliation_freeze import _summarize


TARGETS = {f"E2E-MT-SEM-{number:03d}" for number in range(1, 13)}
UPDATED_EXPECTED = {
    "status": "ok",
    "action": "CLARIFY",
    "reason_code": "REPLACEMENT_REASON_REQUIRED",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rescore(source: dict, *, source_path: Path) -> dict:
    if source.get("evaluation") != "legacy_reconciliation_freeze_v2":
        raise ValueError("unsupported_legacy_source_report")
    rows = copy.deepcopy(source["rows"])
    changed = []
    for row in rows:
        if row["sequence_id"] not in TARGETS or row["case_id"] != 1:
            continue
        actual = row["actual"]
        if actual != UPDATED_EXPECTED:
            raise ValueError(f"target_actual_does_not_match_approved_policy:{row['sequence_id']}:{row['repeat']}")
        if row["expected"].get("action") != "ANSWER":
            raise ValueError(f"target_expected_is_not_superseded_answer:{row['sequence_id']}:{row['repeat']}")
        if not row["trace_complete"] or not row["module_call_order_matches"]:
            raise ValueError(f"target_trace_or_call_order_not_reusable:{row['sequence_id']}:{row['repeat']}")
        row["expected"] = dict(UPDATED_EXPECTED)
        row["category"] = "PASS"
        changed.append({"sequence_id": row["sequence_id"], "turn_id": row["case_id"], "repeat": row["repeat"]})
    if len(changed) != 36:
        raise ValueError(f"unexpected_reconciled_attempt_count:{len(changed)}")
    return {
        "evaluation": "legacy_fixture_reconciliation_v3",
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest": {
            **source["manifest"],
            "fixture_reconciliation": {
                "version": "v3",
                "source_report": str(source_path),
                "source_report_sha256": _sha(source_path),
                "execution": "offline_rescore_only_no_agent_or_provider_calls",
                "policy_change": "E2E-MT-SEM-001..012 turn 1 now require CLARIFY / REPLACEMENT_REASON_REQUIRED rather than an unsupported direct replacement-fee ANSWER.",
                "changed_attempts": len(changed),
            },
        },
        "rows": rows,
        "summary": _summarize(rows),
        "reconciled_attempts": changed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source_report.read_text(encoding="utf-8"))
    report = rescore(source, source_path=args.source_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_json": str(args.output), "summary": report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
