"""Phase-one retrieval boundary and deterministic scenario mock.

This mock recognises explicit fixture queries only; it is not a search engine.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Literal, Protocol, TypedDict


class EvidenceDocument(TypedDict):
    document_id: str
    title: str
    source: str
    score: float
    excerpt: str


class EvidenceData(TypedDict):
    docs: list[EvidenceDocument]


class RetrievalResult(TypedDict):
    status: Literal["ok", "empty", "error"]
    data: EvidenceData


class Retriever(Protocol):
    """Public callable contract shared by mocks and future search backends."""

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult: ...



def validate_result(result: object, top_k: int) -> RetrievalResult:
    """Enforce E's exact envelope and canonical document schema at the boundary.

    Bad backend output is a technical failure, not an empty business result.
    No fields are added to the shared state or evidence schema.
    """
    from banking_agent.schemas.state import RetrievedDocument
    if not isinstance(result, dict) or set(result) != {'status', 'data'}:
        raise ValueError('Invalid retrieval envelope')
    status, data = result['status'], result['data']
    if status not in ('ok', 'empty', 'error') or not isinstance(data, dict) or set(data) != {'docs'}:
        raise ValueError('Invalid retrieval status/data')
    docs = data['docs']
    if not isinstance(docs, list) or len(docs) > top_k:
        raise ValueError('Invalid document list')
    if (status == 'ok') != bool(docs):
        raise ValueError('Status/documents mismatch')
    validated = []
    seen = set()
    for doc in docs:
        if not isinstance(doc, dict) or set(doc) != {'document_id', 'title', 'source', 'score', 'excerpt'}:
            raise ValueError('Invalid evidence fields')
        if isinstance(doc['score'], bool) or not isinstance(doc['score'], (float, int)) or not math.isfinite(doc['score']):
            raise ValueError('Invalid evidence score')
        item = RetrievedDocument.model_validate(doc).model_dump()
        if any(not item[k].strip() for k in ('document_id', 'title', 'source', 'excerpt')):
            raise ValueError('Blank evidence field')
        if item['document_id'] in seen:
            raise ValueError('Duplicate evidence ID')
        seen.add(item['document_id'])
        validated.append(item)
    return {'status': status, 'data': {'docs': validated}}


def log_retrieval_failure(exc: Exception) -> None:
    """Log only the exception class; queries, excerpts and secrets stay out."""
    logging.getLogger(__name__).error('RAG request failed (%s)', type(exc).__name__)

DEFAULT_CHUNKS = Path(__file__).parent / "chunks/NovaBank_knowledge_chunks_v1_1.jsonl"
REPLACEMENT_CHUNK = "NB-v1_1-lost_or_stolen_card-002"
MOCK_QUERIES = frozenset({
    "what is the replacement fee for my card?",
    "what are the bank's card replacement fees?",
    "how much does replacing a lost card cost?",
})


class MockRetriever:
    """Serve S01 evidence from the maintained corpus; other queries are empty.

    The fixed score 1.0 identifies a fixture match, not semantic confidence.
    Corpus failures return error, never fabricated evidence. Construction does
    not read files; unknown queries need no corpus access.
    """

    def __init__(self, chunks_path: str | Path = DEFAULT_CHUNKS):
        self.chunks_path = Path(chunks_path)
        self._document: EvidenceDocument | None = None

    def _load_document(self) -> EvidenceDocument:
        matches = []
        seen = set()
        for line in self.chunks_path.read_text(encoding="utf-8").splitlines():
            chunk = json.loads(line)
            chunk_id = chunk["chunk_id"]
            if chunk_id in seen:
                raise ValueError("Duplicate chunk ID")
            seen.add(chunk_id)
            if chunk_id == REPLACEMENT_CHUNK:
                matches.append(chunk)
        if len(matches) != 1:
            raise ValueError("Missing mock evidence")
        chunk = matches[0]
        if chunk["status"] != "active" or chunk["source_policy_version"] != "1.1":
            raise ValueError("Inapplicable mock evidence")
        for field in ("title", "content", "source_document", "source_policy_id", "effective_date"):
            if not isinstance(chunk[field], str) or not chunk[field].strip():
                raise ValueError("Invalid evidence field")
        return {
            "document_id": chunk["chunk_id"],
            "title": chunk["title"],
            "source": (
                f'{chunk["source_document"]} | {chunk["source_policy_id"]} '
                f'| v{chunk["source_policy_version"]} | effective {chunk["effective_date"]}'
            ),
            "score": 1.0,
            "excerpt": chunk["content"],
        }

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Return JSON-compatible evidence with no action or state changes.

        Invalid programmer inputs raise ValueError. Expected corpus loading
        failures return the technical error envelope from the module contract.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        normalised = " ".join(query.casefold().split())
        if normalised not in MOCK_QUERIES:
            return {"status": "empty", "data": {"docs": []}}
        try:
            if self._document is None:
                self._document = self._load_document()
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            return {"status": "error", "data": {"docs": []}}
        return {"status": "ok", "data": {"docs": [dict(self._document)][:top_k]}}


def create_retriever(backend: str = "mock", **kwargs: object) -> Retriever:
    """Startup factory. Real dependencies are imported only when requested."""
    if backend == "mock":
        return MockRetriever(**kwargs)
    if backend == "real":
        from .real_retriever import RealRetriever
        return RealRetriever(**kwargs)
    if backend == "hybrid":
        from .hybrid_retriever import HybridRetriever
        return HybridRetriever(**kwargs)
    raise ValueError("backend must be mock, real or hybrid")


def configure_retriever(backend: str = "mock", **kwargs: object) -> Retriever:
    """Set the convenience backend at startup, after successful initialization.

    Prefer create_retriever() + dependency injection for isolated applications.
    Do not reconfigure per request or concurrently with requests.
    """
    global _default_retriever
    instance = create_retriever(backend, **kwargs)
    _default_retriever = instance
    return instance


_default_retriever: Retriever = MockRetriever()


def retrieve(query: str, top_k: int = 5) -> RetrievalResult:
    """E-facing exception-safe entry point; configure backend once at startup."""
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError('query must be nonempty')
        if type(top_k) is not int or top_k <= 0:
            raise ValueError('top_k must be a positive integer')
        return validate_result(_default_retriever.retrieve(query, top_k), top_k)
    except Exception as exc:
        # Catch Exception only at the application boundary, not BaseException:
        # process interrupts and shutdown signals must not be swallowed.
        log_retrieval_failure(exc)
        return {'status': 'error', 'data': {'docs': []}}
