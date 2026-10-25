"""Strict local English BM25 retrieval; no network calls at query time.

Install dependencies with ``python -m pip install -e .``.
Use the public package factory for integration; this class is a ranking component.
Every row needs chunk_id, title, source_type and content (or excerpt).
Answerable rows additionally need source_policy_id and source_policy_version.
The knowledge-chunk builder copies source_type from each owning policy's
verified metadata; unknown sources never receive implicit policy authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi


class ChunkValidationError(ValueError):
    """Malformed JSONL or invalid chunk, including file and line location."""


@dataclass(frozen=True)
class _Document:
    document_id: str
    title: str
    source: str
    excerpt: str
    tokens: frozenset[str]


class BM25Retriever:
    """Load once, allowlist evidence sources, and rank cached English text.

    Scores are raw BM25 scores, not probabilities or proof of semantic support.
    Zero/negative scores may occur in small corpora; matching documents remain
    eligible. Only documents with a lexical overlap are returned. Final answer
    permission remains with C, and response assembly remains with E.
    """

    ANSWERABLE_SOURCE_TYPES = frozenset({"Category Master Policy", "FAQ"})

    def __init__(self, jsonl_path: str, *, normalize: bool = False,
                 title_weight: float = 0.0, faq_path: str | None = None,
                 faq_weight: float = 0.0, coverage_weight: float = 0.0) -> None:
        """Validate all rows and build the in-memory index exactly once.

        Raises OSError for file access failures and ChunkValidationError for
        invalid UTF-8, malformed JSON, missing fields or duplicate identifiers.
        An empty/fully filtered file is valid and yields empty retrieval results.
        """
        if not isinstance(jsonl_path, str) or not jsonl_path.strip():
            raise ValueError("jsonl_path must be a non-empty string")
        for value in (title_weight, faq_weight, coverage_weight):
            if not math.isfinite(value) or value < 0:
                raise ValueError("Ranking weights must be finite and nonnegative")
        if faq_weight and not faq_path:
            raise ValueError("faq_weight requires faq_path")
        self.normalize = normalize
        self.title_weight = title_weight
        self.faq_weight = faq_weight
        self.coverage_weight = coverage_weight
        path = Path(jsonl_path)
        documents: list[_Document] = []
        corpus: list[list[str]] = []
        titles: list[list[str]] = []
        bodies: list[list[str]] = []
        seen: set[str] = set()
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    # Blank lines are harmless; nonblank rows must be JSON objects.
                    if not line.strip():
                        continue
                    location = f"{path}:{line_number}"
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ChunkValidationError(f"{location}: invalid JSON: {exc.msg}") from exc
                    if not isinstance(row, dict):
                        raise ChunkValidationError(f"{location}: expected a JSON object")
                    chunk_id = self._required_string(row, "chunk_id", location).strip()
                    title = self._required_string(row, "title", location).strip()
                    source_type = self._required_string(row, "source_type", location)
                    if chunk_id in seen:
                        raise ChunkValidationError(f"{location}: duplicate chunk_id {chunk_id!r}")
                    # Check IDs even in excluded rows to prevent silent corruption.
                    seen.add(chunk_id)
                    supplied = [key for key in ("content", "excerpt") if key in row]
                    if not supplied:
                        raise ChunkValidationError(f"{location}: missing content or excerpt")
                    for key in supplied:
                        self._required_string(row, key, location)
                    if len(supplied) == 2 and row["content"] != row["excerpt"]:
                        raise ChunkValidationError(f"{location}: content and excerpt disagree")
                    content = row[supplied[0]]
                    # Exact allowlist: unknown sources, analyses and registries
                    # are excluded; titles or filenames never grant authority.
                    if source_type not in self.ANSWERABLE_SOURCE_TYPES:
                        continue
                    policy_id = self._required_string(row, "source_policy_id", location).strip()
                    version = self._required_string(row, "source_policy_version", location).strip()
                    tokens = self._tokenize(title + " " + content)
                    if not tokens:
                        raise ChunkValidationError(f"{location}: no indexable English text")
                    documents.append(_Document(chunk_id, title,
                                               f"{policy_id} | v{version} | {source_type}",
                                               content, frozenset(tokens)))
                    corpus.append(tokens)
                    titles.append(self._tokenize(title))
                    bodies.append(self._tokenize(content))
        except UnicodeDecodeError as exc:
            raise ChunkValidationError(f"{path}: invalid UTF-8") from exc
        self._documents = tuple(documents)
        self._index = BM25Okapi(bodies if title_weight else corpus) if corpus else None
        self._title_index = BM25Okapi(titles) if corpus and title_weight else None
        self._faq_index = None
        self._faq_targets: list[list[int]] = []
        if faq_path and faq_weight and documents:
            positions = {d.document_id: i for i, d in enumerate(documents)}
            faq_tokens = []
            # Candidate mappings are lexical hints, never authoritative evidence.
            # Spread their influence across mapped chunks; never change excerpts.
            for line in Path(faq_path).read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                targets = [positions[c["chunk_id"]] for c in row["candidate_chunks"]
                           if c["chunk_id"] in positions]
                if not targets:
                    continue
                expressions = row["expressions"]
                if not isinstance(expressions, list) or not all(isinstance(q, str) for q in expressions):
                    raise ChunkValidationError("Invalid FAQ expressions")
                tokens = self._tokenize(" ".join(dict.fromkeys(expressions)))
                if tokens:
                    faq_tokens.append(tokens)
                    self._faq_targets.append(targets)
            if faq_tokens:
                self._faq_index = BM25Okapi(faq_tokens)

    def evidence_documents(self) -> list[dict[str, Any]]:
        """Return detached evidence records for same-corpus retrieval backends."""
        return [{"document_id": d.document_id, "title": d.title, "source": d.source,
                 "score": 0.0, "excerpt": d.excerpt} for d in self._documents]

    @staticmethod
    def _required_string(row: dict[str, Any], field: str, location: str) -> str:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ChunkValidationError(f"{location}: {field} must be a non-empty string")
        return value

    def _tokenize(self, text: str) -> list[str]:
        # Preserve numbers/decimals for banking limits. Apply identical processing
        # to queries and documents; original excerpts are never modified.
        tokens = re.findall(r"[a-z]+|\d+(?:\.\d+)?", text.lower())
        if not self.normalize:
            return tokens
        # Small conservative inflection map; retain negation, numbers and units.
        stopwords = {"a", "an", "the", "is", "are", "am", "was", "were", "be",
                     "i", "my", "me", "you", "your", "it", "its", "to", "of",
                     "for", "and", "or", "in", "on", "at", "do", "does", "please"}
        forms = {"fees": "fee", "cards": "card", "transfers": "transfer",
                 "payments": "payment", "refunds": "refund", "limits": "limit",
                 "accounts": "account", "charges": "charge", "charged": "charge",
                 "replacing": "replace", "replacement": "replace",
                 "withdrawals": "withdrawal", "deposits": "deposit"}
        return [forms.get(t, t) for t in tokens if t not in stopwords]

    def retrieve(self, query: str, top_k: int = 5) -> dict:
        """Return descending BM25 matches using only the cached index.

        Invalid inputs raise ValueError. Known scoring failures return error;
        no corpus or no overlapping vocabulary returns empty. Technical errors
        are not represented as successful or normal-empty business results.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        tokens = self._tokenize(query)
        if not tokens:
            if not re.search(r"[a-z0-9]", query.lower()):
                raise ValueError("query must contain English words or numbers")
            return {"status": "empty", "data": {"docs": []}}
        if self._index is None:
            return {"status": "empty", "data": {"docs": []}}
        try:
            scores = self._index.get_scores(tokens)
            if self._title_index is not None:
                scores = scores + self.title_weight * self._title_index.get_scores(tokens)
            if self._faq_index is not None:
                # Max pooling avoids rewarding chunks solely for many FAQ links.
                bonus = [0.0] * len(self._documents)
                for value, targets in zip(self._faq_index.get_scores(tokens), self._faq_targets):
                    for rank, index in enumerate(targets, 1):
                        bonus[index] = max(bonus[index], float(value) / rank)
                scores = scores + self.faq_weight * np.array(bonus)
            if len(scores) != len(self._documents) or not all(math.isfinite(float(s)) for s in scores):
                raise ArithmeticError("invalid BM25 score array")
        except (ArithmeticError, ValueError, RuntimeError):
            return {"status": "error", "data": {"docs": []}}
        query_tokens = set(tokens)
        matched = [i for i, doc in enumerate(self._documents) if doc.tokens & query_tokens]
        # Stable identifier tie-break makes repeated retrieval deterministic.
        matched.sort(key=lambda i: (-float(scores[i]), self._documents[i].document_id))
        if self.coverage_weight and len(matched) > top_k:
            # Retrieve a larger pool, then greedily cover previously unseen query
            # terms. Uses only the query and corpus, never evaluation gold labels.
            pool = matched[:max(20, top_k * 4)]
            selected: list[int] = []
            covered: set[str] = set()
            scale = max(abs(float(scores[i])) for i in pool) or 1.0
            while pool and len(selected) < top_k:
                best = max(pool, key=lambda i: (
                    float(scores[i]) / scale + self.coverage_weight *
                    len((self._documents[i].tokens & query_tokens) - covered) / len(query_tokens),
                    -matched.index(i)))
                selected.append(best)
                covered.update(self._documents[best].tokens & query_tokens)
                pool.remove(best)
            # Preserve the score-descending public contract within the selected set.
            matched = sorted(selected, key=lambda i: (-float(scores[i]), self._documents[i].document_id))
        docs = [{"document_id": self._documents[i].document_id,
                 "title": self._documents[i].title,
                 "source": self._documents[i].source,
                 "score": float(scores[i]),
                 "excerpt": self._documents[i].excerpt}
                for i in matched[:top_k]]
        return {"status": "ok" if docs else "empty", "data": {"docs": docs}}
