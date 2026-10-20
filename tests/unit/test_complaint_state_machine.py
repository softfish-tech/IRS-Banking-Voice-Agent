"""Module C complaint lifecycle guards."""

import unittest

from banking_agent.modules.rules import ComplaintSnapshot, ComplaintStateMachine, InvalidTransition
from banking_agent.schemas.enums import ComplaintStatus, HandoffStatus


class ComplaintStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = ComplaintStateMachine()

    def test_open_review_resolve_requires_human_evidence(self) -> None:
        opened = self.machine.transition(ComplaintStatus.NONE, "OPEN", actor="agent")
        self.assertEqual(opened, ComplaintStatus.OPEN)
        reviewed = self.machine.transition(opened, "START_REVIEW", actor="human_agent")
        self.assertEqual(reviewed, ComplaintStatus.UNDER_REVIEW)
        resolved = self.machine.transition(
            reviewed, "RESOLVE", actor="human_agent", evidence_ref="case-note:123"
        )
        self.assertEqual(resolved, ComplaintStatus.RESOLVED)

    def test_case_creation_alone_never_marks_resolved(self) -> None:
        opened = self.machine.transition(ComplaintStatus.NONE, "OPEN", actor="agent")
        self.assertNotEqual(opened, ComplaintStatus.RESOLVED)

    def test_cannot_skip_review(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "COMPLAINT_NOT_UNDER_REVIEW"):
            self.machine.transition(
                ComplaintStatus.OPEN, "RESOLVE", actor="human_agent",
                evidence_ref="case-note:123",
            )

    def test_resolve_rejects_automated_actor_and_missing_evidence(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "HUMAN_RESOLUTION_REQUIRED"):
            self.machine.transition(
                ComplaintStatus.UNDER_REVIEW, "RESOLVE", actor="agent",
                evidence_ref="case-note:123",
            )
        with self.assertRaisesRegex(InvalidTransition, "RESOLUTION_EVIDENCE_REQUIRED"):
            self.machine.transition(
                ComplaintStatus.UNDER_REVIEW, "RESOLVE", actor="human_agent",
            )

    def test_cannot_open_duplicate_active_complaint(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "ACTIVE_COMPLAINT_EXISTS"):
            self.machine.transition(ComplaintStatus.OPEN, "OPEN", actor="agent")

    def test_case_revision_and_duplicate_event_guard(self) -> None:
        opened = self.machine.transition_case(
            ComplaintSnapshot(), "OPEN", actor="agent",
            event_id="event-001", expected_revision=0,
        )
        self.assertEqual(opened.status, ComplaintStatus.OPEN)
        self.assertEqual(opened.revision, 1)
        with self.assertRaisesRegex(InvalidTransition, "DUPLICATE_EVENT_ID"):
            self.machine.transition_case(
                opened, "START_REVIEW", actor="human_agent",
                event_id="event-001", expected_revision=1,
            )
        with self.assertRaisesRegex(InvalidTransition, "STALE_CASE_REVISION"):
            self.machine.transition_case(
                opened, "START_REVIEW", actor="human_agent",
                event_id="event-002", expected_revision=0,
            )

    def test_escalated_case_needs_human_clearance_before_resolution(self) -> None:
        escalated = self.machine.transition_case(
            ComplaintSnapshot(), "ESCALATE", actor="agent",
            event_id="event-001", expected_revision=0,
        )
        self.assertEqual(escalated.status, ComplaintStatus.OPEN)
        self.assertEqual(escalated.handoff_status, HandoffStatus.ESCALATED)
        reviewed = self.machine.transition_case(
            escalated, "START_REVIEW", actor="human_agent",
            event_id="event-002", expected_revision=1,
        )
        with self.assertRaisesRegex(InvalidTransition, "HANDOFF_CLEARANCE_REQUIRED"):
            self.machine.transition_case(
                reviewed, "RESOLVE", actor="human_agent",
                event_id="event-003", expected_revision=2,
                evidence_ref="case-note:123",
            )
        resolved = self.machine.transition_case(
            reviewed, "RESOLVE", actor="human_agent",
            event_id="event-003", expected_revision=2,
            evidence_ref="case-note:123", handoff_cleared=True,
        )
        self.assertEqual(resolved.status, ComplaintStatus.RESOLVED)
        self.assertEqual(resolved.handoff_status, HandoffStatus.NOT_REQUIRED)
        self.assertEqual(resolved.resolution_evidence_ref, "case-note:123")
        self.assertEqual(resolved.revision, 3)

    def test_reopened_case_clears_prior_resolution_reference(self) -> None:
        previous = ComplaintSnapshot(
            status=ComplaintStatus.RESOLVED,
            revision=3,
            resolution_evidence_ref="prior-case-note",
        )
        reopened = self.machine.transition_case(
            previous, "OPEN", actor="agent", event_id="event-004",
            expected_revision=3,
        )
        self.assertEqual(reopened.status, ComplaintStatus.OPEN)
        self.assertIsNone(reopened.resolution_evidence_ref)

    def test_human_review_and_resolution_reject_customer_or_agent(self) -> None:
        opened = ComplaintSnapshot(status=ComplaintStatus.OPEN)
        with self.assertRaisesRegex(InvalidTransition, "HUMAN_REVIEW_REQUIRED"):
            self.machine.transition_case(
                opened, "START_REVIEW", actor="customer",
                event_id="event-001", expected_revision=0,
            )
        review = ComplaintSnapshot(status=ComplaintStatus.UNDER_REVIEW)
        with self.assertRaisesRegex(InvalidTransition, "HUMAN_RESOLUTION_REQUIRED"):
            self.machine.transition_case(
                review, "RESOLVE", actor="agent",
                event_id="event-001", expected_revision=0,
                evidence_ref="customer-says-resolved",
            )


if __name__ == "__main__":
    unittest.main()
