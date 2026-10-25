"""Keep the small semantic scorecard aligned with the maintained E2E seed data."""

import json
from pathlib import Path
import re
import unittest

from scripts.evaluate_real_llm_e2e import FORBIDDEN_PATTERN_RUBRICS, RESPONSE_FACT_RUBRICS

ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = ROOT / "tests/fixtures/evaluation/semantic/v1"
E2E_ROOT = ROOT / "tests/e2e/single_turn"
MULTI_TURN_ROOT = ROOT / "tests/e2e/multi_turn"


def _scorecard_cases() -> list[dict]:
    payloads = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURE_ROOT.glob("single_turn*.json"))
    ]
    if not all(payload["schema_version"] == "semantic-eval-v1" for payload in payloads):
        raise AssertionError("unsupported semantic scorecard version")
    return [case for payload in payloads for case in payload["cases"]]


class SemanticEvaluationFixtureTests(unittest.TestCase):
    def test_scorecards_cover_all_non_technical_single_turn_cases_once(self) -> None:
        cases = _scorecard_cases()
        expected_source_ids = {
            case["case_id"]
            for path in E2E_ROOT.glob("*.json")
            for case in json.loads(path.read_text(encoding="utf-8"))["cases"]
            if case["scenario_id"] != "T01"
        }
        self.assertEqual(len(cases), 40)
        self.assertEqual({case["source_case_id"] for case in cases}, expected_source_ids)
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))
        self.assertTrue(all(case["review_status"] for case in cases))

    def test_each_scorecard_case_references_a_maintained_e2e_case(self) -> None:
        source_ids = {
            case["case_id"]
            for path in E2E_ROOT.glob("*.json")
            for case in json.loads(path.read_text(encoding="utf-8"))["cases"]
        }
        self.assertTrue({case["source_case_id"] for case in _scorecard_cases()} <= source_ids)

    def test_policy_and_recommendation_gold_is_explicit(self) -> None:
        cases = {case["case_id"]: case for case in _scorecard_cases()}
        self.assertEqual(
            cases["SEM-S01-LOST-CARD-FEE"]["decision"]["action"],
            "ESCALATE",
        )
        self.assertEqual(
            cases["SEM-S06-PERMITTED-SAVINGS-RECOMMENDATION"]["recommendation"]["required_product_ids"],
            ["savings-premium", "savings-flex", "emergency-reserve"],
        )

    def test_response_fact_groups_are_reviewable_regex_alternatives(self) -> None:
        for case in _scorecard_cases():
            response = case.get("response", {})
            for group in response.get("required_fact_groups", []):
                with self.subTest(case=case["case_id"], group=group["id"]):
                    self.assertTrue(group["id"])
                    self.assertTrue(group["any_of"])
                    for pattern in group["any_of"]:
                        re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
            for pattern in response.get("forbidden_patterns", []):
                re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)

    def test_final_answer_semantic_rubrics_cover_all_reviewed_response_labels(self) -> None:
        payloads = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(FIXTURE_ROOT.glob("single_turn*.json"))
        ]
        response_records = [
            case["response"]
            for payload in payloads for case in payload["cases"]
            if case.get("response")
        ]
        supplements = json.loads(
            (FIXTURE_ROOT / "response_supplements_v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(supplements["schema_version"], "response-supplements-v1")
        response_records.extend(supplements["complex"].values())
        response_records.extend(supplements["legacy"].values())
        response_records.extend(supplements["expanded"].values())
        required_ids = {
            group["id"]
            for response in response_records
            for group in response.get("required_fact_groups", [])
        }
        forbidden_patterns = {
            pattern
            for response in response_records
            for pattern in response.get("forbidden_patterns", [])
        }
        self.assertTrue(required_ids <= RESPONSE_FACT_RUBRICS.keys())
        self.assertTrue(forbidden_patterns <= FORBIDDEN_PATTERN_RUBRICS.keys())

    def test_legacy_response_supplements_cover_declared_text_quality_turns(self) -> None:
        supplements = json.loads(
            (FIXTURE_ROOT / "response_supplements_v1.json").read_text(encoding="utf-8")
        )
        expected = {
            f"{sequence['sequence_id']}:{turn_id}"
            for path in MULTI_TURN_ROOT.glob("**/*.json")
            for sequence in [json.loads(path.read_text(encoding="utf-8"))]
            for turn_id, turn in enumerate(sequence["turns"], start=1)
            if turn["expected"].get("action") in {"ANSWER", "CLARIFY"}
        }
        self.assertEqual(set(supplements["legacy"]), expected)

    def test_ambiguous_understanding_gold_declares_allowed_routes(self) -> None:
        cases = {case["case_id"]: case for case in _scorecard_cases()}
        self.assertEqual(
            {entry["risk_level"] for entry in cases["SEM-S05-OPEN-COMPLAINT-BLOCKS-RECOMMENDATION"]["understanding"]["allowed"]},
            {"LOW", "MEDIUM"},
        )


if __name__ == "__main__":
    unittest.main()
