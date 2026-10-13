"""Behavioral tests for product filtering and deterministic ranking."""

import copy
import itertools
import json
from pathlib import Path
import unittest

from banking_agent.modules.recommendation import recommend
from banking_agent.schemas import RecommendationItem

FIXTURE = Path(__file__).resolve().parents[2] / "data/fixtures/recommendation.json"


class RecommendationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.request = {
            "session_id": "session-001",
            "complaint_status": "RESOLVED",
            "handoff_status": "NOT_REQUIRED",
            "consent": "GRANTED",
        }

    def call(self, *, profiles=None, products=None):
        return recommend(
            self.request,
            customer_profiles=self.raw["customer_profiles"] if profiles is None else profiles,
            products=self.raw["products"] if products is None else products,
        )

    def test_s06_returns_expected_products_and_shared_item_format(self) -> None:
        result = self.call()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["data"]["allowed"])
        self.assertEqual(result["data"]["reason_code"], "ELIGIBLE_WITH_CONSENT")
        items = result["data"]["items"]
        self.assertEqual(
            [item["product_id"] for item in items],
            ["savings-premium", "savings-flex", "emergency-reserve"],
        )
        self.assertEqual([item["rank"] for item in items], [1, 2, 3])
        for item in items:
            RecommendationItem.model_validate(item)
            self.assertEqual(set(item), {"product_id", "name", "rank", "reason"})
        self.assertIn("does not match", items[2]["reason"])
        json.dumps(result)

    def test_goal_match_precedes_demo_priority(self) -> None:
        profiles = copy.deepcopy(self.raw["customer_profiles"])
        profiles["session-001"]["goal"] = "emergency"
        items = self.call(profiles=profiles)["data"]["items"]
        self.assertEqual(
            [item["product_id"] for item in items],
            ["emergency-reserve", "savings-flex", "savings-premium"],
        )

    def test_ties_are_broken_by_product_id(self) -> None:
        first = copy.deepcopy(self.raw["products"][0])
        second = copy.deepcopy(first)
        first["product_id"] = "z-product"
        second["product_id"] = "a-product"
        items = self.call(products=[first, second])["data"]["items"]
        self.assertEqual([item["product_id"] for item in items], ["a-product", "z-product"])

    def test_all_candidate_permutations_and_repeats_are_stable(self) -> None:
        expected = self.call()
        for products in itertools.permutations(self.raw["products"]):
            with self.subTest(order=[product["product_id"] for product in products]):
                self.assertEqual(self.call(products=products), expected)
                self.assertEqual(self.call(products=products), expected)

    def test_product_age_boundary(self) -> None:
        product = self.raw["products"][1]
        for age, expected_count in ((20, 0), (21, 1), (22, 1)):
            with self.subTest(age=age):
                profiles = copy.deepcopy(self.raw["customer_profiles"])
                profiles["session-001"]["age"] = age
                self.assertEqual(
                    len(self.call(profiles=profiles, products=[product])["data"]["items"]),
                    expected_count,
                )

    def test_product_deposit_boundary_in_integer_cents(self) -> None:
        product = self.raw["products"][1]
        for amount, expected_count in ((99999, 0), (100000, 1), (100001, 1)):
            with self.subTest(amount=amount):
                profiles = copy.deepcopy(self.raw["customer_profiles"])
                profiles["session-001"]["available_deposit_cents"] = amount
                self.assertEqual(
                    len(self.call(profiles=profiles, products=[product])["data"]["items"]),
                    expected_count,
                )

    def test_residency_mismatch_filters_products(self) -> None:
        self.request["session_id"] = "session-003"
        self.assertEqual(self.call()["data"]["items"], [])

    def test_partial_eligibility_returns_only_the_matching_product(self) -> None:
        self.request["session_id"] = "session-004"
        items = self.call()["data"]["items"]
        self.assertEqual([item["product_id"] for item in items], ["savings-flex"])
        self.assertEqual(items[0]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
