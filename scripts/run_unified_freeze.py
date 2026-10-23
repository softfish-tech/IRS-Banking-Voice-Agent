"""Run the frozen three-repeat A/B/C/D/E acceptance population.

This is deliberately an orchestration layer over the maintained evaluators.  It
does not tune prompts or select a winning configuration: its job is to pin one
configuration, retain every synthetic response/trace, and report denominators
separately for core, complex-development, complex-holdout, legacy multi-turn,
and approved expanded multi-turn fixtures.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from hashlib import sha256
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from banking_agent.app.local_env import load_local_env
from banking_agent.app.providers import LLMSettings
from banking_agent.schemas import AgentState

try:
    from scripts import evaluate_real_llm_e2e as core
    from scripts import run_single_turn_fuse_freeze as complex_freeze
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import evaluate_real_llm_e2e as core
    import run_single_turn_fuse_freeze as complex_freeze


DEFAULT_OUTPUT = ROOT / "artifacts/evaluation/unified_freeze"
METRIC_TAGS = ROOT / "tests/fixtures/evaluation/multi_turn_semantic/v1/expanded_e2e_metric_tags.json"


class _InjectedIntentFailure:
    """Evaluation-only A failure injection; no product code path uses this."""

    async def analyze(self, session_id: str, user_text: str) -> dict:
        return {"status": "error"}


def _git(*args: str) -> str | None:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else None


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _population() -> dict:
    core_cases = core._load_cases()
    complex_cases = complex_freeze._load_cases()
    expanded = core._load_expanded_multi_turn()
    legacy = [json.loads(path.read_text(encoding="utf-8"))["sequence_id"] for path in sorted(core.MULTI_TURN_ROOT.glob("**/*.json"))]
    return {
        "core_business_case_ids": sorted(case["case_id"] for case in core_cases if not case["case_id"].startswith("E2E-T")),
        "technical_case_ids": sorted(case["case_id"] for case in core_cases if case["case_id"].startswith("E2E-T")),
        "complex_development_case_ids": sorted(case["case_id"] for case in complex_cases if case["split"] == "development"),
        "complex_holdout_case_ids": sorted(case["case_id"] for case in complex_cases if case["split"] == "holdout"),
        "legacy_sequence_ids": sorted(legacy),
        "expanded_sequence_ids": sorted(sequence["id"] for sequence, _ in expanded),
    }


def _manifest(*, repetitions: int, selected: dict, population: dict) -> dict:
    settings = LLMSettings.from_environment()
    # Never write base URL or API key into a shareable artifact.
    return {
        "schema_version": "unified-freeze-manifest-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "git": {"revision": _git("rev-parse", "HEAD"), "dirty": bool(_git("status", "--porcelain"))},
        "configuration": {
            "understanding_mode": "fuse", "context_memory": True,
            "context_window_public_turns": 3, "query_rewrite": True,
            "grounded_final_answer": True, "recommendation_presentation": True,
            "model": os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip() or None,
            "provider": settings.provider, "timeout_seconds": settings.timeout_seconds,
            "max_retries": settings.max_retries, "max_concurrency": settings.max_concurrency,
            "temperature": os.environ.get("BANKING_AGENT_LLM_TEMPERATURE", "provider_default_not_exposed"),
            "top_k": os.environ.get("BANKING_AGENT_LLM_TOP_K", "provider_default_not_exposed"),
            "context_reset_expiry": "per evaluator sequence; no cross-sequence carry-over; last 3 completed public turns only",
        },
        "fixture_versions": {
            "core": "tests/e2e/single_turn/*.json", "complex": "a-only-complex-v1 / complex-language-semantic-v1",
            "legacy_multi_turn": "tests/e2e/multi_turn/**/*.json", "expanded_multi_turn": "multi_turn_semantic/v1",
        },
        "fixture_sha256": {
            "expanded_annotations": _digest(core.EXPANDED_MULTI_TURN_ANNOTATIONS),
            "expanded_metric_tags": _digest(METRIC_TAGS),
            "complex_development": _digest(complex_freeze.DEVELOPMENT),
            "complex_holdout": _digest(complex_freeze.HOLDOUT),
        },
        "retrieval_profile": {
            "backend": "optimized_bm25_cross_encoder", "candidate_k": 20, "top_k": 5,
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "reranker_revision": "233902d25c440f23af6f7d6e94d2946bac0bee0a",
        },
        "immutable_population": population,
        "repetitions": repetitions, "selection": selected,
        "response_text": "retained only in this local synthetic evaluation artifact",
    }


def _pct(values: list[int], p: int) -> int | None:
    return sorted(values)[round((len(values) - 1) * p / 100)] if values else None


def _rate(passed: int, total: int) -> dict:
    return {"passed": passed, "total": total, "rate": round(passed / total, 4) if total else None}


def _metric_tags() -> dict[tuple[str, int], list[str]]:
    payload = json.loads(METRIC_TAGS.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "expanded-multi-turn-metric-tags-v1":
        raise ValueError("unsupported_expanded_metric_tags")
    result: dict[tuple[str, int], list[str]] = {}
    for item in payload["tags"]:
        key = (item["sequence_id"], item["turn_id"])
        if key in result or not item["metrics"]:
            raise ValueError("invalid_expanded_metric_tags")
        result[key] = list(item["metrics"])
    return result


def _attempt_pass(row: dict, population: str) -> bool:
    if population == "complex":
        return bool(row["semantic"]["outcome_passed"])
    workflow = row["category"] == "PASS" and row["trace_complete"] and row["module_call_order_matches"]
    semantic = row.get("semantic")
    return workflow and (semantic is None or bool(semantic["outcome_passed"]))


def _summarize(report: dict) -> dict:
    core_rows = report["core_attempts"]
    complex_rows = report["complex_attempts"]
    business_core = [r for r in core_rows if not r["sequence_id"] and not r["case_id"].startswith("E2E-T")]
    technical = [r for r in core_rows if not r["sequence_id"] and r["case_id"].startswith("E2E-T")]
    legacy = [r for r in core_rows if (r["sequence_id"] or "").startswith("E2E-MT")]
    expanded = [r for r in core_rows if (r["sequence_id"] or "").startswith("MTX-")]
    complex_dev = [r for r in complex_rows if r["split"] == "development"]
    complex_holdout = [r for r in complex_rows if r["split"] == "holdout"]

    def expected_action(row: dict, kind: str) -> str | None:
        return row["expected_action"] if kind == "complex" else row["expected"]["action"]

    def single_metrics(rows: list[dict], kind: str) -> dict:
        passed = [_attempt_pass(r, kind) for r in rows]
        resolved = [r for r in rows if expected_action(r, kind) in {"ANSWER", "RECOMMEND"}]
        safe = [r for r in rows if expected_action(r, kind) in {"CLARIFY", "ABSTAIN", "BLOCK", "ESCALATE", "HANDLE_COMPLAINT"}]
        return {
            "end_to_end_appropriate": _rate(sum(passed), len(rows)),
            "resolved_answer_or_recommendation": _rate(sum(_attempt_pass(r, kind) for r in resolved), len(resolved)),
            "safe_non_answer_delivery": _rate(sum(_attempt_pass(r, kind) for r in safe), len(safe)),
        }

    mixed = [(row, "core") for row in business_core] + [(row, "complex") for row in complex_rows]
    mixed_resolved = [(row, kind) for row, kind in mixed if expected_action(row, kind) in {"ANSWER", "RECOMMEND"}]
    mixed_safe = [(row, kind) for row, kind in mixed if expected_action(row, kind) in {"CLARIFY", "ABSTAIN", "BLOCK", "ESCALATE", "HANDLE_COMPLAINT"}]
    mixed_metrics = {
        "end_to_end_appropriate": _rate(sum(_attempt_pass(row, kind) for row, kind in mixed), len(mixed)),
        "resolved_answer_or_recommendation": _rate(sum(_attempt_pass(row, kind) for row, kind in mixed_resolved), len(mixed_resolved)),
        "safe_non_answer_delivery": _rate(sum(_attempt_pass(row, kind) for row, kind in mixed_safe), len(mixed_safe)),
    }

    def mt_metrics(rows: list[dict], label: str) -> dict:
        attempted = [_attempt_pass(r, "core") if label == "legacy" else bool(r["expanded_context_evaluation"]["passed"]) for r in rows]
        by_seq: dict[str, list[bool]] = {}
        for row, ok in zip(rows, attempted, strict=True): by_seq.setdefault(row["sequence_id"], []).append(ok)
        return {"turn_pass": _rate(sum(attempted), len(attempted)), "sequence_all_configured_repeats_pass": _rate(sum(all(v) for v in by_seq.values()), len(by_seq))}

    def b0_metrics(rows: list[dict]) -> dict:
        attempted = [bool(row["context_evaluation"]["passed"]) for row in rows]
        by_seq: dict[str, list[bool]] = {}
        for row, ok in zip(rows, attempted, strict=True): by_seq.setdefault(row["sequence_id"], []).append(ok)
        return {"turn_pass": _rate(sum(attempted), len(attempted)), "sequence_all_configured_repeats_pass": _rate(sum(all(v) for v in by_seq.values()), len(by_seq))}

    def stability(rows: list[dict], kind: str) -> dict:
        by_case: dict[str, list[dict]] = {}
        for row in rows:
            by_case.setdefault(row["case_id"], []).append(row)
        complete = [attempts for attempts in by_case.values() if len(attempts) == report["manifest"]["repetitions"]]
        return _rate(sum(all(_attempt_pass(row, kind) for row in attempts) for attempts in complete), len(complete))

    expanded_metrics = {}
    for metric in sorted({tag for row in expanded for tag in row.get("metric_tags", [])}):
        scoped = [row for row in expanded if metric in row.get("metric_tags", [])]
        expanded_metrics[metric] = _rate(
            sum(bool(row["expanded_context_evaluation"]["passed"]) for row in scoped), len(scoped)
        )

    core_grounding = [row["semantic"] for row in business_core if row.get("semantic", {}).get("grounding_passed") is not None]
    complex_grounding = [row["semantic"] for row in complex_rows if row["semantic"].get("grounding_passed") is not None]
    recommendation_rows = [
        (row, kind) for row, kind in mixed
        if expected_action(row, kind) == "RECOMMEND"
    ]
    recommendation_denials = [
        (row, kind) for row, kind in mixed
        if expected_action(row, kind) == "BLOCK" and (
            row.get("semantic", {}).get("checks", {}).get("recommendation") is not None
            or row.get("semantic", {}).get("checks", {}).get("module_calls") is not None
        )
    ]
    legacy_b0 = [row for row in legacy if "context_evaluation" in row]
    legacy_semantic_predecessors = [
        row for row in legacy
        if row["sequence_id"].startswith("E2E-MT-SEM") and "context_evaluation" not in row
    ]
    legacy_technical = [row for row in legacy if row["expected"]["status"] == "error"]
    legacy_state_workflow = [
        row for row in legacy
        if row["sequence_id"].startswith("E2E-MT-STATE") and row["expected"]["status"] != "error"
    ]

    latencies = [r["duration_ms"] for r in core_rows] + [r["trace"]["duration_ms"] for r in complex_rows]
    all_modules = [event for r in core_rows for event in r["modules"]] + [event for r in complex_rows for event in r["trace"]["modules"]]
    llm = [e for e in all_modules if e["module"].startswith("E.LLM.")]
    tokens = [e["total_tokens"] for e in llm if e["total_tokens"] is not None]
    violations = sum(r["category"] == "SAFETY_FAILURE" for r in core_rows) + sum(len(r["safety_violations"]) for r in complex_rows)
    return {
        "single_turn": {"core_business": single_metrics(business_core, "core"), "complex_development": single_metrics(complex_dev, "complex"), "complex_holdout": single_metrics(complex_holdout, "complex"), "business_total": mixed_metrics, "all_configured_repeats_pass": stability(business_core, "core")},
        "technical": _rate(sum(r["passed"] for r in report["technical_attempts"]), len(report["technical_attempts"])),
        "retrieval_grounding": {
            "core_required_evidence": _rate(sum(item["grounding_passed"] is True for item in core_grounding), len(core_grounding)),
            "complex_required_evidence": _rate(sum(item["grounding_passed"] is True for item in complex_grounding), len(complex_grounding)),
        },
        "recommendation_delivery": {
            "permitted_recommendations": _rate(sum(_attempt_pass(row, kind) for row, kind in recommendation_rows), len(recommendation_rows)),
            "denied_recommendations": _rate(sum(_attempt_pass(row, kind) for row, kind in recommendation_denials), len(recommendation_denials)),
        },
        "multi_turn": {
            "legacy": {
                "state_workflow": mt_metrics(legacy_state_workflow, "legacy"),
                "b0_context_follow_up": b0_metrics(legacy_b0),
                "pre_context_legacy_oracle_diagnostic": mt_metrics(legacy_semantic_predecessors, "legacy"),
                "technical_fixture": {"attempts": len(legacy_technical), "note": "not scored as a real-module success; the unified technical injection is authoritative"},
                "note": "Do not pool these distinct legacy oracle populations into one accuracy percentage.",
            },
            "expanded": {**mt_metrics(expanded, "expanded"), "context_diagnostics": expanded_metrics},
        },
        "safety_violations": violations,
        "reliability_cost": {"llm_fallbacks": sum(e["status"] == "fallback" for e in llm), "llm_calls": len(llm), "tokens_total": sum(tokens) if tokens else None, "token_events": len(tokens), "latency_ms": {"p50": _pct(latencies, 50), "p95": _pct(latencies, 95), "mean": round(sum(latencies)/len(latencies)) if latencies else None}},
    }


def _markdown(report: dict) -> str:
    s = report["summary"]
    lines = ["# Unified frozen evaluation", "", f"Generated: {report['generated_at']}", "", "## Separate denominators", ""]
    for name in ("core_business", "complex_development", "complex_holdout", "business_total"):
        value = s["single_turn"][name]
        lines.append(f"- {name}: E2E {value['end_to_end_appropriate']['passed']}/{value['end_to_end_appropriate']['total']}; resolved {value['resolved_answer_or_recommendation']['passed']}/{value['resolved_answer_or_recommendation']['total']}; safe non-answer {value['safe_non_answer_delivery']['passed']}/{value['safe_non_answer_delivery']['total']}.")
    diagnostics = "; ".join(f"{name} {value['passed']}/{value['total']}" for name, value in s["multi_turn"]["expanded"]["context_diagnostics"].items()) or "none selected"
    legacy = s["multi_turn"]["legacy"]
    lines.extend(["", f"- Single-turn all-configured-repeats pass: {s['single_turn']['all_configured_repeats_pass']['passed']}/{s['single_turn']['all_configured_repeats_pass']['total']} (the formal freeze config uses 3 repetitions).", f"- Technical fail-closed injection: {s['technical']['passed']}/{s['technical']['total']}.", f"- Core required evidence/grounding: {s['retrieval_grounding']['core_required_evidence']['passed']}/{s['retrieval_grounding']['core_required_evidence']['total']}; complex: {s['retrieval_grounding']['complex_required_evidence']['passed']}/{s['retrieval_grounding']['complex_required_evidence']['total']}.", f"- Recommendation permitted: {s['recommendation_delivery']['permitted_recommendations']['passed']}/{s['recommendation_delivery']['permitted_recommendations']['total']}; denied: {s['recommendation_delivery']['denied_recommendations']['passed']}/{s['recommendation_delivery']['denied_recommendations']['total']}.", f"- Legacy state/workflow: {legacy['state_workflow']['turn_pass']['passed']}/{legacy['state_workflow']['turn_pass']['total']} turns; sequences all configured repeats pass {legacy['state_workflow']['sequence_all_configured_repeats_pass']['passed']}/{legacy['state_workflow']['sequence_all_configured_repeats_pass']['total']}.", f"- Legacy B0 context follow-up: {legacy['b0_context_follow_up']['turn_pass']['passed']}/{legacy['b0_context_follow_up']['turn_pass']['total']} turns; sequences all configured repeats pass {legacy['b0_context_follow_up']['sequence_all_configured_repeats_pass']['passed']}/{legacy['b0_context_follow_up']['sequence_all_configured_repeats_pass']['total']}.", f"- Legacy pre-context oracle diagnostic: {legacy['pre_context_legacy_oracle_diagnostic']['turn_pass']['passed']}/{legacy['pre_context_legacy_oracle_diagnostic']['turn_pass']['total']} (not pooled); technical legacy attempts: {legacy['technical_fixture']['attempts']}.", f"- Expanded multi-turn: {s['multi_turn']['expanded']['turn_pass']['passed']}/{s['multi_turn']['expanded']['turn_pass']['total']} turns; sequences all configured repeats pass {s['multi_turn']['expanded']['sequence_all_configured_repeats_pass']['passed']}/{s['multi_turn']['expanded']['sequence_all_configured_repeats_pass']['total']}; diagnostics: {diagnostics}.", f"- Safety violations: {s['safety_violations']}; LLM fallbacks: {s['reliability_cost']['llm_fallbacks']}/{s['reliability_cost']['llm_calls']}; latency p50/p95: {s['reliability_cost']['latency_ms']['p50']}/{s['reliability_cost']['latency_ms']['p95']} ms.", "", "LLM semantic judging is not a headline metric. Expanded multi-turn uses reviewed actions, evidence, state/context, and explicit response constraints where present; the raw final response is retained for diagnosis.", ""])
    return "\n".join(lines)


async def evaluate(*, repetitions: int, core_case_ids: set[str] | None = None, complex_case_ids: set[str] | None = None, expanded_sequence_ids: set[str] | None = None, include_legacy_multi_turn: bool = True) -> dict:
    if repetitions <= 0: raise ValueError("repetitions_must_be_positive")
    load_local_env()
    population = _population()
    selected_core = core_case_ids or set(population["core_business_case_ids"])
    selected_complex = complex_case_ids or set(population["complex_development_case_ids"] + population["complex_holdout_case_ids"])
    selected_expanded = expanded_sequence_ids or set(population["expanded_sequence_ids"])
    selected = {"core_case_ids": sorted(selected_core), "complex_case_ids": sorted(selected_complex), "expanded_sequence_ids": sorted(selected_expanded), "include_legacy_multi_turn": include_legacy_multi_turn}
    report = {"evaluation": "unified_freeze_v1", "generated_at": datetime.now(UTC).isoformat(), "manifest": _manifest(repetitions=repetitions, selected=selected, population=population), "core_attempts": [], "technical_attempts": [], "complex_attempts": []}
    for repeat in range(1, repetitions + 1):
        core_run = await core.evaluate(include_legacy_multi_turn, case_ids=selected_core, understanding_mode="fuse", context_memory=True, full_llm_assistance=True, expanded_multi_turn=True, expanded_sequence_ids=selected_expanded)
        semantic_by_source = {row["source_case_id"]: row for row in core_run["semantic_evaluation"]["rows"]}
        for row in core_run["rows"]: row["repeat"] = repeat
        for row in core_run["rows"]:
            row["metric_tags"] = _metric_tags().get((row.get("sequence_id"), row["case_id"]), [])
            if row["case_id"] in semantic_by_source:
                row["semantic"] = semantic_by_source[row["case_id"]]
        report["core_attempts"].extend(core_run["rows"])
        model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip() or None
        components = core._components(model, understanding_mode="fuse", full_llm_assistance=True)
        for case in (item for item in core._load_cases() if item["case_id"].startswith("E2E-T")):
            response, trace = await core._run_turn(
                (_InjectedIntentFailure(), *components[1:]), AgentState(**case["input"], **case["initial_state"]),
                f"unified-technical-{repeat}-{case['case_id']}", case["scenario_id"], progress_label=f"technical {case['case_id']} run={repeat}",
            )
            row = core._row(case["case_id"], case["expected"], response, trace)
            row["repeat"] = repeat
            row["passed"] = (
                response.status == "error" and response.error is not None and response.error.module == "A"
                and response.error.code == "module_error" and [event["module"] for event in row["modules"]] == ["A"]
                and "could not be completed" in response.text.casefold()
            )
            report["technical_attempts"].append(row)
    complex_run = await complex_freeze.evaluate(repetitions=repetitions, enable_query_rewrite=True, semantic_response_evaluation=False, record_response_text=True, case_ids=selected_complex)
    complex_actions = {case["case_id"]: case["semantic_gold"].get("decision", {}).get("action") for case in complex_freeze._load_cases()}
    report["complex_attempts"] = complex_run["modes"]["fuse"]["rows"]
    for row in report["complex_attempts"]:
        row["expected_action"] = complex_actions[row["case_id"]]
    report["summary"] = _summarize(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--core-case-id", action="append")
    parser.add_argument("--complex-case-id", action="append")
    parser.add_argument("--expanded-sequence-id", action="append")
    parser.add_argument("--skip-legacy-multi-turn", action="store_true", help="Smoke-only selector; a frozen run must include all 24 legacy sequences.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = asyncio.run(evaluate(repetitions=args.repetitions, core_case_ids=set(args.core_case_id) if args.core_case_id else None, complex_case_ids=set(args.complex_case_id) if args.complex_case_id else None, expanded_sequence_ids=set(args.expanded_sequence_id) if args.expanded_sequence_id else None, include_legacy_multi_turn=not args.skip_legacy_multi_turn))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json": str(args.output_dir / "report.json"), "report_markdown": str(args.output_dir / "report.md")}, ensure_ascii=False))


if __name__ == "__main__": main()
