"""Real B/D adapters used by the phase-one hybrid E2E suite.

A and C remain scenario-scripted until their owner implementations are
available.  B and D deliberately use their delivered public implementations;
the fixture's B/D envelopes are removed before the scripted double is built so
the E2E path cannot silently fall back to them.
"""

from copy import deepcopy
from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from banking_agent.app.persistence import StoreError
from banking_agent.app.recommendation_adapter import ConversationProfileRecommendationAdapter
from banking_agent.app.retrieval_adapter import AsyncRetrievalAdapter
from banking_agent.modules.rag.retriever import create_retriever
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture

from helpers.mock_modules import ScriptedModules


ROOT = Path(__file__).resolve().parents[2]


class DeterministicReranker:
    """Exercise B's real BM25 backend without a downloaded cross-encoder."""

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        del query
        return [
            dict(document, score=float(top_k - index))
            for index, document in enumerate(candidates[:top_k])
        ]


class RecordingModule:
    """Add B/D calls to the shared E2E call trace without changing behavior."""

    def __init__(self, name: str, delegate: Any, calls: list[str]) -> None:
        self._name, self._delegate, self._calls = name, delegate, calls

    async def retrieve(self, query: str, top_k: int) -> Any:
        self._calls.append(self._name)
        return await self._delegate.retrieve(query, top_k)

    async def recommend(
        self, session_id: str, complaint_status: str, handoff_status: str, consent: str
    ) -> Any:
        self._calls.append(self._name)
        return await self._delegate.recommend(session_id, complaint_status, handoff_status, consent)


def scripted_a_and_c(envelopes: dict[str, Any]) -> ScriptedModules:
    """Return only the unavailable A/C doubles for an E2E fixture."""

    scripted = deepcopy(envelopes)
    scripted.pop("B", None)
    scripted.pop("D", None)
    return ScriptedModules(scripted)


@lru_cache
def _real_retriever(mode: str):
    # CI uses the deterministic reranker so it never needs model weights. A
    # prepared local environment can exercise B's complete cached
    # Cross-Encoder path without allowing a download.
    if mode == "cross_encoder":
        return create_retriever("real")
    return create_retriever("real", reranker=DeterministicReranker())


def real_retrieval(calls: list[str]) -> RecordingModule:
    mode = os.environ.get("BANKING_AGENT_E2E_RERANKER", "deterministic")
    retriever = _real_retriever(mode)
    return RecordingModule("B", AsyncRetrievalAdapter(retriever), calls)


def real_recommendation(
    calls: list[str], profile_keys: dict[str, str] | None = None
) -> RecordingModule:
    dataset = load_fixture(ROOT / "data/fixtures/recommendation.json")
    adapter: Any = RecommendationAdapter(dataset)
    if profile_keys is not None:
        def profile_key_for_conversation(conversation_id: str) -> str:
            try:
                return profile_keys[conversation_id]
            except KeyError as exc:
                raise StoreError("synthetic_profile_key_required") from exc

        adapter = ConversationProfileRecommendationAdapter(adapter, profile_key_for_conversation)
    return RecordingModule("D", adapter, calls)
