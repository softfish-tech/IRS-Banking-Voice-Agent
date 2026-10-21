"""Conservative, score-independent evidence check for the phase-one text path.

B's ranking score is not a calibrated answerability score.  The current E
renderer emits every retrieved excerpt, so every document must pass this gate.
This check is deliberately narrow: it rejects obvious topic/detail mismatches
but cannot prove arbitrary natural-language entailment.  See the C README.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from banking_agent.schemas.state import RetrievedDocument


_STOPWORDS = frozenset(
    "a an and are as at be been before by can could do does for from has have how "
    "i if in is it me my of on or our please should that the their these this those "
    "to us we what when where which who why will with would you your bank banking there get anything "
    "novabank policy tell explain help about need want know exact specific "
    "much many long".split()
)
_ALIASES = {
    "fees": "fee", "cost": "fee", "costs": "fee", "charges": "fee", "pay": "fee", "paying": "fee",
    "charge": "fee", "price": "fee", "prices": "fee",
    "replace": "replacement", "replacing": "replacement", "replaced": "replacement",
    "cards": "card", "wallets": "wallet", "crypto": "cryptocurrency",
    "cryptocurrencies": "cryptocurrency", "recovery": "recover", "recovering": "recover",
    "delivery": "deliver", "delivered": "deliver", "arrival": "deliver", "arrive": "deliver",
    "shipping": "deliver", "ship": "deliver", "days": "day", "hours": "hour",
    "minutes": "minute", "unauthorised": "unauthorized", "unrecognised": "unrecognized", "debit": "card",
    "loss": "lost", "damaged": "damage",
    "grams": "gram", "manufactures": "manufacture", "printed": "print",
}
_MONEY_VALUE = re.compile(
    r"(?:\b(?:sgd|usd)\s*\d+(?:\.\d+)?\b|(?:s\$|us\$|\$)\s*\d+(?:\.\d+)?\b|"
    r"\b\d+(?:\.\d+)?\s*(?:dollars?|cents?)\b|"
    r"\b(?:free|waived|complimentary)\b|\bno\s+(?:fee|charge)\b)",
    re.I,
)
_FEE_CONTEXT = re.compile(r"\b(?:fee|fees|cost|costs|charge|charges|price|replacement)\b", re.I)
_TIME_VALUE = re.compile(r"\b(?:\d+|one|two|three|five|seven|ten)\s*(?:days?|hours?|minutes?|weeks?)\b|\b(?:immediate|instantly|same-day)\b", re.I)
_CRYPTO_WALLET_RECOVERY = re.compile(
    r"(?=.*\b(?:crypto|cryptocurrency)\b)(?=.*\bwallet\b)"
    r"(?=.*\b(?:recover(?:y|ing)?|restor(?:e|ation)|los[et]\s+access)\b)",
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
    """Reject missing, malformed, irrelevant or incomplete retrieved excerpts."""

    def select_relevant(
        self, question: str, docs: list[RetrievedDocument]
    ) -> list[RetrievedDocument]:
        """Narrow B's candidates to excerpts that C may safely render.

        A B ranking is a candidate list rather than an answerability decision.
        The final :meth:`assess` call still makes the permission decision after
        E stores this subset.  If nothing is answerable but a document exposes
        a missing replacement reason, preserve it so C can issue its required
        clarification instead of turning an understood request into ABSTAIN.
        """
        answerable: list[RetrievedDocument] = []
        clarification_candidates: list[RetrievedDocument] = []
        for doc in docs:
            assessment = self.assess(question, [doc])
            if assessment.sufficient:
                answerable.append(doc)
            elif assessment.reason_code == "REPLACEMENT_REASON_REQUIRED":
                clarification_candidates.append(doc)
        # ``docs`` preserves B's descending rank.  Because ``assess`` already
        # requires each retained excerpt to answer the complete question, one
        # highest-ranked answerable source is sufficient and avoids rendering
        # adjacent policy branches with different conditions or prices.
        if answerable:
            return answerable[:1]
        return clarification_candidates[:1]

    def assess(self, question: str, docs: list[RetrievedDocument]) -> EvidenceAssessment:
        if not docs:
            return EvidenceAssessment(False, "NO_EVIDENCE")
        query_terms = _terms(question)
        if not query_terms:
            return EvidenceAssessment(False, "QUESTION_SCOPE_UNCLEAR")

        seen: set[str] = set()
        crypto_wallet_recovery = bool(_CRYPTO_WALLET_RECOVERY.search(question))
        for doc in docs:
            if (
                not doc.document_id.strip() or doc.document_id in seen
                or not doc.title.strip() or not doc.source.strip()
                or not doc.excerpt.strip() or not math.isfinite(doc.score)
            ):
                return EvidenceAssessment(False, "INVALID_EVIDENCE")
            seen.add(doc.document_id)

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
                continue

            # The E renderer currently displays all docs. A single unrelated
            # excerpt therefore prevents the whole answer from being rendered.
            evidence_terms = _terms(f"{doc.title} {doc.excerpt}")
            overlap = query_terms & evidence_terms
            # "Replacement is SGD 15" states a price without the word fee.
            # Accept that single missing term only when the priced clause
            # names the subject; the amount still needs the later value gate.
            if query_terms - overlap == {"fee"} and _has_relevant_money_value(query_terms, doc.excerpt):
                overlap = overlap | {"fee"}
            # A broad topic overlap can still answer the wrong attribute:
            # card-fee evidence says nothing about the card's colour. Require
            # every salient request term to be represented in each rendered
            # excerpt. This favours abstention when wording differs.
            if overlap != query_terms:
                return EvidenceAssessment(False, "EVIDENCE_SCOPE_MISMATCH")

            # The maintained B corpus gives reason-specific replacement fees.
            # A generic card-replacement question must not inherit the loss,
            # damage or compromise price from one retrieved branch.
            if {"card", "replacement", "fee"} <= query_terms and not (
                {"lost", "stolen", "damage", "compromised", "compromise"} & query_terms
            ):
                branch_terms = _terms(f"{doc.document_id} {doc.title} {doc.excerpt}")
                if {
                    "lost", "stolen", "damage", "compromised", "compromise",
                    "retained", "swallowed",
                } & branch_terms:
                    return EvidenceAssessment(False, "REPLACEMENT_REASON_REQUIRED")

            query_lower = question.casefold()
            if ("how much" in query_lower or "fee" in query_terms) and not _has_relevant_money_value(query_terms, doc.excerpt):
                return EvidenceAssessment(False, "MISSING_REQUESTED_VALUE")
            if ("how long" in query_lower or "when " in query_lower) and not _TIME_VALUE.search(doc.excerpt):
                return EvidenceAssessment(False, "MISSING_REQUESTED_TIME")

        return EvidenceAssessment(True, "EVIDENCE_SCOPE_MATCHED")
