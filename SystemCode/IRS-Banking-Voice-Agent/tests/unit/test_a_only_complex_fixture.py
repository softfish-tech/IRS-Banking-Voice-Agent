import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests/fixtures/evaluation/a_only_complex/v1/development.json"
HOLDOUT = ROOT / "tests/fixtures/evaluation/a_only_complex/v1/holdout.json"


class AOnlyComplexFixtureTests(unittest.TestCase):
    def test_reviewed_development_set_has_the_planned_family_counts(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "a-only-complex-v1")
        cases = payload["cases"]
        self.assertEqual(len(cases), 36)
        self.assertEqual(len({case["case_id"] for case in cases}), 36)
        counts = {family: sum(case["family"] == family for case in cases) for family in {case["family"] for case in cases}}
        self.assertEqual(counts, {"natural_variation": 12, "multi_intent_priority": 6, "ambiguity": 6, "recommendation_constraints": 4, "grounding_trap": 4, "safety_adversarial": 4})
        for case in cases:
            self.assertTrue(case["input"])
            self.assertIn("understanding", case)
            self.assertIn("decision", case)

    def test_holdout_is_disjoint_and_balanced(self) -> None:
        development = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
        holdout = json.loads(HOLDOUT.read_text(encoding="utf-8"))
        self.assertEqual(holdout["schema_version"], "a-only-complex-v1")
        self.assertEqual(len(holdout["cases"]), 12)
        self.assertTrue({case["case_id"] for case in development}.isdisjoint(case["case_id"] for case in holdout["cases"]))
        self.assertEqual({case["family"] for case in holdout["cases"]}, {"natural_variation", "multi_intent_priority", "ambiguity", "recommendation_constraints", "grounding_trap", "safety_adversarial"})


if __name__ == "__main__":
    unittest.main()
