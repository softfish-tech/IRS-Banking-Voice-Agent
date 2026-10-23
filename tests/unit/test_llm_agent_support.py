"""LLM middle-loop proposals are typed and cannot weaken deterministic safety."""
import asyncio
import unittest

from banking_agent.app.conversation_context import deterministic_follow_up_resolution, recent_public_context
from banking_agent.app.llm_agent_support import FusedIntentModule, LLMTextAssistant, LLMUnderstanding
from banking_agent.app.providers import MockLLMClient
from banking_agent.schemas import Action, AgentState, ConversationContext, ConversationTurn, Decision


class Baseline:
    def __init__(self, intent="policy_enquiry", confidence=0.6, risk="LOW"):
        self.intent, self.confidence, self.risk = intent, confidence, risk
    async def analyze(self, session_id, user_text):
        return {"status": "ok", "data": {"intent": self.intent, "confidence": self.confidence, "risk_level": self.risk, "entities": []}}


class SlowClient:
    async def generate(self, request, response_model):
        await asyncio.sleep(1)


class LLMAgentSupportTests(unittest.IsolatedAsyncioTestCase):
    def test_recent_context_keeps_a_successful_long_public_answer_bounded(self):
        context = recent_public_context([
            {"role": "user", "content": "What is the replacement policy?"},
            {
                "role": "assistant", "content": "x" * 9_000,
                "response": {"status": "ok", "decision": {"action": "ANSWER"}},
            },
        ])
        self.assertEqual(len(context.turns), 1)
        self.assertEqual(len(context.turns[0].assistant_text), 8_000)

    async def test_deterministic_replacement_follow_up_survives_llm_fallback(self):
        context = ConversationContext(turns=[ConversationTurn(
            user_text="What is the replacement-card fee?",
            assistant_text="Which replacement reason applies?",
            action=Action.CLARIFY,
        )])
        self.assertEqual(
            deterministic_follow_up_resolution("When will it arrive?", context),
            "When will the replacement card arrive?",
        )
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(SlowClient(), model="test", timeout_seconds=0.01),
        )

        await module.analyze_with_context("s", "When will it arrive?", context)

        self.assertTrue(module.last_context_reference_resolved)
        self.assertEqual(module.last_resolved_user_text, "When will the replacement card arrive?")

    def test_deterministic_delivery_fee_follow_up_preserves_required_reason_gate(self):
        context = ConversationContext(turns=[ConversationTurn(
            user_text="What is the replacement-card fee?",
            assistant_text="Which replacement reason applies?",
            action=Action.CLARIFY,
        )])

        self.assertEqual(
            deterministic_follow_up_resolution("Does that include delivery?", context),
            "Does the replacement-card fee include delivery?",
        )

    async def test_deterministic_damage_and_pending_follow_ups_are_bounded(self):
        replacement_context = ConversationContext(turns=[ConversationTurn(
            user_text="When will my replacement card arrive?",
            assistant_text="Which replacement reason applies?",
            action=Action.CLARIFY,
        )])
        self.assertEqual(
            deterministic_follow_up_resolution("It was damaged.", replacement_context),
            "When will a damaged replacement card arrive?",
        )
        transfer_context = ConversationContext(turns=[ConversationTurn(
            user_text="What about my transfer?",
            assistant_text="Please tell me its current status.",
            action=Action.CLARIFY,
        )])
        self.assertEqual(
            deterministic_follow_up_resolution("It is still pending.", transfer_context),
            "My bank transfer is still pending. What should I do?",
        )
        self.assertIsNone(
            deterministic_follow_up_resolution("It was stolen.", replacement_context)
        )

    async def test_deterministic_damage_preserves_an_explicit_fee_question(self):
        context = ConversationContext(turns=[ConversationTurn(
            user_text="How much is a replacement card?",
            assistant_text="Which replacement reason applies?",
            action=Action.CLARIFY,
        )])
        self.assertEqual(
            deterministic_follow_up_resolution("It was damaged.", context),
            "What is the replacement-card fee for a damaged card?",
        )

    async def test_deterministic_resolution_can_use_the_bounded_recent_window(self):
        context = ConversationContext(turns=[
            ConversationTurn(
                user_text="What is the replacement-card fee?",
                assistant_text="Which replacement reason applies?",
                action=Action.CLARIFY,
            ),
            ConversationTurn(
                user_text="When will it arrive?",
                assistant_text="Which replacement reason applies?",
                action=Action.CLARIFY,
            ),
            ConversationTurn(
                user_text="It was damaged.",
                assistant_text="I need more evidence.",
                action=Action.ABSTAIN,
            ),
        ])
        self.assertEqual(
            deterministic_follow_up_resolution("What should I do now?", context),
            "What should I do to replace my damaged card?",
        )
        self.assertEqual(
            deterministic_follow_up_resolution("How much exactly?", context),
            "What is the replacement-card fee?",
        )
        self.assertEqual(
            deterministic_follow_up_resolution(
                "Back to the card fee: how much is it.", context
            ),
            "What is the replacement-card fee?",
        )
        self.assertIsNone(
            deterministic_follow_up_resolution(
                "My old card is still working, but the chip is damaged.",
                ConversationContext(turns=[context.turns[0]]),
            )
        )
        crypto_context = ConversationContext(turns=[ConversationTurn(
            user_text="What is the crypto wallet recovery policy?",
            assistant_text="Crypto wallet recovery is unsupported.",
            action=Action.ANSWER,
        )])
        self.assertEqual(
            deterministic_follow_up_resolution("What if I lost access to it?", crypto_context),
            "What if I lose access to my crypto wallet?",
        )

    async def test_deterministic_resolution_reanalyses_only_the_safe_request_view(self):
        context = ConversationContext(turns=[ConversationTurn(
            user_text="What about my transfer?",
            assistant_text="Please tell me its current status.",
            action=Action.CLARIFY,
        )])
        module = FusedIntentModule(
            Baseline("pending_transfer", 0.95, "LOW"),
            LLMUnderstanding(SlowClient(), model="test", timeout_seconds=0.01),
        )
        result = await module.analyze_with_context("s", "It is still pending.", context)
        self.assertEqual(result["data"]["intent"], "pending_transfer")
        self.assertTrue(module.last_context_reference_resolved)
        self.assertEqual(
            module.last_resolved_user_text,
            "My bank transfer is still pending. What should I do?",
        )

    async def test_correction_cannot_be_marked_as_a_context_resolution(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{
                "intent": "policy_enquiry", "confidence": 0.95, "risk_level": "LOW",
                "entities": [], "context_resolved": True,
                "resolved_user_text": "What is the replacement-card fee?",
            }]), model="test"),
        )
        context = ConversationContext(turns=[ConversationTurn(
            user_text="I lost my card.",
            assistant_text="A handoff has been started.",
            action=Action.ESCALATE,
        )])

        await module.analyze_with_context(
            "s", "Sorry, it was not lost; I only want the replacement fee.", context
        )

        self.assertFalse(module.last_context_reference_resolved)
        self.assertEqual(module.last_llm_disposition, "retained")

    async def test_understanding_timeout_falls_back_before_orchestrator_timeout(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(SlowClient(), model="test", timeout_seconds=0.01),
            mode="shadow",
        )
        result = await module.analyze("s", "What is the card fee?")
        self.assertEqual(result["data"]["intent"], "policy_enquiry")
        self.assertEqual(module.last_llm_status, "fallback")
        self.assertLess(module.last_llm_duration_ms, 500)

    async def test_confident_draft_improves_ambiguous_policy_route(self):
        module = FusedIntentModule(
            Baseline(),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I was charged an unexplained fee")
        self.assertEqual(result["data"]["intent"], "fee_complaint")
        self.assertEqual(result["data"]["risk_level"], "MEDIUM")

    async def test_shadow_mode_records_a_draft_without_changing_a_output(self):
        module = FusedIntentModule(Baseline("policy_enquiry", 0.6, "LOW"), LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": []}]), model="test"), mode="shadow")
        result = await module.analyze("s", "I was charged an unexplained fee")
        self.assertEqual(result["data"]["intent"], "policy_enquiry")
        self.assertEqual(module.last_llm_disposition, "shadow")

    async def test_ambiguous_draft_selects_safe_unknown_only_in_fuse_mode(self):
        module = FusedIntentModule(Baseline("policy_enquiry", 0.95, "LOW"), LLMUnderstanding(MockLLMClient([{"intent": "UNKNOWN", "confidence": 0.9, "risk_level": "LOW", "entities": [], "ambiguous": True}]), model="test"))
        result = await module.analyze("s", "what about that")
        self.assertEqual(result["data"]["intent"], "UNKNOWN")
        self.assertEqual(module.last_llm_disposition, "selected_ambiguity")

    async def test_unknown_draft_needs_an_explicit_reference_before_clarifying(self):
        module = FusedIntentModule(Baseline("policy_enquiry", 0.95, "LOW"), LLMUnderstanding(MockLLMClient([{"intent": "UNKNOWN", "confidence": 0.9, "risk_level": "LOW", "entities": [], "ambiguous": True}]), model="test"))
        result = await module.analyze("s", "What about that fee?")
        self.assertEqual(result["data"]["intent"], "UNKNOWN")
        self.assertEqual(module.last_llm_disposition, "selected_ambiguity")

        retained = FusedIntentModule(Baseline("policy_enquiry", 0.95, "LOW"), LLMUnderstanding(MockLLMClient([{"intent": "UNKNOWN", "confidence": 0.9, "risk_level": "LOW", "entities": []}]), model="test"))
        result = await retained.analyze("s", "What is the crypto policy?")
        self.assertEqual(result["data"]["intent"], "policy_enquiry")

    async def test_unknown_draft_without_ambiguity_cannot_override_confident_a(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "UNKNOWN", "confidence": 0.9, "risk_level": "LOW", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I need help with it.")
        self.assertEqual(result["data"]["intent"], "policy_enquiry")
        self.assertEqual(module.last_llm_disposition, "retained")

    async def test_terse_ellipsis_can_use_a_high_confidence_context_resolution(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{
                "intent": "card_fee_enquiry", "confidence": 0.92, "risk_level": "LOW",
                "entities": [], "context_resolved": True,
                "resolved_user_text": "How much is the replacement-card fee?",
            }]), model="test"),
        )
        context = ConversationContext(turns=[ConversationTurn(
            user_text="When will my replacement card arrive?",
            assistant_text="Please tell me why the card needs replacing.",
            action=Action.CLARIFY,
        )])

        result = await module.analyze_with_context("s", "How much exactly?", context)

        self.assertEqual(result["data"]["intent"], "card_fee_enquiry")
        self.assertEqual(module.last_llm_disposition, "selected_context")
        self.assertTrue(module.last_context_reference_resolved)


    async def test_ambiguous_specific_draft_cannot_override_confident_a(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.95, "risk_level": "MEDIUM", "entities": [], "ambiguous": True}]), model="test"),
        )
        result = await module.analyze("s", "What about that?")
        self.assertEqual(result["data"]["intent"], "policy_enquiry")
        self.assertEqual(module.last_llm_disposition, "risk_raised")

    async def test_ambiguity_flag_without_reference_does_not_override_a(self):
        module = FusedIntentModule(Baseline("fee_complaint", 0.9, "MEDIUM"), LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": [], "ambiguous": True}]), model="test"))
        result = await module.analyze("s", "I do not recognise this fee")
        self.assertEqual(result["data"]["intent"], "fee_complaint")
        self.assertEqual(module.last_llm_disposition, "retained")

    async def test_llm_cannot_lower_existing_high_risk(self):
        module = FusedIntentModule(
            Baseline("fraud_suspicion", 0.95, "HIGH"),
            LLMUnderstanding(MockLLMClient([{"intent": "policy_enquiry", "confidence": 0.99, "risk_level": "LOW", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "fraud report")
        self.assertEqual(result["data"]["intent"], "fraud_suspicion")
        self.assertEqual(result["data"]["risk_level"], "HIGH")

    async def test_higher_risk_draft_preserves_a_intent(self):
        module = FusedIntentModule(
            Baseline("card_fee_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I was charged a fee I do not understand")
        self.assertEqual(result["data"]["intent"], "card_fee_enquiry")
        self.assertEqual(result["data"]["risk_level"], "MEDIUM")
        self.assertEqual(module.last_llm_disposition, "risk_raised")

    async def test_llm_high_risk_draft_without_urgent_text_does_not_escalate_a_fee_complaint(self):
        module = FusedIntentModule(
            Baseline("fee_complaint", 0.9, "MEDIUM"),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.9, "risk_level": "HIGH", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I got billed a weird card charge")
        self.assertEqual(result["data"]["intent"], "fee_complaint")
        self.assertEqual(result["data"]["risk_level"], "MEDIUM")
        self.assertEqual(module.last_llm_disposition, "retained")

    async def test_llm_high_risk_draft_with_card_use_signal_can_raise_risk(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.9, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "unauthorized_transaction", "confidence": 0.9, "risk_level": "HIGH", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "My card got used by someone else")
        self.assertEqual(result["data"]["risk_level"], "HIGH")
        self.assertEqual(module.last_llm_disposition, "risk_raised")

    async def test_short_context_free_request_can_select_safe_unknown(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.95, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "UNKNOWN", "confidence": 0.9, "risk_level": "LOW", "entities": [], "ambiguous": True}]), model="test"),
        )
        result = await module.analyze("s", "What happens next?")
        self.assertEqual(result["data"]["intent"], "UNKNOWN")
        self.assertEqual(module.last_llm_disposition, "selected_ambiguity")

    async def test_high_confidence_same_risk_draft_is_retained(self):
        module = FusedIntentModule(
            Baseline("card_fee_enquiry", 0.95, "MEDIUM"),
            LLMUnderstanding(MockLLMClient([{"intent": "fee_complaint", "confidence": 0.95, "risk_level": "MEDIUM", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "I was charged a fee I do not understand")
        self.assertEqual(result["data"]["intent"], "card_fee_enquiry")

    async def test_materially_stronger_llm_can_correct_bounded_low_risk_query(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.74, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "card_fee_enquiry", "confidence": 0.95, "risk_level": "LOW", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "card replcement fee?")
        self.assertEqual(result["data"]["intent"], "card_fee_enquiry")
        self.assertEqual(result["data"]["risk_level"], "LOW")
        self.assertEqual(module.last_llm_disposition, "selected_safe_low_risk")

    async def test_bounded_low_risk_correction_cannot_select_recommendation_intent(self):
        module = FusedIntentModule(
            Baseline("policy_enquiry", 0.74, "LOW"),
            LLMUnderstanding(MockLLMClient([{"intent": "product_recommendation", "confidence": 0.99, "risk_level": "LOW", "entities": []}]), model="test"),
        )
        result = await module.analyze("s", "what is the card fee?")
        self.assertEqual(result["data"]["intent"], "policy_enquiry")
        self.assertEqual(module.last_llm_disposition, "retained")

    async def test_query_and_clarification_require_c_route(self):
        assistant = LLMTextAssistant(MockLLMClient([{"text": "replacement card fee policy"}, {"text": "Was the card lost, damaged, or expired?"}]), model="test")
        answer = AgentState(session_id="s", user_text="What does it cost?", decision=Decision(action=Action.ANSWER, reason_code="POLICY_RETRIEVAL_PERMITTED"))
        self.assertEqual(await assistant.rewrite(answer, request_id="q"), "replacement card fee policy")
        clarify = AgentState(session_id="s", user_text="What does it cost?", decision=Decision(action=Action.CLARIFY, reason_code="REPLACEMENT_REASON_REQUIRED"))
        self.assertEqual(await assistant.clarify(clarify, request_id="c"), "Was the card lost, damaged, or expired?")
        self.assertIsNone(await assistant.rewrite(clarify, request_id="no"))
