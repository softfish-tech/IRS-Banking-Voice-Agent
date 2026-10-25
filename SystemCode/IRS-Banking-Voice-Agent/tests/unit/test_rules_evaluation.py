"""Synthetic safety benchmark stays aligned with the implemented C policy."""

import unittest

from banking_agent.modules.rules.evaluate_rules import evaluate_matrix


class RulesEvaluationTests(unittest.TestCase):
    def test_decision_matrix_has_no_safety_regressions(self) -> None:
        report = evaluate_matrix()
        self.assertEqual(report["cases"], 31)
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["safe_escalation_rate"], 1.0)
        self.assertEqual(report["recommendation_violation_rate"], 0.0)
        self.assertEqual(report["unsupported_answer_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
