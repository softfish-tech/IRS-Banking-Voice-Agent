"""Replace an unscored legacy population with a legacy-only judge artifact.

This never calls the provider. It preserves the baseline verdicts for core,
complex and expanded populations, then replaces—not adds to—the legacy rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _summarize(verdicts: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in verdicts:
        grouped[row["population"]].append(row)
    result = {}
    for name, items in grouped.items():
        in_scope = [item for item in items if item["scope"] == "answer_or_clarify"]
        scored = [item for item in in_scope if item.get("scored")]
        result[name] = {
            "all_recorded_responses": len(items),
            "answer_or_clarify_candidates": len(in_scope),
            "scored": len(scored),
            "response_passed": sum(item.get("response_passed") is True for item in scored),
            "unscored": len(in_scope) - len(scored),
            "non_answer_structural_safety_only": sum(
                item["scope"] == "non_answer_structural_safety_only" for item in items
            ),
        }
    return result


def merge(baseline: dict, legacy_only: dict, *, baseline_path: Path, legacy_path: Path) -> dict:
    if baseline.get("evaluation") != "final_response_semantic_v1":
        raise ValueError("unsupported_baseline_evaluation")
    if legacy_only.get("evaluation") != "final_response_semantic_v1":
        raise ValueError("unsupported_legacy_evaluation")
    if not legacy_only.get("scope", {}).get("legacy_only"):
        raise ValueError("legacy_report_must_use_legacy_only")
    if baseline.get("sources", {}).get("unified_sha256") != legacy_only.get("sources", {}).get("unified_sha256"):
        raise ValueError("unified_source_hash_mismatch")

    legacy_population = "legacy_multi_turn_reconciliation"
    baseline_rows = [
        row for row in baseline.get("verdicts", [])
        if row.get("population") != legacy_population
    ]
    legacy_rows = [
        row for row in legacy_only.get("verdicts", [])
        if row.get("population") == legacy_population
    ]
    if not legacy_rows:
        raise ValueError("legacy_report_has_no_legacy_verdicts")
    verdicts = [*baseline_rows, *legacy_rows]
    return {
        "evaluation": "final_response_semantic_v1_merged",
        "generated_at": datetime.now(UTC).isoformat(),
        "method": baseline.get("method"),
        "sources": {
            **legacy_only["sources"],
            "baseline_response_semantic": str(baseline_path),
            "baseline_response_semantic_sha256": _sha(baseline_path),
            "legacy_only_response_semantic": str(legacy_path),
            "legacy_only_response_semantic_sha256": _sha(legacy_path),
        },
        "scope": {
            **baseline.get("scope", {}),
            "legacy_only": False,
            "legacy_replaced_from_scored_artifact": True,
        },
        "merge": {
            "operation": "replace_unscored_legacy_population",
            "baseline_legacy_rows_discarded": len(baseline.get("verdicts", [])) - len(baseline_rows),
            "legacy_rows_inserted": len(legacy_rows),
        },
        "summary": _summarize(verdicts),
        "verdicts": verdicts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--legacy-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = merge(
        _load(args.baseline_report), _load(args.legacy_report),
        baseline_path=args.baseline_report, legacy_path=args.legacy_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_json": str(args.output), "summary": report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
