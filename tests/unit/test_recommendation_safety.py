"""Fail-closed, no-candidate and data-integrity checks for the D module."""

import copy
import json
from pathlib import Path
import unittest

from banking_agent.modules.recommendation import Product, load_fixture, recommend

FIXTURE = Path(__file__).resolve().parents[2] / "data/fixtures/recommendation.json"
ERROR = {"status": "error", "data": {}}


class RecommendationSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.request = {
            "session_id": "session-001",
            "complaint_status": "RESOLVED",
            "handoff_status": "NOT_REQUIRED",
            "consent": "GRANTED",
        }

    def call(self, request=None, profiles=None, products=None):
        return recommend(
            self.request if request is None else request,
            customer_profiles=self.raw["customer_profiles"] if profiles is None else profiles,
            products=self.raw["products"] if products is None else products,
        )

    def assert_blocked(self, result, reason):
        self.assertEqual(result, {
            "status": "ok",
            "data": {"allowed": False, "reason_code": reason, "items": []},
        })

    def test_s05_open_and_under_review_complaints_are_rejected(self) -> None:
        for status in ("OPEN", "UNDER_REVIEW"):
            with self.subTest(status=status):
                self.request["complaint_status"] = status
                self.assert_blocked(self.call(), "UNRESOLVED_COMPLAINT")

    def test_s09_unknown_and_denied_consent_are_rejected(self) -> None:
        for consent in ("UNKNOWN", "DENIED"):
            with self.subTest(consent=consent):
                self.request["consent"] = consent
                self.assert_blocked(self.call(), "CONSENT_REQUIRED")

    def test_unresolved_complaint_precedes_consent_rejection(self) -> None:
        self.request.update(complaint_status="OPEN", consent="DENIED")
        self.assert_blocked(self.call(), "UNRESOLVED_COMPLAINT")

    def test_active_handoff_is_a_fail_closed_invocation_error(self) -> None:
        for status in ("PENDING", "ESCALATED"):
            for complaint in ("NONE", "OPEN", "RESOLVED"):
                with self.subTest(handoff=status, complaint=complaint):
                    self.request.update(handoff_status=status, complaint_status=complaint)
                    self.assertEqual(self.call(), ERROR)

    def test_s10_no_eligible_product_is_a_normal_business_result(self) -> None:
        self.request["session_id"] = "session-002"
        self.assert_blocked(self.call(), "NO_ELIGIBLE_PRODUCT")

    def test_empty_catalog_is_not_a_technical_error(self) -> None:
        self.assert_blocked(self.call(products=[]), "NO_ELIGIBLE_PRODUCT")

    def test_unknown_session_never_falls_back_to_a_default_customer(self) -> None:
        self.request["session_id"] = "not-in-fixtures"
        self.assertEqual(self.call(), ERROR)

    def test_all_four_request_fields_are_required(self) -> None:
        for field in tuple(self.request):
            with self.subTest(field=field):
                request = self.request.copy()
                del request[field]
                self.assertEqual(self.call(request=request), ERROR)

    def test_unknown_fields_and_invalid_enum_values_are_errors(self) -> None:
        self.assertEqual(self.call(request={**self.request, "risk_level": "LOW"}), ERROR)
        for field in ("complaint_status", "handoff_status", "consent"):
            for value in ("INVALID", None, True, 1):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.call(request={**self.request, field: value}), ERROR)

    def test_invalid_request_objects_are_errors(self) -> None:
        for request in ("invalid", [], 42):
            with self.subTest(request=request):
                self.assertEqual(self.call(request=request), ERROR)
        self.assertEqual(recommend(
            None,
            customer_profiles=self.raw["customer_profiles"],
            products=self.raw["products"],
        ), ERROR)

    def test_corrupt_catalog_is_not_silently_partially_recommended(self) -> None:
        products = copy.deepcopy(self.raw["products"])
        products[1]["min_deposit_cents"] = True
        self.assertEqual(self.call(products=products), ERROR)
        products = copy.deepcopy(self.raw["products"])
        products[1]["product_id"] = products[0]["product_id"]
        self.assertEqual(self.call(products=products), ERROR)

    def test_invalid_profile_does_not_become_no_eligible_product(self) -> None:
        profiles = copy.deepcopy(self.raw["customer_profiles"])
        profiles["session-001"]["available_deposit_cents"] = -1
        self.assertEqual(self.call(profiles=profiles), ERROR)

    def test_call_does_not_mutate_inputs(self) -> None:
        before = copy.deepcopy((self.request, self.raw))
        self.call()
        self.assertEqual((self.request, self.raw), before)

    def test_validated_models_are_supported_and_revalidated(self) -> None:
        fixture = load_fixture(FIXTURE)
        result = self.call(profiles=fixture.customer_profiles, products=fixture.products)
        self.assertTrue(result["data"]["allowed"])
        forged = Product.model_construct(**{
            **self.raw["products"][0], "min_deposit_cents": -1,
        })
        self.assertEqual(self.call(products=[forged]), ERROR)

    def test_none_complaint_does_not_create_an_extra_product_gate(self) -> None:
        self.request["complaint_status"] = "NONE"
        self.assertTrue(self.call()["data"]["allowed"])


if __name__ == "__main__":
    unittest.main()
