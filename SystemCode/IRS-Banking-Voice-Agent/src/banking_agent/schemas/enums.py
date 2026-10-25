"""Canonical enums shared across banking-agent modules."""

from enum import StrEnum


class Action(StrEnum):
    """Business actions that the Rules module may return."""

    ANSWER = "ANSWER"
    HANDLE_COMPLAINT = "HANDLE_COMPLAINT"
    ESCALATE = "ESCALATE"
    RECOMMEND = "RECOMMEND"
    CLARIFY = "CLARIFY"
    BLOCK = "BLOCK"
    ABSTAIN = "ABSTAIN"


class ComplaintStatus(StrEnum):
    """Lifecycle states for a simulated customer complaint."""

    NONE = "NONE"
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"


class HandoffStatus(StrEnum):
    """Status of escalation or human-handoff handling."""

    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"


class RiskLevel(StrEnum):
    """Risk assessment returned by the understanding module."""

    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConsentStatus(StrEnum):
    """Whether the customer has granted recommendation consent."""

    UNKNOWN = "UNKNOWN"
    GRANTED = "GRANTED"
    DENIED = "DENIED"


class TranscriptionStatus(StrEnum):
    """Outcome of a local audio-to-text attempt."""

    OK = "OK"
    EMPTY = "EMPTY"
    ERROR = "ERROR"
