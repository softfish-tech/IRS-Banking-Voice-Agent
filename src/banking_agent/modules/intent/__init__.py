"""Intent, risk, and entity extraction module (Part A).

Phase one exposes :func:`classify`, a deterministic implementation of the
module API contract in ``docs/module_api_contract.md`` (section A):

    {"status": "ok", "data": {"intent": ..., "confidence": ...,
                              "risk_level": ..., "entities": [...]}}

The module never returns an ``action``, a ``reason_code``, or a final response;
those belong to the Rules module (C). It also never reads business state such
as the complaint status, so it cannot decide whether a recommendation is
permitted.

:class:`TrainedIntentClassifier` is the opt-in Phase-two implementation of the
same ``classify(text)`` shape; see ``docs/intent_module.md``.

:class:`EncoderIntentClassifier` is the published frozen MiniLM +
logistic-regression implementation of that same shape. Its NumPy/torch
dependencies are loaded lazily, so importing this package stays lightweight.

:class:`IntentModuleAdapter` is the async E-facing adapter:
``await IntentModuleAdapter().analyze(session_id, user_text)``.
"""

from .adapter import IntentModuleAdapter
from .classifier import TrainedIntentClassifier
from .encoder_classifier import EncoderArtifactError, EncoderIntentClassifier
from .mock import (
    analyze,
    classify,
    classify_by_rules,
    detect_risk,
    extract_entities,
    score_intent,
)
from .project_calibration import calibrate_project_route

__all__ = [
    "IntentModuleAdapter",
    "EncoderArtifactError",
    "EncoderIntentClassifier",
    "TrainedIntentClassifier",
    "analyze",
    "classify",
    "classify_by_rules",
    "calibrate_project_route",
    "detect_risk",
    "extract_entities",
    "score_intent",
]
