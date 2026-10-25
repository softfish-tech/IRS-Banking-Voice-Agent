"""Response templates preserve final C decisions and returned evidence."""
import unittest
from banking_agent.schemas import Action, AgentState, Decision, RecommendationItem, RetrievedDocument
from banking_agent.app.orchestrator.response_builder import build_response

class ResponseBuilderTests(unittest.TestCase):
    def test_safe_paths_render_without_recommendations(self):
        for action in (Action.HANDLE_COMPLAINT, Action.ESCALATE, Action.CLARIFY, Action.BLOCK, Action.ABSTAIN):
            with self.subTest(action=action):
                state = AgentState(session_id='test', user_text='Hello', decision=Decision(action=action, reason_code='TEST'))
                self.assertTrue(build_response(state))
                self.assertEqual(state.decision.action, action)

    def test_recommendation_does_not_render_fixture_eligibility_reasoning(self):
        state = AgentState(session_id='test', user_text='Hello', decision=Decision(action=Action.RECOMMEND, reason_code='TEST'), recommendations=[RecommendationItem(product_id='synthetic', name='Synthetic Savings', rank=1, reason='Synthetic match')])
        response = build_response(state)
        self.assertIn('product options', response)
        self.assertNotIn('Synthetic', response)

    def test_damaged_replacement_fallback_omits_unrelated_freeze_paragraph(self):
        state = AgentState(
            session_id='test', user_text='How much does it cost to replace my damaged card?',
            decision=Decision(action=Action.ANSWER, reason_code='POLICY_EVIDENCE_FOUND'),
            retrieved_docs=[RetrievedDocument(
                document_id='damage-policy', title='Damaged card replacement', source='Synthetic policy', score=0.9,
                excerpt=(
                    'A temporary customer freeze may be removed within 60 seconds. '
                    'Damaged-card replacement costs SGD 15. Standard delivery costs SGD 0.'
                ),
            )],
        )
        response = build_response(state)
        self.assertIn('Damaged-card replacement costs SGD 15.', response)
        self.assertNotIn('temporary customer freeze', response)

    def test_crypto_wallet_recovery_renders_reviewed_unsupported_boundary(self):
        state = AgentState(
            session_id="test",
            user_text="Does the bank support recovering crypto wallets?",
            decision=Decision(action=Action.ANSWER, reason_code="POLICY_EVIDENCE_FOUND"),
            retrieved_docs=[RetrievedDocument(
                document_id="NB-v1_1-fiat_currency_support-001",
                title="Supported balances and funding boundaries",
                source="Synthetic policy",
                score=0.9,
                excerpt="Other fiat currencies, cryptocurrency and precious metals are unsupported.",
            )],
        )

        answer = build_response(state)

        self.assertIn("cryptocurrency is unsupported", answer.casefold())
        self.assertIn("wallet recovery is not supported", answer.casefold())
        self.assertIn("NB-v1_1-fiat_currency_support-001", answer)

    def test_crypto_wallet_recovery_uses_the_resolved_follow_up_question(self):
        state = AgentState(
            session_id="test", user_text="What if I lost access to it?",
            resolved_user_text="What if I lose access to my crypto wallet?",
            context_reference_resolved=True,
            decision=Decision(action=Action.ANSWER, reason_code="POLICY_EVIDENCE_FOUND"),
            retrieved_docs=[RetrievedDocument(
                document_id="NB-v1_1-fiat_currency_support-001",
                title="Supported balances and funding boundaries",
                source="Synthetic policy", score=0.9,
                excerpt="Cryptocurrency is unsupported at NovaBank.",
            )],
        )

        self.assertIn("wallet recovery is not supported", build_response(state).casefold())

    def test_reason_specific_safe_templates_include_required_public_facts(self):
        clarify = AgentState(
            session_id="test", user_text="card replacement fee",
            decision=Decision(action=Action.CLARIFY, reason_code="REPLACEMENT_REASON_REQUIRED"),
        )
        complaint = AgentState(
            session_id="test", user_text="why was I charged?",
            decision=Decision(action=Action.HANDLE_COMPLAINT, reason_code="FEE_COMPLAINT"),
        )

        self.assertIn("lost", build_response(clarify).casefold())
        self.assertIn("complaint", build_response(complaint).casefold())
        self.assertIn("case is open", build_response(complaint).casefold())
