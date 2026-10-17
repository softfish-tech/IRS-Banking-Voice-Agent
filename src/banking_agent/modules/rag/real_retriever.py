"""Callable B-module backend: optimized BM25 candidates, then fixed CE ranking."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from .bm25_retriever import BM25Retriever
from .cross_encoder_reranker import CrossEncoderReranker
from .retriever import DEFAULT_CHUNKS, EvidenceDocument, RetrievalResult, validate_result, log_retrieval_failure

DEFAULT_FAQ = DEFAULT_CHUNKS.parent / 'NovaBank_faq_chunk_mapping_v1_1.jsonl'
DEFAULT_MODEL = 'cross-encoder/ms-marco-MiniLM-L6-v2'
DEFAULT_REVISION = '233902d25c440f23af6f7d6e94d2946bac0bee0a'


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]: ...


class RealRetriever:
    """Build once at application startup, then reuse for all requests.

    Initialization errors propagate to the caller: never silently switch to a
    mock or construct a model per request. Runtime scoring failures return error.
    This backend ranks evidence; it has no calibrated evidence rejection gate.
    Its ok status is not permission to answer, and C must check sufficiency.
    """

    def __init__(self, jsonl_path: str = str(DEFAULT_CHUNKS), *,
                 faq_path: str = str(DEFAULT_FAQ), candidate_k: int = 20,
                 model_name: str = DEFAULT_MODEL, revision: str | None = DEFAULT_REVISION,
                 local_files_only: bool = True, reranker: Reranker | None = None) -> None:
        if type(candidate_k) is not int or candidate_k < 1:
            raise ValueError('candidate_k must be a positive integer')
        self.candidate_k = candidate_k
        self._backend = BM25Retriever(jsonl_path, normalize=True, title_weight=1.0,
                                      faq_path=faq_path, faq_weight=0.5)
        self._reranker = reranker if reranker is not None else CrossEncoderReranker(
            model_name, revision=revision, local_files_only=local_files_only)
        self.metadata = {
            'backend': 'optimized_bm25_cross_encoder', 'candidate_k': candidate_k,
            'model': model_name, 'revision': revision, 'rejection_threshold': None,
            'reranker_class': type(self._reranker).__name__,
            'corpus_sha256': hashlib.sha256(Path(jsonl_path).read_bytes()).hexdigest(),
            'faq_sha256': hashlib.sha256(Path(faq_path).read_bytes()).hexdigest(),
        }

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        try:
            if not isinstance(query, str) or not query.strip():
                raise ValueError('query must be a nonempty string')
            if type(top_k) is not int or top_k < 1:
                raise ValueError('top_k must be a positive integer')
            result = self._backend.retrieve(query, max(self.candidate_k, top_k))
            if result['status'] != 'ok':
                return validate_result(result, top_k)
            candidates = result['data']['docs']
            docs: list[EvidenceDocument] = self._reranker.rerank(query, candidates, top_k)
            originals = {d['document_id']: d for d in candidates}
            for doc in docs:
                original = originals[doc['document_id']]
                if any(doc[k] != original[k] for k in ('title', 'source', 'excerpt')):
                    raise ValueError('Reranker modified evidence')
            return validate_result({'status': 'ok' if docs else 'empty', 'data': {'docs': docs}}, top_k)
        except Exception as exc:
            log_retrieval_failure(exc)
            return {'status': 'error', 'data': {'docs': []}}
