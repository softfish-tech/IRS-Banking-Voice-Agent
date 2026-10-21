"""Conservative project-route calibration after BANKING77 inference.

BANKING77 does not contain direct labels for every route in this prototype
(notably a fee complaint, a recommendation request, and anaphoric help
requests).  The learned classifier remains responsible for ordinary banking
language; these auditable patterns only cover project routes whose wording is
unambiguous.  They deliberately return an :class:`UnderstandingResult`, never
a C-owned action or state patch.
"""

from __future__ import annotations

import re

from banking_agent.schemas.state import UnderstandingResult

from .mock import detect_risk
from .taxonomy import (
    INTENT_CARD_FEE_ENQUIRY,
    INTENT_FEE_COMPLAINT,
    INTENT_FRAUD_SUSPICION,
    INTENT_PRODUCT_RECOMMENDATION,
    INTENT_UNAUTHORIZED_TRANSACTION,
    INTENT_POLICY_ENQUIRY,
    UNKNOWN_INTENT,
)


_VAGUE_REQUEST = re.compile(
    r"^\s*(?:can you help (?:with )?(?:that )?(?:bank )?thing|"
    r"i need help with (?:it|that)|what about (?:the )?other one)\s*[?.!]*\s*$",
    re.I,
)
_FRAUD_REPORT = re.compile(
    r"\b(?:scam|fraud(?:ster)?|phishing)\b|"
    r"\b(?:trick(?:ed|ing)?|deceiv(?:e|ed|ing)|coerc(?:e|ed|ing)|pressur(?:e|ed|ing))\b",
    re.I,
)
_UNAUTHORIZED_REPORT = re.compile(
    r"\b(?:unrecogn(?:ised|ized)|unauthori[sz]ed|not mine|never made|"
    r"did not make|didn't make|do not recognise|don't recognise|"
    r"someone (?:used|paid|spent|withdrew))\b",
    re.I,
)
_RECOMMENDATION = re.compile(
    r"\b(?:recommend(?:ation|ations)?|recommend|suggest(?:ion)?)\b|"
    r"\bwhich\s+(?:savings\s+)?(?:product|option|account)\b|"
    r"\bwhat\s+(?:savings\s+)?product\b",
    re.I,
)
_FEE_COMPLAINT = re.compile(
    r"\b(?:charged|charge|fee|fees)\b.{0,80}"
    r"\b(?:do not (?:understand|recognise)|don't (?:understand|recognise)|"
    r"not (?:right|recognised|recognized)|unexpected|dispute|wrong|why)\b|"
    r"\b(?:dispute|unexpected|wrong)\b.{0,80}\b(?:charge|fee)\b",
    re.I,
)
_WHY_CHARGED_FEE = re.compile(
    r"\bwhy\b.{0,60}\bcharged\b.{0,60}\bfee\b", re.I
)
_CARD_FEE_ENQUIRY = re.compile(
    r"\b(?:replacement|replace|replacing)\b.{0,60}\b(?:card|fee|cost|charge|pay)\b|"
    r"\b(?:fee|cost|charge)\b.{0,60}\b(?:replacement|replace|replacing|card)\b",
    re.I,
)
_CRYPTO_POLICY = re.compile(
    r"\b(?:crypto(?:currency)?|wallet)\b.{0,80}\b(?:recover|recovery|restore|restoration|access|lose|lost|losing)\b|"
    r"\b(?:recover|recovery|restore|restoration|lose|lost|losing)\b.{0,80}\b(?:crypto(?:currency)?|wallet)\b",
    re.I,
)


def _route_for(text: str) -> tuple[str, float] | None:
    """Return a project-only route where the text carries enough evidence."""
    if _VAGUE_REQUEST.match(text):
        return UNKNOWN_INTENT, 0.31
    if _FRAUD_REPORT.search(text):
        return INTENT_FRAUD_SUSPICION, 0.93
    # A clear product request must reach C's recommendation gate. C then
    # applies the unresolved-complaint and consent constraints; A must not
    # hide that request merely because the customer mentions an open fee case.
    if _RECOMMENDATION.search(text):
        return INTENT_PRODUCT_RECOMMENDATION, 0.91
    # A disputed fee is a complaint, even when the customer says they do not
    # recognise it. A bare unrecognised purchase remains high-risk below.
    if _FEE_COMPLAINT.search(text) or _WHY_CHARGED_FEE.search(text):
        return INTENT_FEE_COMPLAINT, 0.90
    if _CRYPTO_POLICY.search(text):
        return INTENT_POLICY_ENQUIRY, 0.88
    if _UNAUTHORIZED_REPORT.search(text):
        return INTENT_UNAUTHORIZED_TRANSACTION, 0.93
    if _CARD_FEE_ENQUIRY.search(text):
        return INTENT_CARD_FEE_ENQUIRY, 0.90
    return None


def calibrate_project_route(text: str, result: UnderstandingResult) -> UnderstandingResult:
    """Apply a narrow project-route correction while preserving A's entities.

    The returned risk is recomputed from the calibrated route plus the original
    text.  This prevents a BANKING77-only label from accidentally turning a
    non-risk policy question into a high-risk case, while phrase-level risk is
    still never downgraded.
    """
    calibrated = _route_for(text)
    if calibrated is None:
        return result
    intent, confidence = calibrated
    return result.model_copy(
        update={
            "intent": intent,
            "confidence": confidence,
            "risk_level": detect_risk(text, intent),
        }
    )


__all__ = ["calibrate_project_route"]
