"""E-owned presentation narrowing for a reviewed, condition-specific answer.

C still decides whether the bounded B evidence set permits an answer. This
module does not admit evidence or choose a policy branch. It only prevents a
customer-facing renderer from leading with an unrelated paragraph that shares
the same broad retrieved chunk as the answerable fact.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from banking_agent.schemas.state import RetrievedDocument


_DAMAGE = re.compile(r"\b(?:damage|damaged|chip)\b", re.I)
_REPLACEMENT = re.compile(r"\b(?:replace|replacement|replacing)\b", re.I)
_FEE_QUESTION = re.compile(r"\b(?:fee|cost|charge|price|pay)\b|how much", re.I)
_MONEY = re.compile(r"\b(?:sgd|usd)\s*\d+\b|\b(?:free|waived)\b", re.I)
_SENTENCES = re.compile(r"(?<=[.!?])\s+")


def is_damaged_replacement_question(question: str) -> bool:
    """Recognise the reviewed non-security damaged-card policy branch."""

    return bool(_DAMAGE.search(question) and _REPLACEMENT.search(question))


def presentation_documents(
    question: str, documents: Sequence[RetrievedDocument]
) -> list[RetrievedDocument]:
    """Return C-approved documents suitable for customer-facing rendering.

    The narrowed branch applies only after the customer explicitly supplies
    both a damage condition and a replacement subject. B preserves rank order,
    so the first matching condition-specific candidate remains the source.
    All other questions use the complete C-admissible set unchanged.
    """

    if not is_damaged_replacement_question(question):
        return list(documents)
    matches = [
        document
        for document in documents
        if _DAMAGE.search(f"{document.title} {document.excerpt}")
        and _REPLACEMENT.search(f"{document.title} {document.excerpt}")
    ]
    return matches[:1] or list(documents)


def presentation_excerpt(question: str, document: RetrievedDocument) -> str:
    """Remove unrelated freeze prose from a damaged-replacement source chunk."""

    if not is_damaged_replacement_question(question):
        return document.excerpt
    relevant = [
        sentence
        for sentence in _SENTENCES.split(document.excerpt.strip())
        if _DAMAGE.search(sentence) or _REPLACEMENT.search(sentence)
    ]
    if _FEE_QUESTION.search(question):
        priced = [sentence for sentence in relevant if _MONEY.search(sentence)]
        if priced:
            relevant = priced
    return " ".join(relevant).strip() or document.excerpt
