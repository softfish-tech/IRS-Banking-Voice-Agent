"""Tests for the canonical shared state contract."""

import unittest

from pydantic import ValidationError

from banking_agent.schemas import (
    Action,
    AgentState,
    ComplaintStatus,
    Decision,
    HandoffStatus,
    RiskLevel,
    RuleStatePatch,
)


class AgentStateSchemaTests(unittest.TestCase):
    def test_defaults_are_safe_and_empty(self) -> None:
        state = AgentState(session_id="session-001", user_text="Hello")

        self.assertEqual(state.understanding.risk_level, RiskLevel.UNKNOWN)
        self.assertEqual(state.complaint_status, ComplaintStatus.NONE)
        self.assertEqual(state.handoff_status, HandoffStatus.NOT_REQUIRED)
        self.assertEqual(state.retrieved_docs, [])
        self.assertEqual(state.recommendations, [])

    def test_rule_decision_uses_a_whitelisted_state_patch(self) -> None:
        state = AgentState(
            session_id="session-001",
            user_text="My card was used without permission.",
            decision=Decision(
                action=Action.ESCALATE,
                reason_code="HIGH_RISK_TRANSACTION",
                next_state=RuleStatePatch(
                    complaint_status=ComplaintStatus.OPEN,
                    handoff_status=HandoffStatus.ESCALATED,
                ),
            ),
        )

        self.assertEqual(state.decision.action, Action.ESCALATE)
        self.assertEqual(
            state.decision.next_state.complaint_status, ComplaintStatus.OPEN
        )
        self.assertEqual(
            state.decision.next_state.handoff_status, HandoffStatus.ESCALATED
        )

    def test_abstain_is_a_supported_action(self) -> None:
        decision = Decision(
            action=Action.ABSTAIN,
            reason_code="INSUFFICIENT_EVIDENCE",
        )

        self.assertEqual(decision.action, Action.ABSTAIN)

    def test_unknown_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AgentState(
                session_id="session-001",
                user_text="Hello",
                unapproved_field="not allowed",
            )


if __name__ == "__main__":
    unittest.main()
