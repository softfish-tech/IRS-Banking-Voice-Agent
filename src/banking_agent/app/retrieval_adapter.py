"""E-owned async bridge for B's public synchronous retrieval interface."""

import asyncio
from collections.abc import Mapping
from typing import Any

from banking_agent.modules.rag.retriever import Retriever


class AsyncRetrievalAdapter:
    """Call an injected B retriever without blocking the orchestrator event loop.

    The adapter deliberately knows only B's public ``Retriever.retrieve``
    method.  Retrieval ranking, evidence selection, and envelope contents stay
    owned by B; an unexpected backend exception is converted into the public
    technical-error envelope so E can fail the request closed.
    """

    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    async def retrieve(self, query: str, top_k: int) -> Mapping[str, Any]:
        try:
            return await asyncio.to_thread(self._retriever.retrieve, query, top_k)
        except Exception:
            # Do not leak backend exception details through the orchestration
            # boundary.  The orchestrator records only its sanitized B error.
            return {"status": "error"}
