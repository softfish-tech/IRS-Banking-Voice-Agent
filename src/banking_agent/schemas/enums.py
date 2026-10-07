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


class ComplaintStatus(StrEnum):
    """Lifecycle states for a simulated customer complaint."""

    NONE = "NONE"
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
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


class EligibilityStatus(StrEnum):
    """Eligibility fact supplied by the synthetic data/recommendation domain."""

    UNKNOWN = "UNKNOWN"
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
