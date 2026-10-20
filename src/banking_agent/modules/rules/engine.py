"""Module C business decisions using the canonical AgentState contract.

The orchestrator owns sequencing and response wording. This module owns only
the business action, reason code and permitted business-state patch.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict

from banking_agent.schemas.enums import (
    Action,
    ComplaintStatus,
    ConsentStatus,
    HandoffStatus,
    RiskLevel,
)
from banking_agent.schemas.state import AgentState, Decision, RuleStatePatch

from .complaint_arbitrator import ComplaintArbitrator
from .evidence_arbitrator import EvidenceArbitrator


RagStatus = Literal["ok", "empty", "error"]


class RulesResult(BaseModel):
    """The existing module envelope with a canonical Decision payload."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    data: Decision


class RuleEngine:
    """Fail-closed phase-one rules for the text mock workflow.

    ``rag_status=None`` means that B has not yet been called. After B returns,
    E must call again with B's actual status and the retrieved docs merged into
    ``AgentState``. This explicit signal distinguishes no evidence from no
    retrieval attempt; it does not add a field to the shared schema.
    """

    _UNKNOWN_INTENTS = frozenset({"", "unknown"})
    _ACCOUNT_READ_INTENTS = frozenset(
        {"check_balance", "balance_enquiry", "account_balance", "transaction_history", "check_transactions"}
    )
    _TRANSACTION_INTENTS = frozenset(
        {"make_transfer", "transfer_money", "execute_transfer", "make_payment", "execute_payment"}
    )
    _RECOMMENDATION_REQUEST = re.compile(
        r"^\s*(?:(?:can|could|would)\s+you\s+|please\s+)?(?:recommend|suggest)\b"
        r"|\bi\s+(?:would\s+like|want|need)\s+(?:you\s+to\s+)?(?:recommend|suggest)\b",
        re.I,
    )
    _ACCOUNT_READ_REQUEST = re.compile(
        r"\b(?:what(?:'s| is)|check|show(?: me)?|tell me)\s+my\s+"
        r"(?:(?:account|current)\s+)?(?:balance|transactions?|transaction history)\b",
        re.I,
    )
    _TRANSACTION_REQUEST = re.compile(
        r"^\s*(?:(?:can|could|would)\s+you\s+|please\s+)?"
        r"(?:make|send|execute|initiate)\s+(?:a\s+)?(?:bank\s+)?(?:transfer|payment)\b"
        r"|^\s*(?:(?:can|could|would)\s+you\s+|please\s+)?transfer\s+money\b",
        re.I,
    )

    def __init__(self, confidence_threshold: float = 0.70) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be within [0, 1]")
        self.confidence_threshold = confidence_threshold
        self.complaints = ComplaintArbitrator()
        self.evidence = EvidenceArbitrator()

    def evaluate(
        self, state: AgentState, *, rag_status: RagStatus | None = None
    ) -> RulesResult:
        if rag_status not in (None, "ok", "empty", "error"):
            raise ValueError("rag_status must be None, ok, empty, or error")

        understanding = state.understanding
        intent = (understanding.intent or "").strip().lower()

        # An urgent report cannot be downgraded by an unreliable classifier.
        urgent_reason = self.complaints.urgent_reason(state, intent)
        if urgent_reason is not None:
            return RulesResult(data=self.complaints.urgent_decision(state, urgent_reason))

        is_recommendation = (
            intent == "product_recommendation"
            or bool(self._RECOMMENDATION_REQUEST.search(state.user_text))
        )

        # This text mock has neither authenticated account access nor a
        # transaction executor. Retrieval must not be used as a substitute.
        if intent in self._ACCOUNT_READ_INTENTS or self._ACCOUNT_READ_REQUEST.search(state.user_text):
            return self._result(Action.BLOCK, "AUTHENTICATION_REQUIRED")
        if intent in self._TRANSACTION_INTENTS or self._TRANSACTION_REQUEST.search(state.user_text):
            return self._result(Action.BLOCK, "OPERATION_NOT_SUPPORTED")

        # Business constraints precede uncertainty: an open complaint cannot
        # be made marketable by low classifier confidence or a model response.
        if is_recommendation:
            if state.complaint_status in (
                ComplaintStatus.OPEN,
                ComplaintStatus.UNDER_REVIEW,
            ):
                return self._result(Action.BLOCK, "UNRESOLVED_COMPLAINT")
            if state.handoff_status != HandoffStatus.NOT_REQUIRED:
                return self._result(Action.BLOCK, "HANDOFF_ACTIVE")
            if state.complaint_status != ComplaintStatus.RESOLVED:
                return self._result(Action.BLOCK, "SERVICE_NOT_RESOLVED")
            if state.consent != ConsentStatus.GRANTED:
                return self._result(Action.BLOCK, "CONSENT_REQUIRED")
            if understanding.risk_level != RiskLevel.LOW:
                return self._result(Action.BLOCK, "RISK_NOT_CLEARED")

        if state.handoff_status != HandoffStatus.NOT_REQUIRED:
            return self._result(Action.ESCALATE, "HANDOFF_ALREADY_ACTIVE")

        confidence = understanding.confidence
        if confidence is None or confidence < self.confidence_threshold:
            return self._result(Action.CLARIFY, "LOW_INTENT_CONFIDENCE")
        if intent in self._UNKNOWN_INTENTS:
            return self._result(Action.CLARIFY, "UNKNOWN_INTENT")
        if understanding.risk_level == RiskLevel.UNKNOWN:
            return self._result(Action.CLARIFY, "UNKNOWN_RISK")

        complaint_decision = self.complaints.complaint_decision(state, intent)
        if complaint_decision is not None:
            return RulesResult(data=complaint_decision)

        if is_recommendation:
            # D still owns product eligibility and ranking. This action only
            # grants permission for E to invoke D.
            return self._result(Action.RECOMMEND, "RECOMMENDATION_PERMITTED")

        if rag_status is None:
            return self._result(Action.ANSWER, "POLICY_RETRIEVAL_PERMITTED")
        if rag_status == "error":
            return self._result(Action.ABSTAIN, "RETRIEVAL_ERROR")
        if rag_status == "empty" or not state.retrieved_docs:
            return self._result(Action.ABSTAIN, "INSUFFICIENT_EVIDENCE")
        evidence = self.evidence.assess(state.user_text, state.retrieved_docs)
        if not evidence.sufficient:
            if evidence.reason_code == "REPLACEMENT_REASON_REQUIRED":
                return self._result(Action.CLARIFY, evidence.reason_code)
            return self._result(Action.ABSTAIN, "INSUFFICIENT_EVIDENCE")
        return self._result(Action.ANSWER, "POLICY_EVIDENCE_FOUND")

    async def decide(self, state: AgentState) -> dict[str, object]:
        """Implement E's async ``RulesModule.decide(state)`` adapter.

        E clears ``state.decision`` before the first C call. It calls C again
        after B only when the first decision was ANSWER, leaving that decision
        on the state. This distinguishes the two calls without changing the
        shared AgentState schema. B's technical errors are handled by E.

        Return a mapping because E validates the result with its own
        ``schemas.module_results.RulesResult`` model, which is not the local
        envelope class used on the main branch.
        """

        after_retrieval = (
            state.decision is not None and state.decision.action == Action.ANSWER
        )
        result = self.evaluate(
            state, rag_status="ok" if after_retrieval else None
        )
        return result.model_dump(mode="json")

    @staticmethod
    def _result(
        action: Action,
        reason_code: str,
        *,
        complaint_status: ComplaintStatus | None = None,
        handoff_status: HandoffStatus | None = None,
    ) -> RulesResult:
        return RulesResult(
            data=Decision(
                action=action,
                reason_code=reason_code,
                next_state=RuleStatePatch(
                    complaint_status=complaint_status,
                    handoff_status=handoff_status,
                ),
            )
        )


def evaluate_rules(
    state: AgentState, *, rag_status: RagStatus | None = None
) -> RulesResult:
    """Convenience entry point for the default phase-one rule configuration."""

    return RuleEngine().evaluate(state, rag_status=rag_status)
