"""Response templates preserve final C decisions and returned evidence."""
import unittest
from banking_agent.schemas import Action, AgentState, Decision, RecommendationItem
from banking_agent.app.orchestrator.response_builder import build_response

class ResponseBuilderTests(unittest.TestCase):
    def test_safe_paths_render_without_recommendations(self):
        for action in (Action.HANDLE_COMPLAINT, Action.ESCALATE, Action.CLARIFY, Action.BLOCK, Action.ABSTAIN):
            with self.subTest(action=action):
                state = AgentState(session_id='test', user_text='Hello', decision=Decision(action=action, reason_code='TEST'))
                self.assertTrue(build_response(state))
                self.assertEqual(state.decision.action, action)

    def test_recommendation_renders_returned_items(self):
        state = AgentState(session_id='test', user_text='Hello', decision=Decision(action=Action.RECOMMEND, reason_code='TEST'), recommendations=[RecommendationItem(product_id='synthetic', name='Synthetic Savings', rank=1, reason='Synthetic match')])
        self.assertIn('Synthetic Savings: Synthetic match', build_response(state))
