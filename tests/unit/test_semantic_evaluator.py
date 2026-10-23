"""Unit coverage for semantic checks added beyond the original core scorecard."""

from types import SimpleNamespace
import unittest

from banking_agent.schemas import Action, AgentState, Decision, RiskLevel, UnderstandingResult
from scripts.evaluate_real_llm_e2e import (
    ResponseAssessment,
    _context_oracle_result,
    _extract_json_object,
    _normalize_response_assessment,
    _redact_evaluation_text,
    _semantic_result,
    apply_semantic_response_assessment,
)


class SemanticEvaluatorTests(unittest.TestCase):
    def test_context_oracle_requires_route_and_declared_resolution(self) -> None:
        row = {
            "actual": {"status": "ok", "action": "CLARIFY", "reason_code": "REPLACEMENT_REASON_REQUIRED"},
            "context_contract": {"reference_resolved": True, "resolved_query_used": True},
        }
        result = _context_oracle_result(
            row,
            {"action": "CLARIFY", "reason_code": "REPLACEMENT_REASON_REQUIRED", "resolution": "required"},
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["category"], "CONTEXT_PASS")

        row["context_contract"]["reference_resolved"] = False
        result = _context_oracle_result(
            row,
            {"action": "CLARIFY", "reason_code": "REPLACEMENT_REASON_REQUIRED", "resolution": "required"},
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["category"], "CONTEXT_GAP")

    def test_allowed_reason_code_is_accepted(self) -> None:
        state = AgentState(
            session_id="semantic-test",
            user_text="I need help with it.",
            understanding=UnderstandingResult(intent="UNKNOWN", confidence=0.9, risk_level=RiskLevel.LOW),
            decision=Decision(action=Action.CLARIFY, reason_code="UNKNOWN_INTENT"),
        )
        response = SimpleNamespace(state=state, decision=state.decision, text="Could you clarify what you need?", recommendations=[])
        trace = SimpleNamespace(retrieved_document_ids=(), modules=(SimpleNamespace(module="A"), SimpleNamespace(module="C")))
        gold = {"case_id": "SEM-TEST", "source_case_id": "E2E-TEST", "review_status": "confirmed_scenario_rule", "decision": {"action": "CLARIFY", "reason_code": "LOW_INTENT_CONFIDENCE", "allowed_reason_codes": ["UNKNOWN_INTENT"]}}
        self.assertTrue(_semantic_result(gold, response, trace)["checks"]["decision"])
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

    def test_outcome_metric_separates_understanding_from_downstream_success(self) -> None:
        state = AgentState(
            session_id="semantic-test",
            user_text="What is the policy?",
            understanding=UnderstandingResult(intent="policy_enquiry", confidence=0.9, risk_level=RiskLevel.MEDIUM),
            decision=Decision(action=Action.ANSWER, reason_code="POLICY_EVIDENCE_FOUND"),
        )
        response = SimpleNamespace(
            state=state,
            decision=state.decision,
            text="Cryptocurrency is unsupported.",
            recommendations=[],
        )
        trace = SimpleNamespace(
            retrieved_document_ids=("NB-v1_1-fiat_currency_support-001",),
            modules=(SimpleNamespace(module="A"), SimpleNamespace(module="C"), SimpleNamespace(module="B")),
        )
        gold = {
            "case_id": "SEM-TEST",
            "source_case_id": "E2E-TEST",
            "review_status": "confirmed_corpus",
            "understanding": {"intent": "policy_enquiry", "risk_level": "LOW"},
            "decision": {"action": "ANSWER", "reason_code": "POLICY_EVIDENCE_FOUND"},
            "retrieval": {"required_document_ids": ["NB-v1_1-fiat_currency_support-001"]},
            "response": {"required_facts": ["cryptocurrency is unsupported"]},
        }

        result = _semantic_result(gold, response, trace)

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["understanding"])
        self.assertTrue(result["outcome_passed"])
        self.assertTrue(result["response_passed"])
        self.assertTrue(result["grounding_passed"])

    def test_semantic_response_judge_replaces_only_final_answer_gates(self) -> None:
        state = AgentState(
            session_id="semantic-test",
            user_text="How much is a lost-card replacement?",
            understanding=UnderstandingResult(intent="card_fee_enquiry", confidence=0.9, risk_level=RiskLevel.LOW),
            decision=Decision(action=Action.ANSWER, reason_code="POLICY_EVIDENCE_FOUND"),
        )
        response = SimpleNamespace(
            state=state,
            decision=state.decision,
            text="A lost-card replacement is SGD 15.",
            recommendations=[],
        )
        trace = SimpleNamespace(
            retrieved_document_ids=("NB-v1_1-lost_or_stolen_card-002",),
            modules=(SimpleNamespace(module="A"), SimpleNamespace(module="C"), SimpleNamespace(module="B")),
        )
        gold = {
            "case_id": "SEM-TEST",
            "source_case_id": "E2E-TEST",
            "review_status": "confirmed_corpus",
            "decision": {"action": "ANSWER", "reason_code": "POLICY_EVIDENCE_FOUND"},
            "retrieval": {"required_document_ids": ["NB-v1_1-lost_or_stolen_card-002"]},
            "response": {"required_fact_groups": [{"id": "lost_card_fee", "any_of": ["SGD 15"]}]},
        }
        result = _semantic_result(gold, response, trace)

        judged = apply_semantic_response_assessment(
            result,
            ResponseAssessment(
                required_facts={"lost_card_fee": False},
                safety_passed=True,
            ),
            {"status": "ok", "attempts": 1, "prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
        )

        self.assertTrue(judged["checks"]["decision"])
        self.assertTrue(judged["checks"]["retrieval"])
        self.assertTrue(judged["checks"]["response_lexical_facts"])
        self.assertFalse(judged["checks"]["response_facts"])
        self.assertFalse(judged["response_passed"])
        self.assertFalse(judged["passed"])

    def test_unavailable_response_judge_is_not_silently_scored_by_regex(self) -> None:
        result = {
            "checks": {"response_facts": True},
            "outcome_passed": True,
            "response_passed": True,
            "grounding_passed": None,
            "passed": True,
        }

        judged = apply_semantic_response_assessment(
            result,
            None,
            {"status": "unavailable", "attempts": 1, "prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
        )

        self.assertTrue(judged["checks"]["response_lexical_facts"])
        self.assertIsNone(judged["response_passed"])
        self.assertFalse(judged["passed"])

    def test_response_evaluator_redacts_credential_values_before_provider_call(self) -> None:
        self.assertEqual(
            _redact_evaluation_text("My PIN is 1234; please help."),
            "My credential is [REDACTED]; please help.",
        )

    def test_response_evaluator_normalizes_legacy_fact_list(self) -> None:
        assessment, error = _normalize_response_assessment(
            {
                "facts": [{"fact_id": "Delivery_Time", "passed": "yes"}],
                "safe": "true",
            },
            expected_fact_ids={"delivery_time"},
            safety_required=True,
        )
        self.assertEqual(error, "")
        self.assertEqual(assessment.required_facts, {"delivery_time": True})
        self.assertTrue(assessment.safety_passed)

    def test_response_evaluator_extracts_json_from_code_fence(self) -> None:
        self.assertEqual(
            _extract_json_object("Here is the verdict:\n```json\n{\"safety_passed\": true}\n```"),
            {"safety_passed": True},
        )


if __name__ == "__main__":
    unittest.main()
