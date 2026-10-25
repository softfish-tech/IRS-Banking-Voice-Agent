"""Evaluate the real A adapter and C pre-routing without any LLM/provider."""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from banking_agent.modules.intent import EncoderIntentClassifier, IntentModuleAdapter
from banking_agent.modules.rules import RuleEngine
from banking_agent.schemas import AgentState, Decision, UnderstandingResult
from banking_agent.app.llm_agent_support import FusedIntentModule, LLMUnderstanding, merge_understanding
from banking_agent.app.local_env import load_local_env
from banking_agent.app.providers import LLMSettings, create_llm_client

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/evaluation/a_only_complex/v1/development.json"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts/evaluation/a_only_semantic"


def default_output_path(fixture: Path, repetitions: int) -> Path:
    """Return a unique local artifact path when the caller omits --output."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_OUTPUT_DIR / f"{fixture.stem}_{repetitions}x_{timestamp}.json"


def _matches(actual: UnderstandingResult, gold: dict) -> bool:
    return any(
        actual.intent == expected["intent"] and actual.risk_level.value == expected["risk_level"]
        for expected in gold.get("allowed", [gold])
    )


async def evaluate(
    *, shadow: bool = False, compare_fuse: bool = False, fixture: Path = FIXTURE,
    progress_label: str | None = None, case_ids: set[str] | None = None,
) -> dict:
    fixture = fixture.resolve()
    try:
        fixture_label = str(fixture.relative_to(ROOT))
    except ValueError as exc:
        raise ValueError("a_only_fixture_must_be_inside_repository") from exc
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "a-only-complex-v1":
        raise RuntimeError("unsupported_a_only_fixture")
    cases = payload["cases"]
    if case_ids is not None:
        cases = [case for case in cases if case["case_id"] in case_ids]
        missing = case_ids - {case["case_id"] for case in cases}
        if missing:
            raise ValueError(f"unknown_a_only_case_ids:{','.join(sorted(missing))}")
    adapter = IntentModuleAdapter(classifier=EncoderIntentClassifier.from_pretrained().classify)
    shadow_adapter = None
    if shadow or compare_fuse:
        load_local_env()
        model = __import__("os").environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
        if not model:
            raise SystemExit("BANKING_AGENT_LLM_MODEL_required_for_shadow")
        shadow_adapter = FusedIntentModule(adapter, LLMUnderstanding(create_llm_client(LLMSettings.from_environment()), model=model), mode="shadow")
    rules = RuleEngine()
    rows, by_family = [], defaultdict(list)
    total_cases = len(cases)
    for index, case in enumerate(cases, start=1):
        if progress_label:
            print(f"[{progress_label} {index}/{total_cases} {case['case_id']}] start", flush=True)
        result = await adapter.analyze(case["case_id"], case["input"])
        understanding = UnderstandingResult.model_validate(result["data"])
        state = AgentState(session_id=case["case_id"], user_text=case["input"], understanding=understanding, **case["state"])
        decision = Decision.model_validate((await rules.decide(state))["data"])
        decision_gold = case["decision"]
        route_ok = (
            decision.action.value == decision_gold.get("action", decision.action.value)
            and decision.action.value in decision_gold.get("allowed_actions", [decision.action.value])
            and (decision_gold.get("reason_code") is None or decision.reason_code == decision_gold["reason_code"])
        )
        row = {"case_id": case["case_id"], "family": case["family"], "understanding_passed": _matches(understanding, case["understanding"]), "route_passed": route_ok, "actual": {"intent": understanding.intent, "risk_level": understanding.risk_level.value, "confidence": understanding.confidence, "action": decision.action.value, "reason_code": decision.reason_code}}
        if shadow_adapter is not None:
            shadow_result = await shadow_adapter.analyze(case["case_id"], case["input"])
            if UnderstandingResult.model_validate(shadow_result["data"]) != understanding:
                raise RuntimeError("shadow_changed_a_result")
            draft = shadow_adapter.last_draft
            draft_understanding = None if draft is None else UnderstandingResult(
                intent=draft.intent,
                confidence=draft.confidence,
                risk_level=draft.risk_level,
                entities=draft.entities,
            )
            row["llm_shadow"] = {
                "status": shadow_adapter.last_llm_status,
                "disposition": shadow_adapter.last_llm_disposition,
                "duration_ms": shadow_adapter.last_llm_duration_ms,
                "attempts": shadow_adapter.last_llm_attempts,
                "understanding_passed": None if draft_understanding is None else _matches(draft_understanding, case["understanding"]),
                "draft": None if draft is None else {"intent": draft.intent, "risk_level": draft.risk_level.value, "confidence": draft.confidence, "ambiguous": draft.ambiguous},
            }
            if compare_fuse:
                fused, disposition = (
                    merge_understanding(understanding, draft, case["input"])
                    if draft is not None
                    else (understanding, "fallback_baseline")
                )
                fused_state = AgentState(session_id=f"fuse-{case['case_id']}", user_text=case["input"], understanding=fused, **case["state"])
                fused_decision = Decision.model_validate((await rules.decide(fused_state))["data"])
                fused_route_ok = (
                    fused_decision.action.value == decision_gold.get("action", fused_decision.action.value)
                    and fused_decision.action.value in decision_gold.get("allowed_actions", [fused_decision.action.value])
                    and (decision_gold.get("reason_code") is None or fused_decision.reason_code == decision_gold["reason_code"])
                )
                row["fuse_candidate"] = {"disposition": disposition, "fallback": draft is None, "understanding_passed": _matches(fused, case["understanding"]), "route_passed": fused_route_ok, "actual": {"intent": fused.intent, "risk_level": fused.risk_level.value, "action": fused_decision.action.value, "reason_code": fused_decision.reason_code}}
        rows.append(row)
        by_family[case["family"]].append(row)
        if progress_label:
            draft = row.get("llm_shadow", {}).get("draft")
            fused = row.get("fuse_candidate", {}).get("actual")
            print(
                f"[{progress_label} {index}/{total_cases} {case['case_id']}] "
                f"a={row['actual']['intent']}/{row['actual']['risk_level']} "
                f"draft={None if draft is None else draft['intent'] + '/' + draft['risk_level']} "
                f"fuse={None if fused is None else fused['intent'] + '/' + fused['risk_level']} "
                f"route={None if fused is None else fused['action']} "
                f"llm={row.get('llm_shadow', {}).get('status')}",
                flush=True,
            )
    summary = {family: {"total": len(items), "understanding_passed": sum(item["understanding_passed"] for item in items), "route_passed": sum(item["route_passed"] for item in items), "both_passed": sum(item["understanding_passed"] and item["route_passed"] for item in items)} for family, items in sorted(by_family.items())}
    shadow_summary = None
    if shadow:
        shadow_rows = [row["llm_shadow"] for row in rows]
        shadow_summary = {"drafts_ok": sum(item["status"] == "ok" for item in shadow_rows), "fallbacks": sum(item["status"] == "fallback" for item in shadow_rows), "ambiguous": sum(bool(item["draft"] and item["draft"]["ambiguous"]) for item in shadow_rows), "mean_duration_ms": round(sum(item["duration_ms"] for item in shadow_rows) / len(shadow_rows))}
    fuse_summary = None
    if compare_fuse:
        candidates = [row["fuse_candidate"] for row in rows if "fuse_candidate" in row]
        fuse_summary = {"candidates": len(candidates), "fallbacks": sum(item["fallback"] for item in candidates), "understanding_passed": sum(item["understanding_passed"] for item in candidates), "route_passed": sum(item["route_passed"] for item in candidates), "selected": sum(item["disposition"] not in {"retained", "fallback_baseline"} for item in candidates)}
    return {"evaluation": "real_A_only_with_C_pre_route", "llm_used": shadow or compare_fuse, "fixture": fixture_label, "total_cases": len(rows), "selected_case_ids": sorted(case_ids) if case_ids is not None else None, "summary_by_family": summary, "shadow_summary": shadow_summary, "fuse_candidate_summary": fuse_summary, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        help="Report destination (default: timestamped JSON under artifacts/evaluation/a_only_semantic/).",
    )
    parser.add_argument("--shadow", action="store_true", help="Record typed LLM drafts while retaining A-only routing.")
    parser.add_argument("--compare-fuse", action="store_true", help="Score an in-memory fuse candidate from shadow drafts; never changes live routing.")
    parser.add_argument("--fixture", type=Path, default=FIXTURE, help="Versioned synthetic development or holdout fixture.")
    parser.add_argument("--case-id", action="append", dest="case_ids", metavar="ID", help="Run one named fixture case; repeat to select several.")
    parser.add_argument("--repetitions", type=int, default=1, help="Repeat the full fixture for LLM-stability diagnostics.")
    args = parser.parse_args()
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive")
    output = args.output or default_output_path(args.fixture, args.repetitions)
    reports = [
        asyncio.run(evaluate(
            shadow=args.shadow,
            compare_fuse=args.compare_fuse,
            fixture=args.fixture,
            progress_label=f"repeat {repeat}/{args.repetitions}",
            case_ids=set(args.case_ids) if args.case_ids else None,
        ))
        for repeat in range(1, args.repetitions + 1)
    ]
    if args.repetitions == 1:
        report = reports[0]
    else:
        rows = [row for item in reports for row in item["rows"]]
        shadow_rows = [row["llm_shadow"] for row in rows if "llm_shadow" in row]
        candidates = [row["fuse_candidate"] for row in rows if "fuse_candidate" in row]
        report = {
            "evaluation": "repeated_real_A_LLM_draft_fuse_pre_route",
            "fixture": reports[0]["fixture"],
            "repetitions": args.repetitions,
            "total_attempts": len(rows),
            "summary": {
                "a_understanding_passed": sum(row["understanding_passed"] for row in rows),
                "a_route_passed": sum(row["route_passed"] for row in rows),
                "llm_drafts_ok": sum(row["status"] == "ok" for row in shadow_rows),
                "llm_draft_understanding_passed": sum(row["understanding_passed"] is True for row in shadow_rows),
                "llm_fallbacks": sum(row["status"] == "fallback" for row in shadow_rows),
                "fuse_understanding_passed": sum(row["understanding_passed"] for row in candidates),
                "fuse_route_passed": sum(row["route_passed"] for row in candidates),
                "fuse_selected": sum(row["disposition"] not in {"retained", "fallback_baseline"} for row in candidates),
            },
            "repeat_reports": reports,
        }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    try:
        output_label = output.resolve().relative_to(ROOT)
    except ValueError:
        output_label = output.resolve()
    print(f"report_written: {output_label}")


if __name__ == "__main__":
    main()
