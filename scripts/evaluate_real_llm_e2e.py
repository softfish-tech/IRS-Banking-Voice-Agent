"""Evaluate all maintained synthetic E2E fixtures through real A/B/C/D plus typed LLM help.

This is an evaluation harness, not a CI test: it intentionally reports semantic
and evidence gaps in owner modules instead of treating them as an orchestrator
failure.  Output is privacy-minimised: case identifiers and state/action facts
only; it never writes prompts, customer text, provider output, or credentials.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from collections import Counter
from pathlib import Path

from banking_agent.app.llm_agent_support import FusedIntentModule, LLMTextAssistant, LLMUnderstanding
from banking_agent.app.local_env import load_local_env
from banking_agent.app.observability import DecisionTrace, TraceContext
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.providers import LLMSettings, create_llm_client
from banking_agent.app.response_generator import GroundedResponseGenerator
from banking_agent.app.retrieval_adapter import AsyncRetrievalAdapter
from banking_agent.modules.intent import EncoderIntentClassifier, IntentModuleAdapter
from banking_agent.modules.rag.retriever import create_retriever
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture
from banking_agent.modules.rules import RuleEngine
from banking_agent.schemas import Action, AgentState


ROOT = Path(__file__).resolve().parents[1]
SINGLE_TURN_ROOT = ROOT / "tests/e2e/single_turn"
MULTI_TURN_ROOT = ROOT / "tests/e2e/multi_turn"
SEMANTIC_SCORECARD = ROOT / "tests/fixtures/evaluation/semantic/v1/single_turn.json"


class DeterministicReranker:
    """Keep E2E comparisons repeatable while exercising B's real retriever."""

    def rerank(self, query, candidates, top_k=5):
        return [dict(item, score=float(top_k - index)) for index, item in enumerate(candidates[:top_k])]


class TraceCollector:
    def __init__(self) -> None:
        self.traces: list[DecisionTrace] = []

    def record_trace(self, trace: DecisionTrace) -> None:
        self.traces.append(trace)


def _load_cases() -> list[dict]:
    return [
        case
        for path in sorted(SINGLE_TURN_ROOT.glob("*.json"))
        for case in json.loads(path.read_text(encoding="utf-8"))["cases"]
    ]


def _load_semantic_scorecard() -> dict[str, dict]:
    scorecards = []
    for path in sorted(SEMANTIC_SCORECARD.parent.glob("single_turn*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "semantic-eval-v1":
            raise RuntimeError(f"unsupported_semantic_scorecard:{path.name}")
        scorecards.extend(payload["cases"])
    result = {case["source_case_id"]: case for case in scorecards}
    if len(result) != len(scorecards):
        raise RuntimeError("duplicate_semantic_source_case_id")
    return result


def _matches_fact_group(text: str, group: dict) -> bool:
    """Match one reviewed fact through any approved, case-insensitive pattern."""
    patterns = group.get("any_of", [])
    if not isinstance(patterns, list) or not patterns:
        raise ValueError("semantic_fact_group_requires_any_of")
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def _semantic_result(gold: dict, response, trace: DecisionTrace) -> dict:
    """Score reviewed semantic constraints without writing answer text to disk."""
    understanding = gold.get("understanding")
    decision = gold.get("decision", {})
    actual_action = response.decision.action.value if response.decision else None
    actual_reason = response.decision.reason_code if response.decision else None
    retrieval = gold.get("retrieval", {})
    recommendation = gold.get("recommendation", {})
    required_docs = retrieval.get("required_document_ids")
    candidate_docs = retrieval.get("candidate_document_ids")
    forbidden_docs = retrieval.get("forbidden_document_ids")
    selected_document_count = retrieval.get("selected_document_count")
    required_products = recommendation.get("required_product_ids")
    actual_products = [item.product_id for item in response.recommendations]
    text = response.text.casefold()
    response_gold = gold.get("response", {})
    required_groups = response_gold.get("required_fact_groups")
    if required_groups is None:
        required_groups = [
            {"id": fact, "any_of": [re.escape(fact)]}
            for fact in response_gold.get("required_facts", [])
        ]
    forbidden_patterns = response_gold.get("forbidden_patterns")
    if forbidden_patterns is None:
        forbidden_patterns = [re.escape(fact) for fact in response_gold.get("forbidden_facts", [])]

    checks: dict[str, bool] = {}
    if understanding is not None:
        allowed = understanding.get("allowed", [understanding])
        checks["understanding"] = any(
            response.state.understanding.intent == expected["intent"]
            and response.state.understanding.risk_level.value == expected["risk_level"]
            for expected in allowed
        )
    if decision:
        checks["decision"] = (
            actual_action == decision.get("action", actual_action)
            and actual_action in decision.get("allowed_actions", [actual_action])
            and (decision.get("reason_code") is None or actual_reason == decision["reason_code"])
        )
        required_state = decision.get("required_state")
        if required_state is not None:
            checks["state"] = all(
                getattr(response.state, field).value == value
                for field, value in required_state.items()
            )
    if required_docs is not None:
        checks["retrieval"] = all(
            document_id in trace.retrieved_document_ids for document_id in required_docs
        )
    if candidate_docs is not None:
        checks["candidate_retrieval"] = all(
            document_id in trace.retrieved_document_ids for document_id in candidate_docs
        )
    if forbidden_docs is not None:
        checks["retrieval_safety"] = not any(
            document_id in trace.retrieved_document_ids for document_id in forbidden_docs
        )
    if selected_document_count is not None:
        checks["selected_evidence"] = len(trace.retrieved_document_ids) == selected_document_count
    if required_products is not None:
        checks["recommendation"] = actual_products == required_products
    called_modules = {event.module for event in trace.modules}
    call_constraints = (
        ("B", retrieval.get("must_call_b"), retrieval.get("must_not_call_b")),
        ("D", recommendation.get("must_call_d"), recommendation.get("must_not_call_d")),
    )
    if any(must_call is not None or must_not_call is not None for _, must_call, must_not_call in call_constraints):
        checks["module_calls"] = all(
            (must_call is None or (module in called_modules) == must_call)
            and (must_not_call is None or (module not in called_modules) == must_not_call)
            for module, must_call, must_not_call in call_constraints
        )
    if required_groups:
        checks["response_facts"] = all(_matches_fact_group(text, group) for group in required_groups)
    if forbidden_patterns:
        checks["response_safety"] = not any(
            re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            for pattern in forbidden_patterns
        )
    pending_implementation = gold["review_status"].endswith("pending_c_evidence_rule")
    scored_checks = [passed for name, passed in checks.items() if name != "candidate_retrieval"]
    # Candidate retrieval is diagnostic only: it becomes a required document
    # once the C-owned unsupported-service evidence rule is implemented.
    return {
        "case_id": gold["case_id"],
        "source_case_id": gold["source_case_id"],
        "review_status": gold["review_status"],
        "pending_implementation": pending_implementation,
        "checks": checks,
        "passed": bool(scored_checks) and all(scored_checks),
    }


def _trace_complete(trace: DecisionTrace, response) -> bool:
    """Check required trace fields independently from scenario correctness."""
    required = (
        trace.request_id and trace.session_id and trace.modules and trace.risk_level
        and trace.complaint_status_before and trace.handoff_status_before
        and trace.result_status == response.status
    )
    if response.decision:
        required = required and trace.action == response.decision.action.value and trace.reason_code == response.decision.reason_code
    return bool(required)


def _module_call_order_matches(trace: DecisionTrace, expected: dict) -> bool:
    expected_core = expected.get("module_call_order", [])
    actual_core = [event.module for event in trace.modules if event.module in {"A", "B", "C", "D"}]
    return actual_core == expected_core


def _category(expected: dict, response, trace: DecisionTrace) -> str:
    if response.status == "error":
        return "TECHNICAL_FAILURE"
    if expected["status"] == "error":
        return "NOT_APPLICABLE_TECHNICAL_FIXTURE"
    actual = response.decision.action.value if response.decision else None
    reason = response.decision.reason_code if response.decision else None
    expected_reason = expected.get("reason_code")
    if (
        response.status == expected["status"]
        and actual == expected.get("action")
        and (expected_reason is None or reason == expected_reason)
    ):
        return "PASS"
    if expected.get("action") == "ESCALATE" and actual != "ESCALATE":
        return "SAFETY_FAILURE"
    if expected.get("action") in {"BLOCK", "CLARIFY", "ABSTAIN"} and actual == "ANSWER":
        return "SAFETY_FAILURE"
    core_modules = [event.module for event in trace.modules if event.module in {"A", "B", "C", "D"}]
    if expected.get("action") == "BLOCK" and "D" in core_modules:
        return "SAFETY_FAILURE"
    if actual == "ABSTAIN" and expected.get("action") == "ANSWER":
        return "EVIDENCE_GAP"
    return "SEMANTIC_GAP"


def _row(case_id: str, expected: dict, response, trace: DecisionTrace, *, sequence_id: str | None = None) -> dict:
    return {
        "case_id": case_id,
        "sequence_id": sequence_id,
        "expected": {"status": expected["status"], "action": expected.get("action"), "reason_code": expected.get("reason_code")},
        "actual": {
            "status": response.status,
            "action": response.decision.action.value if response.decision else None,
            "reason_code": response.decision.reason_code if response.decision else None,
        },
        "category": _category(expected, response, trace),
        "trace_complete": _trace_complete(trace, response),
        "module_call_order_matches": _module_call_order_matches(trace, expected),
        "duration_ms": trace.duration_ms,
        "modules": [
            {
                "module": event.module,
                "status": event.status,
                "duration_ms": event.duration_ms,
                "attempts": event.attempts,
                "prompt_tokens": event.prompt_tokens,
                "completion_tokens": event.completion_tokens,
                "total_tokens": event.total_tokens,
            }
            for event in trace.modules
        ],
        "retrieved_document_ids": list(trace.retrieved_document_ids),
    }


def _components(model: str, *, experimental_middle_loop: bool):
    client = create_llm_client(LLMSettings.from_environment())
    classifier = EncoderIntentClassifier.from_pretrained()
    baseline_intent = IntentModuleAdapter(classifier=classifier.classify)
    intent = (
        FusedIntentModule(baseline_intent, LLMUnderstanding(client, model=model))
        if experimental_middle_loop
        else baseline_intent
    )
    retrieval = AsyncRetrievalAdapter(create_retriever("real", reranker=DeterministicReranker()))
    recommendation = RecommendationAdapter(load_fixture(ROOT / "data/fixtures/recommendation.json"))
    assistant = LLMTextAssistant(client, model=model)
    response_generator = GroundedResponseGenerator(client, model=model)
    return (
        intent,
        retrieval,
        RuleEngine(),
        recommendation,
        assistant if experimental_middle_loop else None,
        assistant,
        response_generator,
    )


async def _run_turn(
    components, state: AgentState, request_id: str, scenario_id: str | None, *, progress_label: str
):
    collector = TraceCollector()
    intent, retrieval, rules, recommendation, query_rewriter, clarification_generator, response_generator = components
    task = asyncio.create_task(Orchestrator(
        intent, retrieval, rules, recommendation,
        trace_sink=collector,
        trace_context=TraceContext(mode="real_llm_evaluation", scenario_id=scenario_id),
        query_rewriter=query_rewriter,
        clarification_generator=clarification_generator,
        response_generator=response_generator,
    ).handle(state, request_id=request_id))
    elapsed_seconds = 0
    while not task.done():
        done, _ = await asyncio.wait({task}, timeout=10)
        if not done:
            elapsed_seconds += 10
            print(f"[{progress_label}] still running after {elapsed_seconds}s (waiting for module or LLM response)", flush=True)
    response = await task
    if len(collector.traces) != 1:
        raise RuntimeError("expected_one_sanitized_trace_per_turn")
    return response, collector.traces[0]


async def evaluate(
    include_multi_turn: bool,
    case_limit: int | None = None,
    case_ids: set[str] | None = None,
    *,
    experimental_middle_loop: bool = False,
) -> dict:
    load_local_env()
    model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
    if not model:
        raise SystemExit("BANKING_AGENT_LLM_MODEL_required")
    components = _components(model, experimental_middle_loop=experimental_middle_loop)
    rows: list[dict] = []
    semantic_gold = _load_semantic_scorecard()
    semantic_rows: list[dict] = []
    cases = _load_cases()
    if case_ids is not None:
        cases = [case for case in cases if case["case_id"] in case_ids]
        missing = case_ids - {case["case_id"] for case in cases}
        if missing:
            raise ValueError(f"unknown_case_ids:{','.join(sorted(missing))}")
    if case_limit is not None:
        cases = cases[:case_limit]
    total_cases = len(cases)
    for index, case in enumerate(cases, start=1):
        print(f"[single {index}/{total_cases}] start {case['case_id']}", flush=True)
        response, trace = await _run_turn(
            components,
            AgentState(**case["input"], **case["initial_state"]),
            f"real-llm-e2e-{case['case_id']}",
            case.get("scenario_id"),
            progress_label=f"single {index}/{total_cases} {case['case_id']}",
        )
        row = _row(case["case_id"], case["expected"], response, trace)
        rows.append(row)
        print(
            f"[single {index}/{total_cases}] {row['category']} "
            f"actual={row['actual']['action']}/{row['actual']['reason_code']} "
            f"latency_ms={row['duration_ms']}",
            flush=True,
        )
        if case["case_id"] in semantic_gold:
            semantic_rows.append(_semantic_result(semantic_gold[case["case_id"]], response, trace))

    multi_turn_note = "not_run"
    if include_multi_turn and case_limit is None:
        multi_turn_note = "semantic_context_is_not_implemented; turns are independently evaluated with business state carried forward"
        for path in sorted(MULTI_TURN_ROOT.glob("**/*.json")):
            sequence = json.loads(path.read_text(encoding="utf-8"))
            current = dict(sequence["initial_state"])
            for turn in sequence["turns"]:
                print(f"[multi {sequence['sequence_id']} turn {turn['turn_id']}] start", flush=True)
                response, trace = await _run_turn(
                    components,
                    AgentState(session_id=sequence["sequence_id"], user_text=turn["user_text"], **current),
                    f"real-llm-e2e-{sequence['sequence_id']}-{turn['turn_id']}",
                    sequence["sequence_id"],
                    progress_label=f"multi {sequence['sequence_id']} turn {turn['turn_id']}",
                )
                row = _row(turn["turn_id"], turn["expected"], response, trace, sequence_id=sequence["sequence_id"])
                if sequence["type"] == "semantic_context" and turn["turn_id"] > 1:
                    row["context_contract"] = "NOT_IMPLEMENTED"
                rows.append(row)
                print(
                    f"[multi {sequence['sequence_id']} turn {turn['turn_id']}] "
                    f"{row['category']} actual={row['actual']['action']}/{row['actual']['reason_code']} "
                    f"latency_ms={row['duration_ms']}",
                    flush=True,
                )
                current = {
                    "complaint_status": response.state.complaint_status.value,
                    "handoff_status": response.state.handoff_status.value,
                    "consent": response.state.consent.value,
                }

    categories = Counter(row["category"] for row in rows)
    llm_events = Counter(
        f"{event['module']}:{event['status']}"
        for row in rows for event in row["modules"] if event["module"].startswith("E.LLM.")
    )
    def percentile(values: list[int], percentage: int) -> int | None:
        if not values:
            return None
        ordered = sorted(values)
        index = round((len(ordered) - 1) * percentage / 100)
        return ordered[index]

    request_durations = [row["duration_ms"] for row in rows]
    llm_rows = [
        event for row in rows for event in row["modules"]
        if event["module"].startswith("E.LLM.")
    ]
    total_tokens = sum(event["total_tokens"] or 0 for event in llm_rows)
    known_token_events = sum(event["total_tokens"] is not None for event in llm_rows)
    fallback_count = sum(event["status"] == "fallback" for event in llm_rows)
    scorable_semantic = [row for row in semantic_rows if not row["pending_implementation"]]
    semantic_check_summary = {
        name: {
            "passed": sum(row["checks"].get(name, False) for row in scorable_semantic),
            "scored": sum(name in row["checks"] for row in scorable_semantic),
        }
        for name in sorted({name for row in scorable_semantic for name in row["checks"]})
    }
    return {
        "evaluation": "real A/B/C/D plus constrained DeepSeek assistance",
        "experimental_middle_loop": experimental_middle_loop,
        "fixture_counts": {"single_turn": len(cases), "total_turns": len(rows)},
        "multi_turn_note": multi_turn_note,
        "summary": dict(sorted(categories.items())),
        "trace_coverage": {
            "complete": sum(row["trace_complete"] for row in rows),
            "total": len(rows),
            "module_call_order_matches_expected_fixture": sum(row["module_call_order_matches"] for row in rows),
            "llm_events": dict(sorted(llm_events.items())),
        },
        "performance": {
            "request_latency_ms": {"count": len(request_durations), "mean": round(sum(request_durations) / len(request_durations)) if request_durations else None, "p50": percentile(request_durations, 50), "p95": percentile(request_durations, 95)},
            "llm": {
                "calls": len(llm_rows),
                "fallbacks": fallback_count,
                "fallback_rate": round(fallback_count / len(llm_rows), 4) if llm_rows else None,
                "attempts": sum(event["attempts"] or 0 for event in llm_rows),
                "latency_ms": {"mean": round(sum(event["duration_ms"] for event in llm_rows) / len(llm_rows)) if llm_rows else None, "p50": percentile([event["duration_ms"] for event in llm_rows], 50), "p95": percentile([event["duration_ms"] for event in llm_rows], 95)},
                "tokens": {"total": total_tokens if known_token_events else None, "events_with_usage": known_token_events, "calls": len(llm_rows)},
                "ttft_ms": None,
                "ttft_note": "not_available_non_streaming_transport",
            },
        },
        "semantic_evaluation": {
            "scorecard_cases_seen": len(semantic_rows),
            "scorable_cases": len(scorable_semantic),
            "passed_cases": sum(row["passed"] for row in scorable_semantic),
            "pending_implementation_cases": sum(row["pending_implementation"] for row in semantic_rows),
            "check_summary": semantic_check_summary,
            "rows": semantic_rows,
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-multi-turn",
        action="store_true",
        help="Also run the 16 multi-turn fixtures (stateful only; semantic context is not implemented).",
    )
    parser.add_argument(
        "--experimental-middle-loop",
        action="store_true",
        help="Allow LLM intent fusion and retrieval-query rewriting; disabled for the delivery profile.",
    )
    parser.add_argument("--limit", type=int, help="Run only the first N single-turn cases (smoke check).")
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        metavar="ID",
        help="Run a named single-turn case; repeat the option to select several.",
    )
    parser.add_argument("--output", type=Path, help="Write sanitized JSON report to this path.")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.limit is not None and args.case_ids:
        parser.error("--limit and --case-id cannot be combined")
    if args.include_multi_turn and args.case_ids:
        parser.error("--include-multi-turn and --case-id cannot be combined")
    report = asyncio.run(
        evaluate(
            include_multi_turn=args.include_multi_turn,
            case_limit=args.limit,
            case_ids=set(args.case_ids) if args.case_ids else None,
            experimental_middle_loop=args.experimental_middle_loop,
        )
    )
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
