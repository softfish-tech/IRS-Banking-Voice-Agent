"""LLM rendering is optional and cannot alter the C-approved answer route."""

import unittest

from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.providers import MockLLMClient
from banking_agent.app.response_generator import GroundedResponseGenerator
from banking_agent.schemas import AgentState


class AnswerModules:
    async def analyze(self, session_id, user_text):
        return {"status": "ok", "data": {"intent": "policy_enquiry", "confidence": 0.9, "risk_level": "LOW", "entities": []}}

    async def retrieve(self, query, top_k):
        return {"status": "ok", "data": {"docs": [{"document_id": "policy-1", "title": "Synthetic fees", "source": "Test", "score": 0.9, "excerpt": "The synthetic replacement fee is SGD 10."}]}}

    async def decide(self, state):
        return {"status": "ok", "data": {"action": "ANSWER", "reason_code": "POLICY_EVIDENCE_FOUND", "next_state": {}}}

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        raise AssertionError("D must not be called")


class LLMResponseOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_llm_wording_preserves_c_decision_and_sources(self) -> None:
        modules = AnswerModules()
        generator = GroundedResponseGenerator(
            MockLLMClient([{"answer": "The fee is SGD 10.", "citation_ids": ["policy-1"]}]),
            model="test-model",
        )
        response = await Orchestrator(
            modules, modules, modules, modules, response_generator=generator
        ).handle(AgentState(session_id="llm-answer", user_text="What is the fee?"))
        self.assertEqual(response.status, "ok")
        self.assertEqual(response.decision.action.value, "ANSWER")
        self.assertEqual(response.decision.reason_code, "POLICY_EVIDENCE_FOUND")
        self.assertEqual(response.text, "The fee is SGD 10.\n[Source: Synthetic fees; policy-1]")
        self.assertEqual([item.document_id for item in response.citations], ["policy-1"])

    async def test_bad_llm_output_uses_deterministic_evidence_fallback(self) -> None:
        modules = AnswerModules()
        generator = GroundedResponseGenerator(
            MockLLMClient([{"answer": "The fee is SGD 99.", "citation_ids": ["unknown"]}]),
            model="test-model",
        )
        response = await Orchestrator(
            modules, modules, modules, modules, response_generator=generator
        ).handle(AgentState(session_id="llm-fallback", user_text="What is the fee?"))
        self.assertIn("The synthetic replacement fee is SGD 10.", response.text)
        self.assertEqual(response.decision.reason_code, "POLICY_EVIDENCE_FOUND")
