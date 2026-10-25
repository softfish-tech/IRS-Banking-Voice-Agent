"""Re-score recorded synthetic final answers without re-running the agent.

Use only with a local freeze artifact created with ``--record-response-text``.
The source fixture supplies the reviewed question and semantic gold; the
artifact supplies the exact rendered response that was previously generated.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from banking_agent.app.local_env import load_local_env
from banking_agent.app.providers import LLMSettings, create_llm_client

try:
    from scripts.evaluate_real_llm_e2e import SemanticResponseEvaluator, apply_semantic_response_assessment
    from scripts.run_single_turn_fuse_freeze import _load_cases, _markdown, _summarize
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from evaluate_real_llm_e2e import SemanticResponseEvaluator, apply_semantic_response_assessment
    from run_single_turn_fuse_freeze import _load_cases, _markdown, _summarize


async def rescore(report: dict) -> dict:
    if report.get("evaluation") != "single_turn_fuse_freeze_v1":
        raise ValueError("unsupported_freeze_report")
    cases = {case["case_id"]: case for case in _load_cases()}
    load_local_env()
    model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
    if not model:
        raise RuntimeError("BANKING_AGENT_LLM_MODEL_required_for_response_rescoring")
    evaluation_settings = LLMSettings.from_environment()
    evaluator = SemanticResponseEvaluator(
        create_llm_client(evaluation_settings), model=model, settings=evaluation_settings
    )
    for mode, result in report.get("modes", {}).items():
        for row in result.get("rows", []):
            case = cases.get(row.get("case_id"))
            if case is None:
                raise ValueError(f"unknown_case_id:{row.get('case_id')}")
            answer = row.get("final_response_text")
            if not isinstance(answer, str):
                raise ValueError("report_missing_final_response_text; rerun_with_record_response_text")
            semantic_gold = {
                **case["semantic_gold"],
                "source_case_id": case["case_id"],
                "understanding": case["understanding"],
            }
            response_gold = semantic_gold.get("response", {})
            if not response_gold:
                continue
            assessment, metadata = await evaluator.assess(
                question=case["input"],
                answer=answer,
                response_gold=response_gold,
                request_id=f"rescore-{mode}-{row['repeat']}-{case['case_id']}",
            )
            row["semantic"] = apply_semantic_response_assessment(
                row["semantic"], assessment, metadata
            )
        result["summary"] = _summarize(result["rows"], report["repetitions"])
    report["response_evaluator"] = "llm_semantic_v1_rescored"
    report["response_rescored_from_recorded_text"] = True
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-json", type=Path, required=True, help="Existing local freeze JSON artifact with final_response_text fields.")
    parser.add_argument("--output", type=Path, required=True, help="New JSON destination; the source artifact is not modified.")
    args = parser.parse_args()
    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    rescored = asyncio.run(rescore(report))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rescored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(_markdown(rescored), encoding="utf-8")
    print(json.dumps({"report_json": str(args.output), "report_markdown": str(args.output.with_suffix('.md'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
