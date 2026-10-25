"""Contract checks for the freeze-experiment aggregation helpers."""
import unittest
from types import SimpleNamespace

from banking_agent.schemas import Action, Decision, RiskLevel, UnderstandingResult
from scripts.run_single_turn_fuse_freeze import _pre_route_passed, _safety_violations, _summarize, _understanding_passed


class FreezeExperimentTests(unittest.TestCase):
    def test_understanding_allows_reviewed_alternatives(self) -> None:
        actual = UnderstandingResult(intent="UNKNOWN", confidence=0.8, risk_level=RiskLevel.UNKNOWN)
        self.assertTrue(_understanding_passed(actual, {"allowed": [{"intent": "UNKNOWN", "risk_level": "UNKNOWN"}]}))

    def test_pre_route_accepts_allowed_action_without_reason(self) -> None:
        decision = Decision(action=Action.ESCALATE, reason_code="RISK")
        self.assertTrue(_pre_route_passed(decision, {"allowed_actions": ["ANSWER", "ESCALATE"]}))

    def test_safety_records_answer_instead_of_clarify(self) -> None:
        pre_route = Decision(action=Action.ANSWER, reason_code="POLICY")
        trace = SimpleNamespace(modules=[])
        self.assertEqual(_safety_violations(pre_route, trace, {"action": "CLARIFY"}), ["unsafe_answer_instead_of_guarded_route"])

    def test_summary_reports_strict_and_downstream_semantic_metrics(self) -> None:
        row = {
            "case_id": "AOC-TEST", "split": "development", "family": "natural_variation",
            "status": "ok", "understanding_passed": False, "pre_route_passed": True,
            "safety_violations": [], "response_delivery": {"nonempty_text": True, "route_appropriate_evidence_shape": True},
            "semantic": {
                "passed": False, "outcome_passed": True, "response_passed": True,
                "grounding_passed": True, "checks": {"understanding": False, "decision": True},
            },
            "trace": {"duration_ms": 1, "complete": True}, "llm": None,
            "actual": {"intent": "policy_enquiry", "risk_level": "MEDIUM", "action": "ANSWER", "reason_code": "POLICY"},
        }

        summary = _summarize([row], repetitions=1)["overall"]

        self.assertEqual(summary["semantic_passed"], 0)
        self.assertEqual(summary["semantic_decision_passed"], 1)
        self.assertEqual(summary["semantic_outcome_passed"], 1)
        self.assertEqual(summary["semantic_response_passed"], 1)
        self.assertEqual(summary["semantic_grounding_passed"], 1)


if __name__ == "__main__":
    unittest.main()
