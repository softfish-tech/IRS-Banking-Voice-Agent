"""LLM middle-loop proposals are typed and cannot weaken deterministic safety."""
import unittest

from banking_agent.app.llm_agent_support import FusedIntentModule, LLMTextAssistant, LLMUnderstanding
from banking_agent.app.providers import MockLLMClient
from banking_agent.schemas import Action, AgentState, Decision


class Baseline:
    def __init__(self, intent="policy_enquiry", confidence=0.6, risk="LOW"):
        self.intent, self.confidence, self.risk = intent, confidence, risk
    async def analyze(self, session_id, user_text):
        return {"status": "ok", "data": {"intent": self.intent, "confidence": self.confidence, "risk_level": self.risk, "entities": []}}


class LLMAgentSupportTests(unittest.IsolatedAsyncioTestCase):
    async def test_confident_draft_improves_ambiguous_policy_route(self):
        module = FusedIntentModule(
            Baseline(),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I was charged an unexplained fee")
        self.assertEqual(result["data"]["intent"], "fee_complaint")
        self.assertEqual(result["data"]["risk_level"], "MEDIUM")

    async def test_llm_cannot_lower_existing_high_risk(self):
        module = FusedIntentModule(
            Baseline("fraud_suspicion", 0.95, "HIGH"),
            LLMUnderstanding(MockLLMClient([{"intent": "policy_enquiry", "confidence": 0.99, "risk_level": "LOW", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "fraud report")
        self.assertEqual(result["data"]["intent"], "fraud_suspicion")
        self.assertEqual(result["data"]["risk_level"], "HIGH")

    async def test_higher_risk_draft_can_correct_a_coarse_low_risk_route(self):
        module = FusedIntentModule(
            Baseline("card_fee_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I was charged a fee I do not understand")
        self.assertEqual(result["data"]["intent"], "fee_complaint")
        self.assertEqual(result["data"]["risk_level"], "MEDIUM")

    async def test_high_confidence_same_risk_draft_can_correct_coarse_route(self):
        module = FusedIntentModule(
            Baseline("card_fee_enquiry", 0.95, "MEDIUM"),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.95, "risk_level": "MEDIUM", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I was charged a fee I do not understand")
        self.assertEqual(result["data"]["intent"], "fee_complaint")

    async def test_query_and_clarification_require_c_route(self):
        assistant = LLMTextAssistant(MockLLMClient([{"text": "replacement card fee policy"}, {"text": "Was the card lost, damaged, or expired?"}]), model="test")
        answer = AgentState(session_id="s", user_text="What does it cost?", decision=Decision(action=Action.ANSWER, reason_code="POLICY_RETRIEVAL_PERMITTED"))
        self.assertEqual(await assistant.rewrite(answer, request_id="q"), "replacement card fee policy")
        clarify = AgentState(session_id="s", user_text="What does it cost?", decision=Decision(action=Action.CLARIFY, reason_code="REPLACEMENT_REASON_REQUIRED"))
        self.assertEqual(await assistant.clarify(clarify, request_id="c"), "Was the card lost, damaged, or expired?")
        self.assertIsNone(await assistant.rewrite(clarify, request_id="no"))
