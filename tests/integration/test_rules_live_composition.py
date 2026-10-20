"""Current-main local composition smoke test: E API + C + B mock + D adapter."""
import asyncio
import json
import unittest
from pathlib import Path

from banking_agent.app.api.server import DemoApplication
from banking_agent.app.bootstrap import ModuleBundle, StaticModuleFactory
from banking_agent.app.persistence import InMemoryStore
from banking_agent.modules.rag import MockRetriever
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture
from banking_agent.modules.rules import RuleEngine


class SyntheticIntent:
    async def analyze(self, session_id, user_text):
        if user_text == "I was charged a fee I do not understand.":
            intent, confidence, risk = "fee_complaint", .92, "MEDIUM"
        elif user_text == "I think this transfer may be a scam.":
            intent, confidence, risk = "policy_enquiry", .20, "LOW"
        elif user_text.startswith("Can you recommend"):
            intent, confidence, risk = "policy_enquiry", .93, "LOW"
        else:
            intent, confidence, risk = "card_fee_enquiry", .94, "LOW"
        return {"status": "ok", "data": {
            "intent": intent, "confidence": confidence,
            "risk_level": risk, "entities": [],
        }}


class AsyncMockRetrieval:
    def __init__(self):
        self.backend = MockRetriever()
        self.calls = 0

    async def retrieve(self, query, top_k):
        self.calls += 1
        return self.backend.retrieve(query, top_k)


class RecordingRecommendation:
    def __init__(self, root):
        self.backend = RecommendationAdapter(
            load_fixture(root / "data/fixtures/recommendation.json")
        )
        self.calls = 0

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.calls += 1
        return await self.backend.recommend(
            session_id, complaint_status, handoff_status, consent
        )


class CurrentMainCompositionTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.retrieval = AsyncMockRetrieval()
        self.recommendation = RecordingRecommendation(root)
        bundle = ModuleBundle(
            SyntheticIntent(), self.retrieval, RuleEngine(), self.recommendation
        )
        self.app = DemoApplication(
            store=InMemoryStore(),
            module_factory=StaticModuleFactory(bundle),
        )
        status, _, _ = self.api(
            "POST", "/api/auth/register",
            {"username": "synthetic_test_user", "password": "testpw"}
        )
        self.assertEqual(status, 201)
        status, headers, _ = self.api(
            "POST", "/api/auth/login",
            {"username": "synthetic_test_user", "password": "testpw"}
        )
        self.assertEqual(status, 200)
        self.cookie = dict(headers)["Set-Cookie"].split(";", 1)[0]

    def tearDown(self):
        self.app.store.close()

    def api(self, method, path, body=None):
        payload = json.dumps(body).encode() if body is not None else b""
        status, headers, data = asyncio.run(
            self.app.api(method, path, payload, getattr(self, "cookie", ""))
        )
        return status.value, headers, json.loads(data)

    def create(self, text):
        status, _, body = self.api(
            "POST", "/api/conversations", {"user_text": text}
        )
        self.assertEqual(status, 201, body)
        return body

    def test_generic_fee_asks_for_reason(self):
        body = self.create("What is the replacement fee for my card?")
        self.assertEqual(body["response"]["decision"]["action"], "CLARIFY")
        self.assertEqual(self.retrieval.calls, 1)
        self.assertEqual(self.recommendation.calls, 0)

    def test_specific_lost_card_fee_uses_cited_evidence(self):
        body = self.create("How much does replacing a lost card cost?")
        self.assertEqual(body["response"]["decision"]["action"], "ANSWER")
        self.assertIn("SGD 15", body["response"]["message"]["text"])
        self.assertTrue(body["response"]["citations"])
        self.assertEqual(self.retrieval.calls, 1)

    def test_misclassified_scam_escalates_and_persists(self):
        body = self.create("I think this transfer may be a scam.")
        self.assertEqual(body["response"]["decision"]["action"], "ESCALATE")
        self.assertEqual(body["conversation"]["complaint_status"], "OPEN")
        self.assertEqual(body["conversation"]["handoff_status"], "ESCALATED")
        self.assertEqual(self.retrieval.calls, 0)
        self.assertEqual(self.recommendation.calls, 0)

    def test_open_complaint_blocks_misclassified_offer(self):
        body = self.create("I was charged a fee I do not understand.")
        self.assertEqual(body["response"]["decision"]["action"], "HANDLE_COMPLAINT")
        conversation = body["conversation"]
        self.assertEqual(conversation["complaint_status"], "OPEN")
        status, _, next_turn = self.api(
            "POST", f"/api/conversations/{conversation['id']}/messages",
            {"user_text": "Can you recommend a savings product?", "expected_version": 1},
        )
        self.assertEqual(status, 200, next_turn)
        self.assertEqual(next_turn["response"]["decision"]["action"], "BLOCK")
        self.assertEqual(next_turn["conversation"]["complaint_status"], "OPEN")
        self.assertEqual(self.recommendation.calls, 0)


if __name__ == "__main__":
    unittest.main()
