"""LLM rendering is optional and cannot alter the C-approved answer route."""

import unittest

from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.observability import TraceContext
from banking_agent.app.llm_agent_support import LLMTextAssistant
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
    async def test_validated_llm_steps_are_visible_in_the_sanitized_trace(self) -> None:
        class Sink:
            traces = []
            def record_trace(self, trace): self.traces.append(trace)

        modules, sink = AnswerModules(), Sink()
        rewriter = LLMTextAssistant(
            MockLLMClient([{"text": "replacement card fee policy"}]), model="test"
        )
        response = await Orchestrator(
            modules, modules, modules, modules,
            query_rewriter=rewriter,
            trace_sink=sink,
            trace_context=TraceContext(mode="test"),
        ).handle(AgentState(session_id="llm-trace", user_text="What does it cost?"))
        self.assertEqual(response.status, "ok")
        events = [(event.module, event.status) for event in sink.traces[0].modules]
        self.assertIn(("E.LLM.query_rewrite", "ok"), events)
        llm_event = next(event for event in sink.traces[0].modules if event.module == "E.LLM.query_rewrite")
        self.assertEqual(llm_event.attempts, 1)
        self.assertIsNone(llm_event.total_tokens)  # Mock providers do not invent usage.
        self.assertNotIn("replacement card fee policy", repr(sink.traces[0]))

    async def test_llm_fallback_is_visible_without_changing_the_safe_route(self) -> None:
        class Sink:
            traces = []
            def record_trace(self, trace): self.traces.append(trace)

        modules, sink = AnswerModules(), Sink()
        rewriter = LLMTextAssistant(MockLLMClient([{}]), model="test")
        response = await Orchestrator(
            modules, modules, modules, modules, query_rewriter=rewriter, trace_sink=sink
        ).handle(AgentState(session_id="llm-fallback-trace", user_text="What does it cost?"))
        self.assertEqual(response.decision.action.value, "ANSWER")
        self.assertIn(
            ("E.LLM.query_rewrite", "fallback"),
            [(event.module, event.status) for event in sink.traces[0].modules],
        )

    async def test_query_rewriter_only_changes_the_c_permitted_retrieval_query(self) -> None:
        class Rewriter:
            async def rewrite(self, state, *, request_id):
                self.state = state
                return "replacement card fee policy"

        class RecordingModules(AnswerModules):
            async def retrieve(self, query, top_k):
                self.query = query
                return await super().retrieve(query, top_k)

        modules, rewriter = RecordingModules(), Rewriter()
        response = await Orchestrator(
            modules, modules, modules, modules, query_rewriter=rewriter
        ).handle(AgentState(session_id="llm-query", user_text="What does it cost?"))
        self.assertEqual(response.decision.action.value, "ANSWER")
        self.assertEqual(
            modules.query,
            "What does it cost?\nreplacement card fee policy",
        )

    async def test_clarification_generator_cannot_change_c_decision(self) -> None:
        class ClarifyModules(AnswerModules):
            async def decide(self, state):
                return {"status": "ok", "data": {"action": "CLARIFY", "reason_code": "LOW_INTENT_CONFIDENCE", "next_state": {}}}

        class Clarifier:
            async def clarify(self, state, *, request_id):
                return "Which banking task would you like help with?"

        modules = ClarifyModules()
        response = await Orchestrator(
            modules, modules, modules, modules, clarification_generator=Clarifier()
        ).handle(AgentState(session_id="llm-clarify", user_text="Help me with that"))
        self.assertEqual(response.decision.action.value, "CLARIFY")
        self.assertEqual(response.text, "Which banking task would you like help with?")

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
