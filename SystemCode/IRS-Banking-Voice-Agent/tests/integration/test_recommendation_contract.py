"""D/shared-schema integration; this is not an E-owned full-system E2E test."""

import json
from pathlib import Path
import unittest

from banking_agent.modules.recommendation import load_fixture, recommend
from banking_agent.schemas import AgentState, Decision, RecommendationItem

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests/fixtures/scenarios/recommendation.json"


class RecommendationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = load_fixture(ROOT / "data/fixtures/recommendation.json")
        self.cases = json.loads(CASES.read_text(encoding="utf-8"))["scenarios"]

    def call(self, request):
        return recommend(
            request,
            customer_profiles=self.fixture.customer_profiles,
            products=self.fixture.products,
        )

    def test_scenario_results_match_independent_fixture_expectations(self) -> None:
        for case in self.cases:
            with self.subTest(scenario=case["id"]):
                result = self.call(case["request"])
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["data"]["allowed"], case["expected_d"]["allowed"])
                self.assertEqual(result["data"]["reason_code"], case["expected_d"]["reason_code"])
                self.assertEqual(
                    [item["product_id"] for item in result["data"]["items"]],
                    case["expected_d"]["product_ids"],
                )

    def test_s06_items_merge_into_canonical_state_without_changing_decision(self) -> None:
        case = next(case for case in self.cases if case["id"] == "S06")
        state = AgentState(
            **case["request"],
            user_text=case["user_text"],
            decision=Decision(
                action=case["expected_c_action"],
                reason_code=case["expected_c_reason_code"],
            ),
        )
        original = state.model_dump(mode="json")
        result = self.call(case["request"])
        state.recommendations = [
            RecommendationItem.model_validate(item)
            for item in result["data"]["items"]
        ]
        round_trip = AgentState.model_validate_json(state.model_dump_json())
        self.assertEqual(round_trip.decision.model_dump(mode="json"), original["decision"])
        self.assertEqual(round_trip.complaint_status.value, "RESOLVED")
        self.assertEqual(round_trip.consent.value, "GRANTED")
        self.assertEqual(len(round_trip.recommendations), 3)
        self.assertIsNone(round_trip.final_response)

    def test_technical_failure_does_not_mutate_existing_state(self) -> None:
        state = AgentState(session_id="unknown-session", user_text="Recommend savings")
        before = state.model_dump(mode="json")
        result = self.call({
            "session_id": state.session_id,
            "complaint_status": "RESOLVED",
            "handoff_status": "NOT_REQUIRED",
            "consent": "GRANTED",
        })
        self.assertEqual(result, {"status": "error", "data": {}})
        self.assertEqual(state.model_dump(mode="json"), before)


if __name__ == "__main__":
    unittest.main()
