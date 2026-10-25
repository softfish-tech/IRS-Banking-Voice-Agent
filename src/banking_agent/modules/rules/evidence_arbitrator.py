"""C-owned evidence admissibility checks for the phase-one text path.

B ranks a bounded candidate set and the grounded response model reads that
set as context.  C validates document structure and answer permission; it
does not replace B's ranking with a single-document relevance decision.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from banking_agent.schemas.state import RetrievedDocument


_STOPWORDS = frozenset(
    "a an and are as at be been before but by can could do does for from has have how "
    "i if in is it me my of on or our please should that the their these this those "
    "to us we what when where which who why will with would you your bank banking there get anything "
    "novabank policy tell explain help about need want know exact specific "
    "much many long still old working lol".split()
)
_ALIASES = {
    "fees": "fee", "cost": "fee", "costs": "fee", "charges": "fee", "pay": "fee", "paying": "fee",
    "charge": "fee", "price": "fee", "prices": "fee",
    "replace": "replacement", "replacing": "replacement", "replaced": "replacement",
    "swap": "replacement", "swapping": "replacement", "swapped": "replacement",
    "replcement": "replacement", "replacment": "replacement",
    "cards": "card", "wallets": "wallet", "currencies": "currency",
    "transactions": "transaction", "crypto": "cryptocurrency",
    "cryptocurrencies": "cryptocurrency", "recovery": "recover", "recovering": "recover",
    "delivery": "deliver", "delivered": "deliver", "arrival": "deliver", "arrive": "deliver",
    "shipping": "deliver", "ship": "deliver", "days": "day", "hours": "hour",
    "minutes": "minute", "unauthorised": "unauthorized", "unrecognised": "unrecognized", "debit": "card",
    "loss": "lost", "damaged": "damage", "chip": "damage",
    "grams": "gram", "manufactures": "manufacture", "printed": "print",
}
_MONEY_VALUE = re.compile(
    r"(?:\b(?:sgd|usd)\s*\d+(?:\.\d+)?\b|(?:s\$|us\$|\$)\s*\d+(?:\.\d+)?\b|"
    r"\b\d+(?:\.\d+)?\s*(?:dollars?|cents?)\b|"
    r"\b(?:free|waived|complimentary)\b|\bno\s+(?:fee|charge)\b)",
    re.I,
)
_FEE_CONTEXT = re.compile(r"\b(?:fee|fees|cost|costs|charge|charges|price|replacement)\b", re.I)
_TIME_VALUE = re.compile(r"\b(?:\d+|one|two|three|five|seven|ten)\s*(?:days?|hours?|minutes?|weeks?)\b|\bday\s*\d+\b|\b(?:immediate|instantly|same-day)\b", re.I)
_CRYPTO_WALLET_RECOVERY = re.compile(
    r"(?=.*\b(?:crypto|cryptocurrency)\b)(?=.*\bwallets?\b)"
    r"(?=.*\b(?:recover(?:y|ing)?|restor(?:e|ation)|los(?:e|t|ing)\s+access)\b)",
    re.I,
)
_CRYPTO_UNSUPPORTED = re.compile(r"\bcryptocurrency\b.{0,80}\bunsupported\b", re.I)
_CRYPTO_BOUNDARY_DOCUMENT_ID = "NB-v1_1-fiat_currency_support-001"


def _terms(text: str) -> frozenset[str]:
    words = re.findall(r"[a-z0-9]+", text.casefold())
    return frozenset(_ALIASES.get(word, word) for word in words if len(word) > 1 and word not in _STOPWORDS)


def _has_relevant_money_value(query_terms: frozenset[str], excerpt: str) -> bool:
    """Keep a delivery time or a separate shipping charge from answering a fee."""

    subject_terms = query_terms - {"fee"}
    # A card or loss mention alongside a shipping price cannot establish a
    # replacement fee; the priced clause must name the replacement itself.
    required_subject = {"replacement"} if "replacement" in subject_terms else subject_terms
    # Prices joined by punctuation or a contrast/conjunction can describe a
    # different service. Keep the subject and amount in the same short clause.
    for clause in re.split(
        r"[;,\n–—]|\s+-\s+|(?<=[.!?])\s+|\b(?:and|but|while|whereas)\b",
        excerpt,
        flags=re.I,
    ):
        if (
            _MONEY_VALUE.search(clause)
            and _FEE_CONTEXT.search(clause)
            and (not required_subject or required_subject & _terms(clause))
        ):
            return True
    return False


@dataclass(frozen=True)
class EvidenceAssessment:
    sufficient: bool
    reason_code: str


class EvidenceArbitrator:
    """Check answer permission without collapsing a bounded evidence set."""

    def select_relevant(
        self, question: str, docs: list[RetrievedDocument]
    ) -> list[RetrievedDocument]:
        """Remove only malformed or duplicate documents from B's Top-K.

        Relevance ranking belongs to B and contextual synthesis belongs to the
        grounded response model.  C therefore keeps every structurally valid
        candidate in B order, except for an explicit unsupported-service
        boundary whose only admissible source is fixed by C. :meth:`assess`
        separately checks whether at least one member of this set supports an
        answer or exposes a required business clarification.
        """
        admissible: list[RetrievedDocument] = []
        seen: set[str] = set()
        for doc in docs:
            if (
                not doc.document_id.strip() or doc.document_id in seen
                or not doc.title.strip() or not doc.source.strip()
                or not doc.excerpt.strip() or not math.isfinite(doc.score)
            ):
                continue
            seen.add(doc.document_id)
            admissible.append(doc)
        # The crypto-wallet service boundary is an explicit C policy
        # exception, not semantic re-ranking. No other retrieved document can
        # establish this unsupported-service conclusion, so keeping it would
        # only let a renderer add unrelated policy detail.
        if _CRYPTO_WALLET_RECOVERY.search(question):
            return [
                doc for doc in admissible
                if doc.document_id == _CRYPTO_BOUNDARY_DOCUMENT_ID
                and _CRYPTO_UNSUPPORTED.search(doc.excerpt)
            ]
        return admissible

    def assess(self, question: str, docs: list[RetrievedDocument]) -> EvidenceAssessment:
        if not docs:
            return EvidenceAssessment(False, "NO_EVIDENCE")
        query_terms = _terms(question)
        if not query_terms:
            return EvidenceAssessment(False, "QUESTION_SCOPE_UNCLEAR")

        crypto_wallet_recovery = bool(_CRYPTO_WALLET_RECOVERY.search(question))

        # The maintained corpus gives reason-specific replacement service
        # terms. This is a business completeness requirement, not a relevance
        # decision: do not let the response model apply a fee or delivery
        # branch before the customer states which replacement circumstance
        # applies.
        generic_replacement_enquiry = (
            {"card", "replacement"} <= query_terms
            and ("fee" in query_terms or "how much" in question.casefold())
            and not {"lost", "stolen", "damage", "compromised", "compromise"} & query_terms
        )
        generic_replacement_enquiry = generic_replacement_enquiry or (
            {"card", "replacement"} <= query_terms
            and (
                "how long" in question.casefold()
                or "when " in question.casefold()
                or "today" in query_terms
                or bool({"arrive", "deliver", "receive"} & query_terms)
            )
            and not {"lost", "stolen", "damage", "compromised", "compromise"} & query_terms
        )
        if generic_replacement_enquiry and any(
            {"lost", "stolen", "damage", "compromised", "compromise", "retained", "swallowed"}
            & _terms(f"{doc.document_id} {doc.title} {doc.excerpt}")
            for doc in docs
        ):
            return EvidenceAssessment(False, "REPLACEMENT_REASON_REQUIRED")

        has_supporting_document = False
        missing_requested_value = False
        missing_requested_time = False
        for doc in docs:
            if (
                not doc.document_id.strip()
                or not doc.title.strip() or not doc.source.strip()
                or not doc.excerpt.strip() or not math.isfinite(doc.score)
            ):
                return EvidenceAssessment(False, "INVALID_EVIDENCE")

            # This is a deliberately narrow unsupported-service exception.
            # The policy does not describe a wallet-recovery procedure; it
            # establishes that cryptocurrency itself is unsupported. That is
            # sufficient only to answer that NovaBank cannot provide the
            # requested crypto-wallet recovery service, and only from the
            # reviewed boundary document.
            if (
                crypto_wallet_recovery
                and doc.document_id == _CRYPTO_BOUNDARY_DOCUMENT_ID
                and _CRYPTO_UNSUPPORTED.search(doc.excerpt)
            ):
                has_supporting_document = True
                continue

            evidence_terms = _terms(f"{doc.title} {doc.excerpt}")
            overlap = query_terms & evidence_terms
            # "Replacement is SGD 15" states a price without the word fee.
            # Accept that single missing term only when the priced clause
            # names the subject; the amount still needs the later value gate.
            if query_terms - overlap == {"fee"} and _has_relevant_money_value(query_terms, doc.excerpt):
                overlap = overlap | {"fee"}
            # One document must support the complete requested fact. Other
            # valid B candidates remain available as context and cannot veto
            # this evidence set merely by being less relevant.
            if overlap != query_terms:
                continue

            query_lower = question.casefold()
            if ("how much" in query_lower or "fee" in query_terms) and not _has_relevant_money_value(query_terms, doc.excerpt):
                missing_requested_value = True
                continue
            if ("how long" in query_lower or "when " in query_lower) and not _TIME_VALUE.search(doc.excerpt):
                missing_requested_time = True
                continue
            has_supporting_document = True

        if has_supporting_document:
            return EvidenceAssessment(True, "EVIDENCE_SCOPE_MATCHED")
        if missing_requested_value:
            return EvidenceAssessment(False, "MISSING_REQUESTED_VALUE")
        if missing_requested_time:
            return EvidenceAssessment(False, "MISSING_REQUESTED_TIME")
        return EvidenceAssessment(False, "EVIDENCE_SCOPE_MISMATCH")
