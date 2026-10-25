"""Shape checks for the post-B0 multi-turn E2E candidate population."""

import json
from pathlib import Path
import unittest


FIXTURE = Path("tests/fixtures/evaluation/multi_turn_semantic/v1/expanded_e2e.json")
ANNOTATIONS = Path(
    "tests/fixtures/evaluation/multi_turn_semantic/v1/expanded_e2e_annotations.json"
)


class ExpandedMultiTurnSemanticFixtureTests(unittest.TestCase):
    def test_candidate_population_is_complete_and_kept_out_of_b0_freeze(self) -> None:
        data = json.loads(FIXTURE.read_text())
        self.assertEqual(data["status"], "approved_for_freeze")
        self.assertEqual(data["sequence_count"], 13)
        self.assertEqual(data["turn_count"], 39)
        self.assertEqual(len(data["sequences"]), 13)
        self.assertEqual(sum(len(item["turns"]) for item in data["sequences"]), 39)
        self.assertEqual(len({item["id"] for item in data["sequences"]}), 13)
        for sequence in data["sequences"]:
            self.assertEqual(len(sequence["turns"]), 3)
            for turn in sequence["turns"]:
                self.assertIn(turn["action"], {"ANSWER", "ABSTAIN", "BLOCK", "CLARIFY", "ESCALATE", "HANDLE_COMPLAINT"})

    def test_annotation_overlay_tracks_every_candidate_turn_without_claiming_approval(self) -> None:
        fixture = json.loads(FIXTURE.read_text())
        annotations = json.loads(ANNOTATIONS.read_text())
        self.assertEqual(annotations["status"], "approved_for_freeze")
        self.assertEqual(annotations["summary"]["approved_for_freeze_sequences"], 13)
        self.assertEqual(
            annotations["approval"]["mtx_002_turn_2_resolution"], "not_required"
        )
        self.assertEqual(annotations["summary"]["requires_policy_review_sequences"], 0)
        self.assertEqual(
            {item["id"] for item in fixture["sequences"]},
            {item["sequence_id"] for item in annotations["sequences"]},
        )
        self.assertEqual(
            sum(len(item["turn_oracles"]) for item in annotations["sequences"]),
            fixture["turn_count"],
        )
        for sequence in annotations["sequences"]:
            self.assertIn(
                sequence["review_status"],
                {"approved_for_freeze"},
            )
            for turn in sequence["turn_oracles"]:
                self.assertIn("turn_id", turn)
                self.assertIn("decision", turn)


if __name__ == "__main__":
    unittest.main()
