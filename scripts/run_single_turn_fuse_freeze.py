"""Run the repeatable full-agent single-turn fuse-freeze acceptance experiment.

The experiment executes the 36-case development fixture and the disjoint
12-case holdout fixture through the full real A/B/C/D orchestrator.  Fuse is
the primary system under test; ``--with-a-only`` adds a paired A-only reference
run. Reports contain case IDs and structured outcomes only by default. The
explicit ``--record-response-text`` option is limited to reviewed synthetic
experiments that need later final-answer re-scoring.

The complex-language inputs are paired with reviewed semantic overlays for
final C route, B evidence, D output and response facts. The report therefore
scores these end-to-end checks without storing raw user text or responses.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from banking_agent.app.local_env import load_local_env
from banking_agent.app.providers import LLMSettings, create_llm_client
from banking_agent.modules.rules import RuleEngine
from banking_agent.schemas import AgentState, UnderstandingResult
try:  # Direct ``python scripts/...`` execution and test-package imports differ.
    from scripts.evaluate_real_llm_e2e import (
        ROOT, SemanticResponseEvaluator, _components, _run_turn,
        _semantic_result, apply_semantic_response_assessment,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised by the CLI smoke check
    from evaluate_real_llm_e2e import (
        ROOT, SemanticResponseEvaluator, _components, _run_turn,
        _semantic_result, apply_semantic_response_assessment,
    )


DEVELOPMENT = ROOT / "tests/fixtures/evaluation/a_only_complex/v1/development.json"
HOLDOUT = ROOT / "tests/fixtures/evaluation/a_only_complex/v1/holdout.json"
SEMANTIC_OVERLAYS = {
    "development": ROOT / "tests/fixtures/evaluation/semantic/v1/complex_language_development.json",
    "holdout": ROOT / "tests/fixtures/evaluation/semantic/v1/complex_language_holdout.json",
}


def _load_cases() -> list[dict]:
    cases: list[dict] = []
    for split, path in (("development", DEVELOPMENT), ("holdout", HOLDOUT)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "a-only-complex-v1":
            raise RuntimeError(f"unsupported_fixture:{path.name}")
        overlay = json.loads(SEMANTIC_OVERLAYS[split].read_text(encoding="utf-8"))
        if overlay.get("schema_version") != "complex-language-semantic-v1":
            raise RuntimeError(f"unsupported_semantic_overlay:{SEMANTIC_OVERLAYS[split].name}")
        annotations = {item["case_id"]: item for item in overlay["cases"]}
        source_ids = {case["case_id"] for case in payload["cases"]}
        if source_ids != set(annotations):
            raise RuntimeError(f"semantic_overlay_case_ids_mismatch:{split}")
        cases.extend({**case, "split": split, "semantic_gold": annotations[case["case_id"]]} for case in payload["cases"])
    if len(cases) != 48 or len({case["case_id"] for case in cases}) != 48:
        raise RuntimeError("freeze_fixture_must_contain_48_unique_cases")
    return cases


def _understanding_passed(actual: UnderstandingResult, gold: dict) -> bool:
    return any(
        actual.intent == expected["intent"] and actual.risk_level.value == expected["risk_level"]
        for expected in gold.get("allowed", [gold])
    )


def _pre_route_passed(decision, gold: dict) -> bool:
    if decision is None:
        return False
    action = decision.action.value
    return (
        action == gold.get("action", action)
        and action in gold.get("allowed_actions", [action])
        and (gold.get("reason_code") is None or decision.reason_code == gold["reason_code"])
    )


def _safety_violations(pre_route, trace, gold: dict) -> list[str]:
    """Report only explicit fixture safety boundary failures."""
    actual = pre_route.action.value if pre_route else None
    expected = gold.get("action")
    called = {event.module for event in trace.modules}
    violations: list[str] = []
    if expected == "ESCALATE" and actual != "ESCALATE":
        violations.append("missed_required_escalation")
    if expected in {"BLOCK", "CLARIFY", "ABSTAIN"} and actual == "ANSWER":
        violations.append("unsafe_answer_instead_of_guarded_route")
    if expected == "BLOCK" and "D" in called:
        violations.append("recommendation_called_on_block")
    return violations


def _response_delivery(response, trace) -> dict:
    """Measure observable delivery properties; this is not factual-text scoring."""
    action = response.decision.action.value if response.decision else None
    has_text = bool(response.text and response.text.strip())
    citations = len(response.citations)
    recommendations = len(response.recommendations)
    called = {event.module for event in trace.modules}
    if action == "ANSWER":
        grounded = citations > 0 and "B" in called
    else:
        grounded = citations == 0
    return {
        "nonempty_text": has_text,
        "citation_count": citations,
        "recommendation_count": recommendations,
        "route_appropriate_evidence_shape": grounded,
    }


def _percentile(values: list[int], percentage: int) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * percentage / 100)]


async def _attempt_row(
    case: dict,
    repeat: int,
    response,
    trace,
    *,
    response_evaluator: SemanticResponseEvaluator | None,
    record_response_text: bool,
) -> dict:
    pre_route_state = AgentState(
        session_id=case.get("session_id", f"freeze-{case['case_id']}"),
        user_text=case["input"], understanding=response.state.understanding, **case["state"],
    )
    from banking_agent.schemas import Decision
    pre_route = Decision.model_validate((await RuleEngine().decide(pre_route_state))["data"])
    trace_llm_events = [event for event in trace.modules if event.module.startswith("E.LLM.")]
    understanding_events = [event for event in trace_llm_events if event.module == "E.LLM.understanding"]
    llm = understanding_events[-1] if understanding_events else None
    violations = _safety_violations(pre_route, trace, case["decision"])
    semantic_gold = {
        **case["semantic_gold"],
        "source_case_id": case["case_id"],
        "understanding": case["understanding"],
    }
    semantic = _semantic_result(semantic_gold, response, trace)
    response_gold = semantic_gold.get("response", {})
    if response_evaluator is not None and response_gold:
        assessment, metadata = await response_evaluator.assess(
            question=case["input"],
            answer=response.text,
            response_gold=response_gold,
            request_id=f"freeze-response-eval-{repeat}-{case['case_id']}",
        )
        semantic = apply_semantic_response_assessment(semantic, assessment, metadata)
    row = {
        "case_id": case["case_id"],
        "split": case["split"],
        "family": case["family"],
        "repeat": repeat,
        "status": response.status,
        "understanding_passed": _understanding_passed(response.state.understanding, case["understanding"]),
        "pre_route_passed": _pre_route_passed(pre_route, case["decision"]),
        "pre_route": {"action": pre_route.action.value, "reason_code": pre_route.reason_code},
        "actual": {
            "intent": response.state.understanding.intent,
            "risk_level": response.state.understanding.risk_level.value,
            "confidence": response.state.understanding.confidence,
            "action": response.decision.action.value if response.decision else None,
            "reason_code": response.decision.reason_code if response.decision else None,
        },
        "safety_violations": violations,
        "semantic": semantic,
        "response_delivery": _response_delivery(response, trace),
        "trace": {
            "complete": bool(trace.request_id and trace.session_id and trace.modules),
            "duration_ms": trace.duration_ms,
            # Synthetic-evaluation provenance only: document IDs distinguish
            # a missing B candidate from evidence C later declined. No user
            # text, excerpts, prompts, or provider output is persisted.
            "retrieved_document_ids": list(trace.retrieved_document_ids),
            "modules": [
                {
                    "module": event.module,
                    "status": event.status,
                    "duration_ms": event.duration_ms,
                    "error_code": event.error_code,
                    "attempts": event.attempts,
                    "prompt_tokens": event.prompt_tokens,
                    "completion_tokens": event.completion_tokens,
                    "total_tokens": event.total_tokens,
                }
                for event in trace.modules
            ],
        },
        "llm": None if llm is None else {
            "status": llm.status,
            "disposition": llm.error_code,
            "duration_ms": llm.duration_ms,
            "attempts": llm.attempts,
            "prompt_tokens": llm.prompt_tokens,
            "completion_tokens": llm.completion_tokens,
            "total_tokens": llm.total_tokens,
        },
        "llm_events": [
            {
                "stage": event.module.removeprefix("E.LLM."),
                "status": event.status,
                "duration_ms": event.duration_ms,
                "attempts": event.attempts,
                "prompt_tokens": event.prompt_tokens,
                "completion_tokens": event.completion_tokens,
                "total_tokens": event.total_tokens,
            }
            for event in trace_llm_events
        ],
    }
    if record_response_text:
        row["final_response_text"] = response.text
    return row


def _summarize(rows: list[dict], repetitions: int) -> dict:
    by_case: dict[str, list[dict]] = defaultdict(list)
    by_split: dict[str, list[dict]] = defaultdict(list)
    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_case[row["case_id"]].append(row)
        by_split[row["split"]].append(row)
        by_family[row["family"]].append(row)

    def aggregate(items: list[dict]) -> dict:
        return {
            "attempts": len(items),
            "understanding_passed": sum(row["understanding_passed"] for row in items),
            # The semantic overlay is the reviewed business oracle. Keep the
            # source-fixture route result for A/fuse comparability only.
            "semantic_decision_passed": sum(
                row["semantic"]["checks"].get("decision", False) for row in items
            ),
            "pre_route_passed": sum(row["pre_route_passed"] for row in items),
            "technical_failures": sum(row["status"] != "ok" for row in items),
            "safety_violations": sum(len(row["safety_violations"]) for row in items),
            "nonempty_responses": sum(row["response_delivery"]["nonempty_text"] for row in items),
            "evidence_shape_passed": sum(row["response_delivery"]["route_appropriate_evidence_shape"] for row in items),
            "semantic_passed": sum(row["semantic"]["passed"] for row in items),
            "semantic_outcome_passed": sum(row["semantic"]["outcome_passed"] for row in items),
            "semantic_response_passed": sum(row["semantic"]["response_passed"] is True for row in items),
            "semantic_response_scored": sum(row["semantic"]["response_passed"] is not None for row in items),
            "semantic_grounding_passed": sum(row["semantic"]["grounding_passed"] is True for row in items),
            "semantic_grounding_scored": sum(row["semantic"]["grounding_passed"] is not None for row in items),
            "semantic_checks": {
                name: {"passed": sum(row["semantic"]["checks"].get(name, False) for row in items), "scored": sum(name in row["semantic"]["checks"] for row in items)}
                for name in sorted({name for row in items for name in row["semantic"]["checks"]})
            },
        }

    stability_rows = []
    for case_id, attempts in sorted(by_case.items()):
        if len(attempts) != repetitions:
            raise RuntimeError(f"incomplete_repetitions:{case_id}")
        signatures = {
            (row["status"], row["actual"]["intent"], row["actual"]["risk_level"], row["actual"]["action"], row["actual"]["reason_code"])
            for row in attempts
        }
        stability_rows.append({
            "case_id": case_id,
            "stable": len(signatures) == 1,
            "all_pre_route_passed": all(row["pre_route_passed"] for row in attempts),
            "all_semantic_decision_passed": all(
                row["semantic"]["checks"].get("decision", False) for row in attempts
            ),
            "all_understanding_passed": all(row["understanding_passed"] for row in attempts),
            "any_safety_violation": any(row["safety_violations"] for row in attempts),
            "signatures": [list(signature) for signature in sorted(signatures, key=str)],
        })
    durations = [row["trace"]["duration_ms"] for row in rows]
    llm_rows = [row["llm"] for row in rows if row["llm"] is not None]
    token_rows = [row for row in llm_rows if row["total_tokens"] is not None]
    llm_events = [event for row in rows for event in row.get("llm_events", [])]
    response_evaluations = [
        row["semantic"]["response_evaluation"]
        for row in rows if "response_evaluation" in row["semantic"]
    ]

    def llm_stage_summary(events: list[dict]) -> dict:
        token_events = [event for event in events if event["total_tokens"] is not None]
        return {
            "calls": len(events),
            "validated": sum(event["status"] == "ok" for event in events),
            "fallbacks": sum(event["status"] == "fallback" for event in events),
            "token_total": sum(event["total_tokens"] for event in token_events) if token_events else None,
            "token_events": len(token_events),
            "latency_ms": {
                "mean": round(mean(event["duration_ms"] for event in events)) if events else None,
                "p95": _percentile([event["duration_ms"] for event in events], 95),
            },
        }

    llm_by_stage = {
        stage: llm_stage_summary([event for event in llm_events if event["stage"] == stage])
        for stage in sorted({event["stage"] for event in llm_events})
    }
    return {
        "overall": aggregate(rows),
        "by_split": {name: aggregate(items) for name, items in sorted(by_split.items())},
        "by_family": {name: aggregate(items) for name, items in sorted(by_family.items())},
        "stability": {
            "cases": len(stability_rows),
            "stable_cases": sum(item["stable"] for item in stability_rows),
            "all_repeats_pre_route_passed": sum(item["all_pre_route_passed"] for item in stability_rows),
            "all_repeats_semantic_decision_passed": sum(item["all_semantic_decision_passed"] for item in stability_rows),
            "all_repeats_understanding_passed": sum(item["all_understanding_passed"] for item in stability_rows),
            "cases_with_any_safety_violation": sum(item["any_safety_violation"] for item in stability_rows),
            "rows": stability_rows,
        },
        "performance": {
            "request_latency_ms": {"mean": round(mean(durations)) if durations else None, "p50": _percentile(durations, 50), "p95": _percentile(durations, 95), "p99": _percentile(durations, 99)},
            "llm": {
                "calls": len(llm_rows),
                "validated_drafts": sum(row["status"] == "ok" for row in llm_rows),
                "fallbacks": sum(row["status"] == "fallback" for row in llm_rows),
                "fallback_rate": round(sum(row["status"] == "fallback" for row in llm_rows) / len(llm_rows), 4) if llm_rows else None,
                "tokens": {"total": sum(row["total_tokens"] for row in token_rows) if token_rows else None, "events_with_usage": len(token_rows), "mean_per_event": round(mean(row["total_tokens"] for row in token_rows)) if token_rows else None},
                "latency_ms": {"mean": round(mean(row["duration_ms"] for row in llm_rows)) if llm_rows else None, "p95": _percentile([row["duration_ms"] for row in llm_rows], 95)},
            },
            "llm_by_stage": llm_by_stage,
            "trace_complete": sum(row["trace"]["complete"] for row in rows),
        },
        "final_response_evaluation": {
            "method": "llm_semantic_v1" if response_evaluations else "lexical_regex_v1",
            "attempts": len(response_evaluations),
            "scored": sum(item["scored"] for item in response_evaluations),
            "unavailable_or_invalid": sum(not item["scored"] for item in response_evaluations),
            "tokens": {
                "total": sum(item["total_tokens"] or 0 for item in response_evaluations),
                "events_with_usage": sum(item["total_tokens"] is not None for item in response_evaluations),
            },
        },
    }


async def _run_mode(
    mode: str,
    cases: list[dict],
    repetitions: int,
    *,
    enable_query_rewrite: bool,
    semantic_response_evaluation: bool,
    record_response_text: bool,
) -> list[dict]:
    model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
    components = _components(
        model or None,
        understanding_mode=mode,
        full_llm_assistance=True,
        enable_query_rewrite=enable_query_rewrite,
    )
    response_evaluator = None
    if semantic_response_evaluation:
        evaluation_settings = LLMSettings.from_environment()
        response_evaluator = SemanticResponseEvaluator(
            create_llm_client(evaluation_settings), model=model, settings=evaluation_settings
        )
    rows: list[dict] = []
    total = len(cases) * repetitions
    index = 0
    for repeat in range(1, repetitions + 1):
        for case in cases:
            index += 1
            label = f"{mode} {index}/{total} {case['case_id']} run={repeat}"
            print(f"[{label}] start", flush=True)
            response, trace = await _run_turn(
                components,
                AgentState(session_id=case["semantic_gold"].get("evaluation_session_id", case.get("session_id", f"freeze-{mode}-{repeat}-{case['case_id']}")), user_text=case["input"], **case["state"]),
                f"freeze-{mode}-{repeat}-{case['case_id']}",
                case["case_id"],
                progress_label=label,
            )
            row = await _attempt_row(
                case,
                repeat,
                response,
                trace,
                response_evaluator=response_evaluator,
                record_response_text=record_response_text,
            )
            rows.append(row)
            print(f"[{label}] pre_route={row['pre_route_passed']} safety={len(row['safety_violations'])} latency_ms={trace.duration_ms}", flush=True)
    return rows


def _markdown(report: dict) -> str:
    counts = report["fixture_counts"]
    lines = ["# Single-turn fuse freeze report", "", f"Generated: {report['generated_at']}", "", f"Primary mode: `{report['primary_mode']}`; repetitions: {report['repetitions']}; fixtures: {counts['development']} development + {counts['holdout']} holdout.", ""]
    for mode, result in report["modes"].items():
        overall = result["summary"]["overall"]
        stability = result["summary"]["stability"]
        performance = result["summary"]["performance"]
        response_evaluation = result["summary"]["final_response_evaluation"]
        lines.extend([
            f"## {mode}", "",
            f"- Reviewed semantic C-decision pass: {overall['semantic_decision_passed']}/{overall['attempts']}; understanding pass: {overall['understanding_passed']}/{overall['attempts']}; strict semantic end-to-end pass: {overall['semantic_passed']}/{overall['attempts']}.",
            f"- Legacy source-fixture pre-retrieval route diagnostic: {overall['pre_route_passed']}/{overall['attempts']} (retained only for A/fuse comparison).",
            f"- Downstream outcome pass (C/B/D/response, excluding exact understanding): {overall['semantic_outcome_passed']}/{overall['attempts']}; response pass: {overall['semantic_response_passed']}/{overall['semantic_response_scored']}; evidence-grounding pass: {overall['semantic_grounding_passed']}/{overall['semantic_grounding_scored']}.",
            f"- Safety violations: {overall['safety_violations']}; technical failures: {overall['technical_failures']}.",
            f"- Stable cases: {stability['stable_cases']}/{stability['cases']}; all-three semantic-decision pass: {stability['all_repeats_semantic_decision_passed']}/{stability['cases']}; all-three legacy pre-route diagnostic pass: {stability['all_repeats_pre_route_passed']}/{stability['cases']}.",
            f"- Request latency: mean {performance['request_latency_ms']['mean']} ms, p95 {performance['request_latency_ms']['p95']} ms, p99 {performance['request_latency_ms']['p99']} ms.",
            f"- LLM: calls {performance['llm']['calls']}, fallbacks {performance['llm']['fallbacks']}, token total {performance['llm']['tokens']['total']} ({performance['llm']['tokens']['events_with_usage']} events with usage).",
            f"- Final-answer evaluator: {response_evaluation['method']}; scored {response_evaluation['scored']}/{response_evaluation['attempts']}; evaluator tokens {response_evaluation['tokens']['total']} ({response_evaluation['tokens']['events_with_usage']} events with usage).",
            "- LLM stages: " + "; ".join(
                f"{stage} calls {stats['calls']}, validated {stats['validated']}, "
                f"fallbacks {stats['fallbacks']}, tokens {stats['token_total']}, "
                f"p95 {stats['latency_ms']['p95']} ms"
                for stage, stats in performance["llm_by_stage"].items()
            ),
            "",
        ])
    lines.extend([
        "## Scope note", "",
        "This fixture set scores understanding, C route, safety boundaries, B evidence, D output, response facts and response safety through reviewed complex-language semantic overlays. The final-answer evaluator is separate from agent trace performance and token accounting.",
        "",
    ])
    return "\n".join(lines)


async def evaluate(
    *,
    repetitions: int = 3,
    with_a_only: bool = False,
    a_only_only: bool = False,
    enable_query_rewrite: bool = True,
    semantic_response_evaluation: bool = True,
    record_response_text: bool = False,
    case_ids: set[str] | None = None,
) -> dict:
    if repetitions <= 0:
        raise ValueError("repetitions_must_be_positive")
    load_local_env()
    cases = _load_cases()
    if case_ids is not None:
        cases = [case for case in cases if case["case_id"] in case_ids]
        missing = case_ids - {case["case_id"] for case in cases}
        if missing:
            raise ValueError(f"unknown_case_ids:{','.join(sorted(missing))}")
    if a_only_only and with_a_only:
        raise ValueError("a_only_only_cannot_be_combined_with_with_a_only")
    modes = {}
    if not a_only_only:
        modes["fuse"] = {
            "rows": await _run_mode(
                "fuse",
                cases,
                repetitions,
                enable_query_rewrite=enable_query_rewrite,
                semantic_response_evaluation=semantic_response_evaluation,
                record_response_text=record_response_text,
            )
        }
    if with_a_only or a_only_only:
        modes["a_only"] = {
            "rows": await _run_mode(
                "off",
                cases,
                repetitions,
                enable_query_rewrite=enable_query_rewrite,
                semantic_response_evaluation=semantic_response_evaluation,
                record_response_text=record_response_text,
            )
        }
    for result in modes.values():
        result["summary"] = _summarize(result["rows"], repetitions)
    return {
        "evaluation": "single_turn_fuse_freeze_v1",
        "agent_profile": {
            "understanding": "real_A_plus_fuse_or_a_only",
            "query_rewrite": "llm" if enable_query_rewrite else "disabled_for_ablation",
            "retrieval": "real_bm25_cross_encoder",
            "rules": "real_C",
            "recommendation": "real_D",
            "clarification": "llm_with_template_fallback",
            "answer": "llm_grounded_response_with_template_fallback",
        },
        "generated_at": datetime.now(UTC).isoformat(),
        "primary_mode": "a_only" if a_only_only else "fuse",
        "repetitions": repetitions,
        "fixture_counts": {
            "development": sum(case["split"] == "development" for case in cases),
            "holdout": sum(case["split"] == "holdout" for case in cases),
            "total_cases": len(cases),
        },
        "response_quality_scope": "reviewed_complex_language_semantic_overlays",
        "response_evaluator": "llm_semantic_v1" if semantic_response_evaluation else "lexical_regex_v1",
        "final_response_text_recording": "enabled" if record_response_text else "disabled",
        "modes": modes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=3, help="Runs per case and mode (default: 3).")
    parser.add_argument("--with-a-only", action="store_true", help="Also run the paired A-only/off reference experiment.")
    parser.add_argument(
        "--a-only-only",
        action="store_true",
        help="Run only the A-only path; useful for an isolated B/E ablation.",
    )
    parser.add_argument(
        "--lexical-response-evaluation",
        action="store_true",
        help="Use legacy regex-only final-answer scoring (diagnostic compatibility only).",
    )
    parser.add_argument(
        "--record-response-text",
        action="store_true",
        help="Write final response text into this local evaluation artifact for later re-scoring.",
    )
    parser.add_argument(
        "--disable-query-rewrite",
        action="store_true",
        help="Keep LLM clarification and grounded answers enabled, but send only original user text to B.",
    )
    parser.add_argument("--case-id", action="append", dest="case_ids", metavar="ID", help="Run a named complex-language case; repeat to select several.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/evaluation/single_turn_fuse_freeze", help="Directory for sanitized JSON and Markdown reports.")
    args = parser.parse_args()
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive")
    report = asyncio.run(evaluate(
        repetitions=args.repetitions,
        with_a_only=args.with_a_only,
        a_only_only=args.a_only_only,
        enable_query_rewrite=not args.disable_query_rewrite,
        semantic_response_evaluation=not args.lexical_response_evaluation,
        record_response_text=args.record_response_text,
        case_ids=set(args.case_ids) if args.case_ids else None,
    ))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "report.json"
    markdown_path = args.output_dir / "report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json": str(json_path), "report_markdown": str(markdown_path), "modes": list(report["modes"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
