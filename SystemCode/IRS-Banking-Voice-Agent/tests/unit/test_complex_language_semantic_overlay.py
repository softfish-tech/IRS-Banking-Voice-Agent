import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[2]
OVERLAY_DIR = ROOT / "tests/fixtures/evaluation/semantic/v1"


class ComplexLanguageSemanticOverlayTests(unittest.TestCase):
    def test_overlays_are_complete_disjoint_and_reference_only_source_cases(self) -> None:
        for split, expected_count in (("development", 36), ("holdout", 12)):
            source_path = ROOT / f"tests/fixtures/evaluation/a_only_complex/v1/{split}.json"
            overlay_path = OVERLAY_DIR / f"complex_language_{split}.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
            self.assertEqual(overlay["schema_version"], "complex-language-semantic-v1")
            self.assertEqual(overlay["source_fixture"], str(source_path.relative_to(ROOT)))
            cases = overlay["cases"]
            self.assertEqual(len(cases), expected_count)
            self.assertEqual({case["case_id"] for case in cases}, {case["case_id"] for case in source["cases"]})
            for case in cases:
                self.assertNotIn("input", case)
                self.assertIn("decision", case)
                self.assertIn("review_status", case)
                self.assertTrue(case["retrieval"].get("must_call_b") or case["retrieval"].get("must_not_call_b") or case["retrieval"].get("required_document_ids") or case["retrieval"].get("selected_document_count") is not None)
                if case["decision"]["action"] == "RECOMMEND":
                    self.assertIn("evaluation_session_id", case)
                    self.assertTrue(case["recommendation"].get("required_product_ids"))


if __name__ == "__main__":
    unittest.main()
