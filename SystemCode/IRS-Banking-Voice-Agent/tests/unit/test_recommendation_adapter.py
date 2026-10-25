"""Public async D adapter behavior, using real filtering and synthetic data."""
import asyncio
from pathlib import Path
import unittest

from pydantic import ValidationError

from banking_agent.modules.recommendation import load_fixture
from banking_agent.modules.recommendation.adapter import RecommendationAdapter
from banking_agent.schemas import RecommendationItem

ROOT = Path(__file__).resolve().parents[2]


class RecommendationAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture = load_fixture(ROOT / "data/fixtures/recommendation.json")
        self.adapter = RecommendationAdapter(self.fixture)

    async def test_permitted_call_returns_ranked_canonical_items(self):
        result = await self.adapter.recommend(
            "session-001", "RESOLVED", "NOT_REQUIRED", "GRANTED"
        )
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["data"]["allowed"])
        items = [RecommendationItem.model_validate(i) for i in result["data"]["items"]]
        self.assertEqual([i.product_id for i in items],
                         ["savings-premium", "savings-flex", "emergency-reserve"])
        self.assertEqual([i.rank for i in items], [1, 2, 3])

    async def test_keyword_call_matches_e_public_protocol(self):
        result = await self.adapter.recommend(
            session_id="session-001", complaint_status="RESOLVED",
            handoff_status="NOT_REQUIRED", consent="GRANTED",
        )
        self.assertEqual(result["data"]["reason_code"], "ELIGIBLE_WITH_CONSENT")

    async def test_complaint_and_consent_denials_are_ok_without_items(self):
        for complaint, consent, reason in [
            ("OPEN", "GRANTED", "UNRESOLVED_COMPLAINT"),
            ("UNDER_REVIEW", "GRANTED", "UNRESOLVED_COMPLAINT"),
            ("RESOLVED", "UNKNOWN", "CONSENT_REQUIRED"),
            ("RESOLVED", "DENIED", "CONSENT_REQUIRED"),
        ]:
            with self.subTest(complaint=complaint, consent=consent):
                result = await self.adapter.recommend(
                    "session-001", complaint, "NOT_REQUIRED", consent
                )
                self.assertEqual(result, {"status": "ok", "data": {
                    "allowed": False, "reason_code": reason, "items": [],
                }})

    async def test_no_eligible_products_is_a_business_result(self):
        result = await self.adapter.recommend(
            "session-002", "RESOLVED", "NOT_REQUIRED", "GRANTED"
        )
        self.assertEqual(result, {"status": "ok", "data": {
            "allowed": False, "reason_code": "NO_ELIGIBLE_PRODUCT", "items": [],
        }})

    async def test_errors_omit_data_for_e_typed_envelope(self):
        for session, complaint, handoff, consent in [
            ("unknown", "RESOLVED", "NOT_REQUIRED", "GRANTED"),
            ("session-001", "INVALID", "NOT_REQUIRED", "GRANTED"),
            ("session-001", "RESOLVED", "ESCALATED", "GRANTED"),
        ]:
            with self.subTest(session=session, complaint=complaint, handoff=handoff):
                result = await self.adapter.recommend(session, complaint, handoff, consent)
                self.assertEqual(result, {"status": "error"})

    async def test_constructor_rejects_invalid_catalog(self):
        invalid = self.fixture.model_dump(exclude={"synthetic"})
        invalid["products"][0]["min_deposit_cents"] = -1
        with self.assertRaises(ValidationError):
            RecommendationAdapter(invalid)

    async def test_configuration_is_snapshotted(self):
        self.fixture.customer_profiles.clear()
        result = await self.adapter.recommend(
            "session-001", "RESOLVED", "NOT_REQUIRED", "GRANTED"
        )
        self.assertTrue(result["data"]["allowed"])

    async def test_concurrent_calls_and_returned_values_are_isolated(self):
        results = await asyncio.gather(*[
            self.adapter.recommend(s, "RESOLVED", "NOT_REQUIRED", "GRANTED")
            for s in ["session-001", "session-002"] * 4
        ])
        self.assertEqual([r["data"]["allowed"] for r in results],
                         [True, False] * 4)
        results[0]["data"]["items"].clear()
        self.assertEqual(len(results[2]["data"]["items"]), 3)
        later = await self.adapter.recommend(
            "session-001", "RESOLVED", "NOT_REQUIRED", "GRANTED"
        )
        self.assertEqual(len(later["data"]["items"]), 3)


if __name__ == "__main__":
    unittest.main()
