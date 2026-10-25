import asyncio
import unittest

from banking_agent.app.persistence import StoreError
from banking_agent.app.recommendation_adapter import ConversationProfileRecommendationAdapter


class Delegate:
    def __init__(self) -> None:
        self.profile_key = ""

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.profile_key = session_id
        return {"status": "ok", "data": {"allowed": True, "items": []}}


class ConversationProfileRecommendationAdapterTests(unittest.TestCase):
    def test_resolves_the_conversation_before_delegating_to_d(self) -> None:
        delegate = Delegate()
        adapter = ConversationProfileRecommendationAdapter(delegate, lambda _: "session-003")
        result = asyncio.run(adapter.recommend("conversation-uuid", "NONE", "NOT_REQUIRED", "YES"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(delegate.profile_key, "session-003")

    def test_fails_closed_when_no_profile_snapshot_exists(self) -> None:
        adapter = ConversationProfileRecommendationAdapter(Delegate(), lambda _: (_ for _ in ()).throw(StoreError("synthetic_profile_key_required")))
        result = asyncio.run(adapter.recommend("legacy-conversation", "NONE", "NOT_REQUIRED", "YES"))
        self.assertEqual(result, {"status": "error"})
