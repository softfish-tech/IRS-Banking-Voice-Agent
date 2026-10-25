"""E-owned binding from an application conversation to D's synthetic profile key."""

from collections.abc import Callable
from typing import Any, Mapping

from banking_agent.app.orchestrator.interfaces import RecommendationModule
from banking_agent.app.persistence import StoreError


class ConversationProfileRecommendationAdapter:
    """Resolve an E conversation ID before delegating to D's public async adapter.

    The mapping is local synthetic-test configuration, not customer authentication.
    Resolution failures deliberately become D technical-error envelopes.
    """

    def __init__(
        self,
        delegate: RecommendationModule,
        profile_key_for_conversation: Callable[[str], str],
    ) -> None:
        self._delegate = delegate
        self._profile_key_for_conversation = profile_key_for_conversation

    async def recommend(
        self,
        session_id: str,
        complaint_status: str,
        handoff_status: str,
        consent: str,
    ) -> Mapping[str, Any]:
        try:
            profile_key = self._profile_key_for_conversation(session_id)
        except StoreError:
            return {"status": "error"}
        return await self._delegate.recommend(
            profile_key, complaint_status, handoff_status, consent
        )
