"""E-owned tests for evidence-constrained final response generation."""

import unittest

from banking_agent.app.providers import MockLLMClient
from banking_agent.app.response_generator import GroundedResponseGenerator
from banking_agent.schemas import Action, AgentState, Decision, RetrievedDocument


def answer_state() -> AgentState:
    return AgentState(
        session_id="response-test",
        user_text="What is the synthetic replacement fee?",
        decision=Decision(action=Action.ANSWER, reason_code="POLICY_EVIDENCE_FOUND"),
        retrieved_docs=[
            RetrievedDocument(
                document_id="policy-1",
                title="Synthetic fees",
                source="Synthetic source",
                score=0.9,
                excerpt="The synthetic replacement fee is SGD 10.",
            )
        ],
    )


class GroundedResponseGeneratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_renders_valid_answer_with_e_owned_source_line(self) -> None:
        generator = GroundedResponseGenerator(
            MockLLMClient(
                [{"answer": "The replacement fee is SGD 10.", "citation_ids": ["policy-1"]}]
            ),
            model="test-model",
        )
        text = await generator.generate(answer_state(), request_id="opaque-request")
        self.assertEqual(
            text,
            "The replacement fee is SGD 10.\n[Source: Synthetic fees; policy-1]",
        )

    async def test_unknown_citation_falls_back(self) -> None:
        generator = GroundedResponseGenerator(
            MockLLMClient([
                {"answer": "Invented answer", "citation_ids": ["not-a-source"]},
                {"answer": "Still invented", "citation_ids": ["not-a-source"]},
            ]),
            model="test-model",
        )
        self.assertIsNone(await generator.generate(answer_state(), request_id="opaque-request"))
        self.assertEqual(generator.outcome("opaque-request")[-1], "invalid_citation")

    async def test_invalid_first_draft_retries_once_with_same_approved_sources(self) -> None:
        client = MockLLMClient(
            [
                {"answer": "Invented answer", "citation_ids": ["not-a-source"]},
                {"answer": "The replacement fee is SGD 10.", "citation_ids": ["policy-1"]},
            ]
        )
        generator = GroundedResponseGenerator(client, model="test-model")

        text = await generator.generate(answer_state(), request_id="opaque-request")

        self.assertEqual(
            text,
            "The replacement fee is SGD 10.\n[Source: Synthetic fees; policy-1]",
        )
        self.assertEqual(len(client.requests), 2)
        self.assertEqual(
            generator.outcome("opaque-request")[2], 2,
        )

    async def test_non_answer_route_never_calls_provider(self) -> None:
        client = MockLLMClient([{"answer": "Unused", "citation_ids": ["policy-1"]}])
        generator = GroundedResponseGenerator(client, model="test-model")
        state = answer_state()
        state.decision = Decision(action=Action.ABSTAIN, reason_code="INSUFFICIENT_EVIDENCE")
        self.assertIsNone(await generator.generate(state, request_id="opaque-request"))
        self.assertEqual(client.requests, [])

    async def test_damaged_replacement_prompt_excludes_unrelated_freeze_sentence(self) -> None:
        state = answer_state()
        state.user_text = 'How much does it cost to replace my damaged card?'
        state.retrieved_docs[0] = RetrievedDocument(
            document_id='policy-1', title='Damaged card replacement', source='Synthetic source', score=0.9,
            excerpt=(
                'A temporary customer freeze may be removed within 60 seconds. '
                'Damaged-card replacement costs SGD 15.'
            ),
        )
        client = MockLLMClient([{'answer': 'The damaged-card replacement costs SGD 15.', 'citation_ids': ['policy-1']}])
        generator = GroundedResponseGenerator(client, model='test-model')

        await generator.generate(state, request_id='opaque-request')

        prompt = client.requests[0].messages[-1].content
        self.assertIn('Damaged-card replacement costs SGD 15.', prompt)
        self.assertNotIn('temporary customer freeze', prompt)
