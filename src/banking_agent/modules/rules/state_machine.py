"""Complaint lifecycle transitions owned by Module C.

E must authenticate the actor and retain the evidence reference in its audit
store before applying a RESOLVED state patch. The current shared AgentState has
no resolution-evidence field, so this module cannot persist that reference.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from banking_agent.schemas.enums import ComplaintStatus, HandoffStatus


ComplaintEvent = Literal["OPEN", "START_REVIEW", "ESCALATE", "RESOLVE"]


class InvalidTransition(ValueError):
    """The requested complaint transition is not allowed."""


@dataclass(frozen=True)
class ComplaintSnapshot:
    """C-owned case metadata that E may persist beside canonical AgentState.

    ``revision`` supports optimistic concurrency.  E must additionally enforce
    unique event IDs over the full case history and authenticate actor roles.
    """

    status: ComplaintStatus = ComplaintStatus.NONE
    handoff_status: HandoffStatus = HandoffStatus.NOT_REQUIRED
    revision: int = 0
    last_event_id: str | None = None
    resolution_evidence_ref: str | None = None


class ComplaintStateMachine:
    """Validate case transitions without trusting customer claims of resolution."""

    def transition_case(
        self,
        current: ComplaintSnapshot,
        event: ComplaintEvent,
        *,
        actor: str,
        event_id: str,
        expected_revision: int,
        evidence_ref: str | None = None,
        handoff_cleared: bool = False,
    ) -> ComplaintSnapshot:
        """Return a new case snapshot, or reject a stale/unauthorized event.

        ``handoff_cleared`` must be based on an authenticated human action, not
        customer text.  A resolution never follows directly from opening.
        """

        if expected_revision != current.revision:
            raise InvalidTransition("STALE_CASE_REVISION")
        if not event_id or not event_id.strip():
            raise InvalidTransition("EVENT_ID_REQUIRED")
        if event_id == current.last_event_id:
            raise InvalidTransition("DUPLICATE_EVENT_ID")
        if current.revision < 0:
            raise InvalidTransition("INVALID_CASE_REVISION")

        if event == "OPEN":
            if current.status not in (ComplaintStatus.NONE, ComplaintStatus.RESOLVED):
                raise InvalidTransition("ACTIVE_COMPLAINT_EXISTS")
            if actor not in ("agent", "human_agent"):
                raise InvalidTransition("COMPLAINT_ACTOR_REQUIRED")
            updated = replace(
                current,
                status=ComplaintStatus.OPEN,
                resolution_evidence_ref=None,
            )
        elif event == "START_REVIEW":
            if current.status != ComplaintStatus.OPEN:
                raise InvalidTransition("COMPLAINT_NOT_OPEN")
            if actor != "human_agent":
                raise InvalidTransition("HUMAN_REVIEW_REQUIRED")
            updated = replace(current, status=ComplaintStatus.UNDER_REVIEW)
        elif event == "ESCALATE":
            if actor not in ("agent", "human_agent"):
                raise InvalidTransition("COMPLAINT_ACTOR_REQUIRED")
            updated = replace(
                current,
                status=(
                    ComplaintStatus.OPEN
                    if current.status in (ComplaintStatus.NONE, ComplaintStatus.RESOLVED)
                    else current.status
                ),
                handoff_status=HandoffStatus.ESCALATED,
                resolution_evidence_ref=None,
            )
        elif event == "RESOLVE":
            if current.status != ComplaintStatus.UNDER_REVIEW:
                raise InvalidTransition("COMPLAINT_NOT_UNDER_REVIEW")
            if actor != "human_agent":
                raise InvalidTransition("HUMAN_RESOLUTION_REQUIRED")
            if not evidence_ref or not evidence_ref.strip():
                raise InvalidTransition("RESOLUTION_EVIDENCE_REQUIRED")
            if current.handoff_status != HandoffStatus.NOT_REQUIRED and not handoff_cleared:
                raise InvalidTransition("HANDOFF_CLEARANCE_REQUIRED")
            updated = replace(
                current,
                status=ComplaintStatus.RESOLVED,
                handoff_status=HandoffStatus.NOT_REQUIRED,
                resolution_evidence_ref=evidence_ref.strip(),
            )
        else:
            raise InvalidTransition("UNKNOWN_COMPLAINT_EVENT")
        return replace(updated, revision=current.revision + 1, last_event_id=event_id)

    def transition(
        self,
        current: ComplaintStatus,
        event: ComplaintEvent,
        *,
        actor: str,
        evidence_ref: str | None = None,
    ) -> ComplaintStatus:
        """Compatibility helper for status-only local tests and simple callers."""

        return self.transition_case(
            ComplaintSnapshot(status=current), event,
            actor=actor, event_id="status-only-event", expected_revision=0,
            evidence_ref=evidence_ref,
        ).status
