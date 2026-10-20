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

    async def analyze(self, session_id: str, user_text: str) -> dict[str, object]:
        """Return one contract envelope for a single user turn.

        ``session_id`` is accepted for protocol compatibility but deliberately
        unused: A neither reads nor writes conversation state.
        """
        return analyze(
            {"session_id": session_id, "user_text": user_text},
            classifier=self._classifier,
        )


__all__ = ["IntentModuleAdapter"]
