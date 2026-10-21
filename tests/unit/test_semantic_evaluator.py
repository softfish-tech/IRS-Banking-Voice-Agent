"""Unit coverage for semantic checks added beyond the original core scorecard."""

from types import SimpleNamespace
import unittest

from banking_agent.schemas import Action, AgentState, Decision, RiskLevel, UnderstandingResult
from scripts.evaluate_real_llm_e2e import _semantic_result


class SemanticEvaluatorTests(unittest.TestCase):
    def test_rag_boundary_requires_b_but_rejects_ambiguous_candidate(self) -> None:
        state = AgentState(
            session_id="semantic-test",
            user_text="What is the replacement fee for my card?",
            understanding=UnderstandingResult(intent="card_fee_enquiry", confidence=0.9, risk_level=RiskLevel.LOW),
            decision=Decision(action=Action.CLARIFY, reason_code="REPLACEMENT_REASON_REQUIRED"),
        )
        response = SimpleNamespace(
            state=state,
            decision=state.decision,
            text="Could you clarify why the card needs replacing?",
            recommendations=[],
        )
        trace = SimpleNamespace(
            retrieved_document_ids=(),
            modules=(SimpleNamespace(module="A"), SimpleNamespace(module="C"), SimpleNamespace(module="B"), SimpleNamespace(module="C")),
        )
        gold = {
            "case_id": "SEM-TEST",
            "source_case_id": "E2E-TEST",
            "review_status": "confirmed_scenario_rule",
            "decision": {"action": "CLARIFY", "reason_code": "REPLACEMENT_REASON_REQUIRED"},
            "retrieval": {
                "must_call_b": True,
                "selected_document_count": 0,
                "forbidden_document_ids": ["NB-v1_1-lost_or_stolen_card-002"],
            },
        }

        result = _semantic_result(gold, response, trace)

        self.assertTrue(result["passed"])
        self.assertTrue(result["checks"]["module_calls"])
        self.assertTrue(result["checks"]["selected_evidence"])
        self.assertTrue(result["checks"]["retrieval_safety"])

    def test_recommendation_module_call_is_enforced(self) -> None:
        state = AgentState(
            session_id="semantic-test",
            user_text="Recommend a savings product.",
            understanding=UnderstandingResult(intent="product_recommendation", confidence=0.9, risk_level=RiskLevel.LOW),
            decision=Decision(action=Action.RECOMMEND, reason_code="RECOMMENDATION_PERMITTED"),
        )
        response = SimpleNamespace(state=state, decision=state.decision, text="No eligible recommendation is available.", recommendations=[])
        trace = SimpleNamespace(retrieved_document_ids=(), modules=(SimpleNamespace(module="A"), SimpleNamespace(module="C")))
        gold = {
            "case_id": "SEM-TEST",
            "source_case_id": "E2E-TEST",
            "review_status": "confirmed_d_fixture",
            "recommendation": {"must_call_d": True, "required_product_ids": []},
        }

        result = _semantic_result(gold, response, trace)

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["module_calls"])


if __name__ == "__main__":
    unittest.main()
