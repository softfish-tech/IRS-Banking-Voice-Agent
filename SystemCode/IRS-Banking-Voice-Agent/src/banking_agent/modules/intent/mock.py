"""Deterministic Phase-1 implementation of the intent / risk / entity module.

Two layers, on purpose:

1. :data:`SCENARIO_EXAMPLES` pins the exact outputs agreed for the acceptance
   scenarios in ``docs/scenario_table.md`` (S01-S08). Phase one is a mock
   integration phase, so those values are the contract, not a model result.
2. :func:`classify_by_rules` generalises to arbitrary text with weighted
   keyword rules so the module is not limited to the eight fixtures.

The rule layer alone already reproduces the intent and risk of every scenario
example; the pinned table only fixes the calibrated confidence values.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from banking_agent.schemas.enums import RiskLevel
from banking_agent.schemas.state import Entity, UnderstandingResult

from . import taxonomy as tax

_WHITESPACE = re.compile(r"\s+")

UNKNOWN_CONFIDENCE = 0.31
"""Confidence reported when no intent pattern matched (scenario S07)."""

_RULE_CONFIDENCE_BASE = 0.50
_RULE_CONFIDENCE_PER_POINT = 0.09
_RULE_CONFIDENCE_CAP = 0.95


def normalize(text: str) -> str:
    """Fold case and whitespace so rule and entity matching is deterministic."""
    return _WHITESPACE.sub(" ", text.strip().lower())


SCENARIO_EXAMPLES: dict[str, tuple[str, float, RiskLevel]] = {
    # docs/scenario_table.md, "Core scenarios": pinned mock understanding.
    normalize("What is the replacement fee for my card?"): (
        tax.INTENT_CARD_FEE_ENQUIRY,
        0.94,
        RiskLevel.LOW,
    ),  # S01
    normalize("I was charged a fee I do not understand."): (
        tax.INTENT_FEE_COMPLAINT,
        0.92,
        RiskLevel.MEDIUM,
    ),  # S02
    normalize("Someone used my card without my permission."): (
        tax.INTENT_UNAUTHORIZED_TRANSACTION,
        0.97,
        RiskLevel.HIGH,
    ),  # S03
    normalize("I think this transfer may be a scam."): (
        tax.INTENT_FRAUD_SUSPICION,
        0.95,
        RiskLevel.HIGH,
    ),  # S04
    normalize(
        "Can you recommend a savings product while my fee complaint is still open?"
    ): (tax.INTENT_PRODUCT_RECOMMENDATION, 0.91, RiskLevel.LOW),  # S05
    normalize(
        "My complaint is resolved. Can you recommend a suitable savings product?"
    ): (tax.INTENT_PRODUCT_RECOMMENDATION, 0.93, RiskLevel.LOW),  # S06
    normalize("I need help with that thing from before."): (
        tax.UNKNOWN_INTENT,
        UNKNOWN_CONFIDENCE,
        RiskLevel.UNKNOWN,
    ),  # S07
    normalize("What is the bank policy for crypto wallet recovery?"): (
        tax.INTENT_POLICY_ENQUIRY,
        0.88,
        RiskLevel.LOW,
    ),  # S08
}


def score_intent(text: str) -> tuple[str, float]:
    """Return ``(intent, confidence)`` from the weighted keyword rules."""
    normalized = normalize(text)

    best_intent = tax.UNKNOWN_INTENT
    best_score = 0.0
    for intent in tax.INTENT_PRIORITY:
        score = 0.0
        for pattern, weight in tax.INTENT_PATTERNS[intent]:
            if re.search(pattern, normalized):
                score += weight
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_intent == tax.UNKNOWN_INTENT:
        return tax.UNKNOWN_INTENT, UNKNOWN_CONFIDENCE

    confidence = min(
        _RULE_CONFIDENCE_CAP,
        _RULE_CONFIDENCE_BASE + _RULE_CONFIDENCE_PER_POINT * best_score,
    )
    return best_intent, round(confidence, 2)


def detect_risk(text: str, intent: str | None = None) -> RiskLevel:
    """Return the risk signal for ``text``, optionally seeded by ``intent``.

    Risk is the more severe of the phrase level and the intent baseline, so a
    high-risk phrase is never downgraded by a low intent confidence. The value
    is a signal for the Rules module, not a decision.
    """
    normalized = normalize(text)

    phrase_level = RiskLevel.UNKNOWN
    if any(re.search(pattern, normalized) for pattern in tax.HIGH_RISK_PATTERNS):
        phrase_level = RiskLevel.HIGH
    elif any(re.search(pattern, normalized) for pattern in tax.MEDIUM_RISK_PATTERNS):
        phrase_level = RiskLevel.MEDIUM

    baseline = tax.RISK_BASELINE_BY_INTENT.get(intent or "", RiskLevel.UNKNOWN)
    if tax.RISK_ORDER[baseline] > tax.RISK_ORDER[phrase_level]:
        return baseline
    return phrase_level


def _overlaps(span: tuple[int, int], taken: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(
        start < other_end and other_start < end for other_start, other_end in taken
    )


def extract_entities(text: str) -> list[Entity]:
    """Extract the controlled entity types described in ``taxonomy``."""
    normalized = normalize(text)
    found: list[tuple[int, str, str, float]] = []

    for entity_type, entries in tax.ENTITY_GAZETTEER.items():
        taken: list[tuple[int, int]] = []
        for phrase, canonical in sorted(
            entries, key=lambda entry: len(entry[0]), reverse=True
        ):
            pattern = r"\b" + re.escape(phrase) + r"\b"
            for match in re.finditer(pattern, normalized):
                if _overlaps(match.span(), taken):
                    continue
                taken.append(match.span())
                found.append(
                    (
                        match.start(),
                        entity_type,
                        canonical,
                        tax.ENTITY_GAZETTEER_CONFIDENCE,
                    )
                )

    for entity_type, patterns in tax.ENTITY_PATTERNS.items():
        for pattern, group in patterns:
            for match in re.finditer(pattern, normalized):
                value = match.group(group).strip()
                if not value:
                    continue
                found.append(
                    (match.start(), entity_type, value, tax.ENTITY_PATTERN_CONFIDENCE)
                )

    entities: list[Entity] = []
    seen: set[tuple[str, str]] = set()
    for _, entity_type, value, confidence in sorted(
        found, key=lambda item: (item[0], item[1], item[2])
    ):
        key = (entity_type, value)
        if key in seen:
            continue
        seen.add(key)
        entities.append(Entity(type=entity_type, value=value, confidence=confidence))
    return entities


def classify(text: str) -> UnderstandingResult:
    """Analyse ``text`` and return the shared understanding result.

    Scenario acceptance examples return their pinned values; any other text is
    handled by the rule layer.
    """
    pinned = SCENARIO_EXAMPLES.get(normalize(text))
    if pinned is None:
        intent, confidence = score_intent(text)
        risk_level = detect_risk(text, intent)
    else:
        intent, confidence, risk_level = pinned

    return UnderstandingResult(
        intent=intent,
        confidence=confidence,
        risk_level=risk_level,
        entities=extract_entities(text),
    )


def classify_by_rules(text: str) -> UnderstandingResult:
    """Rule-only classification, used to check generalisation and by tests."""
    intent, confidence = score_intent(text)
    return UnderstandingResult(
        intent=intent,
        confidence=confidence,
        risk_level=detect_risk(text, intent),
        entities=extract_entities(text),
    )


def analyze(
    payload: Mapping[str, object],
    *,
    classifier: Callable[[str], UnderstandingResult] = classify,
) -> dict[str, object]:
    """Contract adapter: ``{session_id, user_text}`` -> ``{status, data}``.

    ``classifier`` lets E inject :class:`TrainedIntentClassifier.classify`
    without changing the envelope.
    """
    user_text = payload.get("user_text")
    if not isinstance(user_text, str) or not user_text.strip():
        return {"status": "error", "data": None}
    return {"status": "ok", "data": classifier(user_text).model_dump(mode="json")}
