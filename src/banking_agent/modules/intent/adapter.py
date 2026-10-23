"""Async adapter that plugs Part A into E's orchestrator.

E calls ``await adapter.analyze(session_id, user_text)`` and validates the
returned mapping as ``banking_agent.schemas.module_results.IntentResult``.
The domain implementation stays in :mod:`banking_agent.modules.intent.mock`;
this class only adapts the call shape.
"""

from __future__ import annotations

from collections.abc import Callable

from banking_agent.schemas.state import UnderstandingResult

from .mock import analyze, classify
from .project_calibration import calibrate_project_route


class IntentModuleAdapter:
    """Async implementation of E's ``IntentModule`` protocol.

    ``classifier`` is injectable so the same adapter can serve the Phase-one
    rules or a loaded :class:`TrainedIntentClassifier`.
    """

    def __init__(
        self,
        *,
        classifier: Callable[[str], UnderstandingResult] = classify,
    ) -> None:
        self._classifier = classifier
        # The deterministic phase-one implementation already owns its pinned
        # scenario values and project rules. Calibration is for an injected
        # BANKING77-backed classifier, whose label space lacks some project
        # routes; do not perturb the mock's contractual confidences.
        self._calibrate_project_routes = classifier is not classify

    async def analyze(self, session_id: str, user_text: str) -> dict[str, object]:
        """Return one contract envelope for a single user turn.

        ``session_id`` is accepted for protocol compatibility but deliberately
        unused: A neither reads nor writes conversation state.
        """
        classifier = self._classifier
        if self._calibrate_project_routes:
            classifier = lambda text: calibrate_project_route(text, self._classifier(text))
        return analyze(
            {"session_id": session_id, "user_text": user_text},
            classifier=classifier,
        )


__all__ = ["IntentModuleAdapter"]
