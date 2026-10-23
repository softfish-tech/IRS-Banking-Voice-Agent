"""Re-aggregate a completed unified-freeze report without re-running inference.

This preserves every raw attempt, trace, response, and timing record in the
source report. It only replaces the derived summary so legacy multi-turn
oracle populations are not incorrectly pooled.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_unified_freeze import _markdown, _summarize


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_json", type=Path, help="Existing unified-freeze report.json")
    parser.add_argument("--output-dir", type=Path, help="Defaults to the source report directory")
    args = parser.parse_args()

    source = args.report_json.resolve()
    report = json.loads(source.read_text(encoding="utf-8"))
    if report.get("evaluation") != "unified_freeze_v1":
        raise ValueError("not_a_unified_freeze_v1_report")
    missing = {"manifest", "core_attempts", "technical_attempts", "complex_attempts"} - set(report)
    if missing:
        raise ValueError(f"missing_raw_report_fields:{','.join(sorted(missing))}")

    report["summary"] = _summarize(report)
    report["rescore"] = {
        "method": "unified_freeze_rescore_v1",
        "rescored_at": datetime.now(UTC).isoformat(),
        "source_report": str(source),
        "note": "Aggregation only: no model, retrieval, evaluator, or fixture execution was repeated; raw attempts are unchanged.",
    }
    output_dir = args.output_dir.resolve() if args.output_dir else source.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report_rescored.json"
    markdown_path = output_dir / "report_rescored.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json": str(json_path), "report_markdown": str(markdown_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
