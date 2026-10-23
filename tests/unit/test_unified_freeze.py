"""Contract checks for the unified freeze runner's local aggregation inputs."""
import unittest

from scripts.run_unified_freeze import _metric_tags, _rate, _summarize


class UnifiedFreezeTests(unittest.TestCase):
    def test_expanded_metric_tags_are_explicit_and_include_requested_diagnostics(self) -> None:
        tags = _metric_tags()
        self.assertIn(("MTX-004", 2), tags)
        self.assertIn("explicit_topic_switch", tags[("MTX-004", 2)])
        self.assertIn("clarification_closure", tags[("MTX-013", 2)])
        self.assertIn("context_reference_resolution", tags[("MTX-013", 3)])

    def test_rate_keeps_its_denominator(self) -> None:
        self.assertEqual(_rate(2, 3), {"passed": 2, "total": 3, "rate": 0.6667})

    def test_summary_keeps_b0_context_oracle_separate_from_pre_context_oracle(self) -> None:
        def row(sequence_id: str, *, category: str = "PASS", context: bool = False, status: str = "success") -> dict:
            value = {
                "sequence_id": sequence_id,
                "case_id": "turn-1",
                "category": category,
                "trace_complete": True,
                "module_call_order_matches": True,
                "expected": {"action": "ANSWER", "status": status},
                "duration_ms": 1,
                "modules": [],
            }
            if context:
                value["context_evaluation"] = {"passed": True}
            return value

        report = {
            "manifest": {"repetitions": 1},
            "core_attempts": [
                row("E2E-MT-SEM-001", category="CONTEXT_PASS", context=True),
                row("E2E-MT-SEM-001", category="SEMANTIC_GAP"),
                row("E2E-MT-STATE-001"),
                row("E2E-MT-STATE-TECH", status="error"),
            ],
            "technical_attempts": [],
            "complex_attempts": [],
        }
        legacy = _summarize(report)["multi_turn"]["legacy"]
        self.assertEqual(legacy["b0_context_follow_up"]["turn_pass"], _rate(1, 1))
        self.assertEqual(legacy["pre_context_legacy_oracle_diagnostic"]["turn_pass"], _rate(0, 1))
        self.assertEqual(legacy["state_workflow"]["turn_pass"], _rate(1, 1))
        self.assertEqual(legacy["technical_fixture"]["attempts"], 1)


if __name__ == "__main__":
    unittest.main()
