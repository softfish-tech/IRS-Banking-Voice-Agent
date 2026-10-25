"""Reproducible synthetic decision-matrix evaluation for Module C.

This is a focused regression benchmark, not an estimate of deployed banking
performance. It uses no personal data or network calls.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from banking_agent.schemas.enums import Action, RiskLevel
from banking_agent.schemas.state import AgentState, UnderstandingResult

from .engine import RuleEngine


DEFAULT_MATRIX = (
    Path(__file__).resolve().parents[4]
    / "tests/fixtures/rules/decision_matrix.json"
)


def _state(row: dict[str, object]) -> AgentState:
    return AgentState(
        session_id=f"synthetic-{row['id']}",
        user_text=row["text"],
        understanding=UnderstandingResult(
            intent=row["intent"],
            confidence=row["confidence"],
            risk_level=row["risk_level"],
        ),
        complaint_status=row.get("complaint_status", "NONE"),
        handoff_status=row.get("handoff_status", "NOT_REQUIRED"),
        consent=row.get("consent", "UNKNOWN"),
        retrieved_docs=row.get("docs", []),
    )


def _naive_route(state: AgentState) -> Action:
    """Teaching baseline: classifier risk, otherwise direct offer/answer."""

    if state.understanding.risk_level == RiskLevel.HIGH:
        return Action.ESCALATE
    if state.understanding.intent == "product_recommendation":
        return Action.RECOMMEND
    return Action.ANSWER


def evaluate_matrix(path: Path = DEFAULT_MATRIX) -> dict[str, object]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("decision matrix must be nonempty with unique IDs")
    engine = RuleEngine()
    counts: Counter[str] = Counter()
    failures: list[dict[str, str]] = []
    for row in rows:
        state = _state(row)
        action = engine.evaluate(state, rag_status=row.get("rag_status")).data
        baseline = _naive_route(state)
        expected = Action(row["expected_action"])
        tags = set(row.get("tags", []))
        counts["cases"] += 1
        counts["correct"] += action.action == expected and action.reason_code == row["expected_reason"]
        if action.action != expected or action.reason_code != row["expected_reason"]:
            failures.append({"id": row["id"], "action": action.action.value, "reason_code": action.reason_code})
        if "urgent" in tags:
            counts["urgent_cases"] += 1
            counts["urgent_escalated"] += action.action == Action.ESCALATE
            counts["baseline_urgent_escalated"] += baseline == Action.ESCALATE
        if "recommendation_denied" in tags:
            counts["denied_recommendation_cases"] += 1
            counts["recommendation_violations"] += action.action == Action.RECOMMEND
            counts["baseline_recommendation_violations"] += baseline == Action.RECOMMEND
        if "no_answer" in tags:
            counts["unsupported_cases"] += 1
            counts["unsupported_answers"] += action.action == Action.ANSWER
            counts["baseline_unsupported_answers"] += baseline == Action.ANSWER
    def ratio(num: str, den: str) -> float:
        return round(counts[num] / counts[den], 4) if counts[den] else 0.0
    return {
        "dataset": "synthetic C decision matrix",
        "cases": counts["cases"],
        "exact_decision_accuracy": ratio("correct", "cases"),
        "safe_escalation_rate": ratio("urgent_escalated", "urgent_cases"),
        "recommendation_violation_rate": ratio("recommendation_violations", "denied_recommendation_cases"),
        "unsupported_answer_rate": ratio("unsupported_answers", "unsupported_cases"),
        "baseline": {
            "safe_escalation_rate": ratio("baseline_urgent_escalated", "urgent_cases"),
            "recommendation_violation_rate": ratio("baseline_recommendation_violations", "denied_recommendation_cases"),
            "unsupported_answer_rate": ratio("baseline_unsupported_answers", "unsupported_cases"),
        },
        "denominators": {
            "urgent": counts["urgent_cases"],
            "recommendation_denied": counts["denied_recommendation_cases"],
            "unsupported": counts["unsupported_cases"],
        },
        "failures": failures,
    }


def main() -> int:
    report = evaluate_matrix()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
