"""Validate synthetic recommendation fixtures and reject ambiguous inputs."""

import copy
import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from banking_agent.modules.recommendation.data import SyntheticFixture, load_fixture

FIXTURE = Path(__file__).resolve().parents[2] / "data/fixtures/recommendation.json"


class RecommendationDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_contains_synthetic_customers_and_products(self) -> None:
        fixture = load_fixture(FIXTURE)
        self.assertTrue(fixture.synthetic)
        self.assertEqual(len(fixture.customer_profiles), 4)
        self.assertEqual(len(fixture.products), 3)
        self.assertEqual(
            fixture.customer_profiles["session-001"].available_deposit_cents,
            150000,
        )

    def test_rejects_false_or_non_boolean_synthetic_marker(self) -> None:
        for marker in (False, 1, "true", None):
            with self.subTest(marker=marker):
                raw = copy.deepcopy(self.raw)
                raw["synthetic"] = marker
                with self.assertRaises(ValidationError):
                    SyntheticFixture.model_validate(raw)

    def test_rejects_invalid_customer_numbers_without_coercion(self) -> None:
        for field in ("age", "available_deposit_cents"):
            for value in (-1, True, 18.0, "18", None):
                with self.subTest(field=field, value=value):
                    raw = copy.deepcopy(self.raw)
                    raw["customer_profiles"]["session-001"][field] = value
                    with self.assertRaises(ValidationError):
                        SyntheticFixture.model_validate(raw)

    def test_rejects_invalid_product_numbers_without_coercion(self) -> None:
        for field in ("min_age", "min_deposit_cents", "demo_priority"):
            for value in (-1, False, 1.0, "1", None):
                with self.subTest(field=field, value=value):
                    raw = copy.deepcopy(self.raw)
                    raw["products"][0][field] = value
                    with self.assertRaises(ValidationError):
                        SyntheticFixture.model_validate(raw)

    def test_rejects_duplicate_product_ids(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["products"][1]["product_id"] = raw["products"][0]["product_id"]
        with self.assertRaises(ValidationError):
            SyntheticFixture.model_validate(raw)

    def test_rejects_blank_fields_and_session_keys(self) -> None:
        for location, field in (("customer", "goal"), ("product", "product_id")):
            with self.subTest(location=location):
                raw = copy.deepcopy(self.raw)
                target = raw["customer_profiles"]["session-001"] if location == "customer" else raw["products"][0]
                target[field] = "   "
                with self.assertRaises(ValidationError):
                    SyntheticFixture.model_validate(raw)
        raw = copy.deepcopy(self.raw)
        raw["customer_profiles"][" "] = raw["customer_profiles"].pop("session-001")
        with self.assertRaises(ValidationError):
            SyntheticFixture.model_validate(raw)

    def test_rejects_empty_product_conditions(self) -> None:
        for field in ("eligible_residencies", "supported_goals"):
            with self.subTest(field=field):
                raw = copy.deepcopy(self.raw)
                raw["products"][0][field] = []
                with self.assertRaises(ValidationError):
                    SyntheticFixture.model_validate(raw)

    def test_rejects_unapproved_customer_fields(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["customer_profiles"]["session-001"]["unapproved_field"] = "not allowed"
        with self.assertRaises(ValidationError):
            SyntheticFixture.model_validate(raw)

    def test_missing_customer_field_is_not_defaulted(self) -> None:
        raw = copy.deepcopy(self.raw)
        del raw["customer_profiles"]["session-001"]["available_deposit_cents"]
        with self.assertRaises(ValidationError):
            SyntheticFixture.model_validate(raw)

    def test_empty_catalog_is_valid_and_can_represent_no_candidates(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["products"] = []
        self.assertEqual(SyntheticFixture.model_validate(raw).products, ())


if __name__ == "__main__":
    unittest.main()
