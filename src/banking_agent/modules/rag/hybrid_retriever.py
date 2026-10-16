"""Local experimental BM25/dense/RRF retrieval with an in-memory cosine index.

Install the optional dependency with ``pip install -e '.[rag-dense]'``.
Construct a new instance after corpus/model changes to rebuild both indexes.
Initialization failures are explicit exceptions; retrieve() converts expected
request/scoring failures into the public error envelope. Direct list methods
raise exceptions so that an error cannot silently become an empty candidate list.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from .bm25_retriever import BM25Retriever
from .retriever import EvidenceDocument, RetrievalResult, validate_result, log_retrieval_failure


class Encoder(Protocol):
    """SentenceTransformer-compatible seam for deterministic offline tests."""

    def encode(self, sentences: list[str], **kwargs: Any) -> Any: ...


class HybridRetriever:
    """Index allowed evidence once, and fuse independent rankings by chunk ID.

    No rejection threshold is inferred from cosine or RRF scores: an unrelated
    query may still return candidates. Answer permission remains with module C.
    """

    def __init__(
        self, jsonl_path: str,
        model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', *,
        revision: str | None = None, device: str = 'cpu',
        local_files_only: bool = False, batch_size: int = 32,
        candidate_k: int = 20, rrf_k: int = 60,
        query_prefix: str = '', document_prefix: str = '',
        encoder: Encoder | None = None,
    ) -> None:
        for name, value in (('batch_size', batch_size), ('candidate_k', candidate_k), ('rrf_k', rrf_k)):
            if type(value) is not int or value <= 0:
                raise ValueError(f'{name} must be a positive integer')
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError('model_name must be nonempty')
        if not isinstance(query_prefix, str) or not isinstance(document_prefix, str):
            raise ValueError('Embedding prefixes must be strings')
        self.candidate_k, self.rrf_k = candidate_k, rrf_k
        self.batch_size, self.query_prefix = batch_size, query_prefix
        # Reuse exactly the baseline loading, duplicate-ID and source allowlist
        # validation. No second parser with potentially divergent filtering.
        self._bm25 = BM25Retriever(jsonl_path)
        self._documents = self._bm25.evidence_documents()
        if encoder is None:
            from sentence_transformers import SentenceTransformer
            encoder = SentenceTransformer(model_name, revision=revision, device=device,
                                          local_files_only=local_files_only,
                                          trust_remote_code=False)
        self._encoder = encoder
        texts = [document_prefix + d['title'] + '\n' + d['excerpt'] for d in self._documents]
        self._matrix = self._encode(texts) if texts else np.empty((0, 0), dtype=np.float32)
        self._matrix.setflags(write=False)
        # Exposed separately from result docs to preserve the shared schema.
        # Pin revision to a model commit for reproducible real-model experiments.
        self.index_metadata = {
            'corpus_sha256': hashlib.sha256(Path(jsonl_path).read_bytes()).hexdigest(),
            'model_name': model_name, 'requested_revision': revision,
            'encoder_class': type(encoder).__name__, 'device': device,
            'dimension': self._matrix.shape[1], 'documents': len(self._documents),
            'candidate_k': candidate_k, 'rrf_k': rrf_k, 'batch_size': batch_size,
            'query_prefix': query_prefix, 'document_prefix': document_prefix,
            'document_text': 'title + newline + full excerpt',
            'max_seq_length': getattr(encoder, 'max_seq_length', None),
            'rebuild': 'Construct a new instance when corpus or model configuration changes',
        }

    def _encode(self, texts: list[str]) -> np.ndarray:
        """Normalize each vector; a dot product then equals cosine similarity."""
        matrix = np.asarray(self._encoder.encode(
            texts, batch_size=self.batch_size, convert_to_numpy=True,
            normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(texts) or matrix.shape[1] == 0:
            raise ValueError('Encoder returned an invalid embedding shape')
        if not np.isfinite(matrix).all():
            raise ValueError('Encoder returned nonfinite embeddings')
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if not np.isfinite(norms).all() or (norms <= 0).any():
            raise ValueError('Encoder returned zero or invalid vector norms')
        return matrix / norms

    @staticmethod
    def _validate(query: str, top_k: int) -> None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError('query must be a nonempty string')
        if type(top_k) is not int or top_k <= 0:
            raise ValueError('top_k must be a positive integer')

    def retrieve_dense(self, query: str, top_k: int = 5) -> list[EvidenceDocument]:
        self._validate(query, top_k)
        if not self._documents:
            return []
        vector = self._encode([self.query_prefix + query])[0]
        if vector.shape[0] != self._matrix.shape[1]:
            raise ValueError('Query/document embedding dimensions differ')
        scores = np.clip(self._matrix @ vector, -1.0, 1.0)
        ranked = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), self._documents[i]['document_id']))
        return [dict(self._documents[i], score=float(scores[i])) for i in ranked[:top_k]]

    def retrieve_bm25(self, query: str, top_k: int = 5) -> list[EvidenceDocument]:
        self._validate(query, top_k)
        result = self._bm25.retrieve(query, top_k)
        if result['status'] == 'error':
            raise RuntimeError('BM25 scoring failed')
        return result['data']['docs']

    def retrieve_hybrid(self, query: str, top_k: int = 5) -> list[EvidenceDocument]:
        self._validate(query, top_k)
        depth = max(top_k, self.candidate_k)
        rankings = (self.retrieve_bm25(query, depth), self.retrieve_dense(query, depth))
        documents: dict[str, EvidenceDocument] = {}
        scores: dict[str, float] = {}
        for ranking in rankings:
            seen: set[str] = set()
            for rank, doc in enumerate(ranking, start=1):
                identifier = doc['document_id']
                if identifier in seen:
                    continue
                seen.add(identifier)
                documents[identifier] = doc
                # Equal-weight RRF: sum 1 / (k + rank) over lists containing
                # this ID. Raw BM25 and cosine scores are never added together.
                scores[identifier] = scores.get(identifier, 0.0) + 1.0 / (self.rrf_k + rank)
        identifiers = sorted(scores, key=lambda cid: (-scores[cid], cid))[:top_k]
        return [dict(documents[cid], score=float(scores[cid])) for cid in identifiers]

    def retrieve(self, query: str, top_k: int = 5, mode: str = 'hybrid') -> RetrievalResult:
        """Return error for invalid requests/known scoring failures, empty for no candidates.

        This wrapper intentionally packages invalid input as requested; the
        original standalone BM25Retriever continues to raise ValueError.
        """
        try:
            self._validate(query, top_k)
            if not isinstance(mode, str) or mode not in ('bm25', 'dense', 'hybrid'):
                raise ValueError('mode must be bm25, dense, or hybrid')
            method = {'bm25': self.retrieve_bm25, 'dense': self.retrieve_dense,
                      'hybrid': self.retrieve_hybrid}[mode]
            docs = method(query, top_k)
            return validate_result({'status': 'ok' if docs else 'empty', 'data': {'docs': docs}}, top_k)
        except Exception as exc:
            log_retrieval_failure(exc)
            return {'status': 'error', 'data': {'docs': []}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jsonl_path', nargs='?', default=str(
        Path(__file__).parent / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'))
    parser.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    parser.add_argument('--revision')
    parser.add_argument('--local-files-only', action='store_true')
    parser.add_argument('--query', default='How much does replacing a lost card cost?')
    args = parser.parse_args()
    backend = HybridRetriever(args.jsonl_path, model_name=args.model,
                              revision=args.revision, local_files_only=args.local_files_only)
    print(json.dumps(backend.index_metadata, indent=2))
    for mode in ('bm25', 'dense', 'hybrid'):
        print(json.dumps({'mode': mode, 'result': backend.retrieve(args.query, mode=mode)}, indent=2))
    print(json.dumps(backend.retrieve('')))  # invalid input -> error envelope
