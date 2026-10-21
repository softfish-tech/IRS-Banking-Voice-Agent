"""Deterministic complaint and urgent-risk arbitration for Module C.

The classifier supplies a signal, not authority to close a case or ignore an
urgent report.  This component never reads another domain module's internals.
"""

from __future__ import annotations

import re

from banking_agent.schemas.enums import Action, ComplaintStatus, HandoffStatus, RiskLevel
from banking_agent.schemas.state import AgentState, Decision, RuleStatePatch

from .state_machine import ComplaintStateMachine


class ComplaintArbitrator:
    """Select the safe case route before ordinary enquiry/recommendation rules."""

    _URGENT_INTENTS = {
        "unauthorized_transaction": "HIGH_RISK_TRANSACTION",
        "unauthorised_transaction": "HIGH_RISK_TRANSACTION",
        "fraud_suspicion": "FRAUD_SUSPICION",
        "suspected_fraud": "FRAUD_SUSPICION",
        "card_stolen": "CARD_SECURITY_RISK",
        "stolen_card": "CARD_SECURITY_RISK",
        "lost_card": "CARD_SECURITY_RISK",
        "compromised_credentials": "CREDENTIAL_SECURITY_RISK",
        "account_takeover": "ACCOUNT_SECURITY_RISK",
    }
    _URGENT_TEXT = (
        (re.compile(r"\b(?:someone|somebody)\b.{0,80}\b(?:used|spent|charged)\b.{0,80}\bwithout\b.{0,30}\b(?:permission|authori[sz]ation)\b", re.I), "HIGH_RISK_TRANSACTION"),
        (re.compile(r"\b(?:i|we)\s+(?:think|suspect|believe)\b.{0,80}\b(?:scam|fraud)\b", re.I), "FRAUD_SUSPICION"),
        # Keep this independent of A's risk classifier: a model may map this
        # wording to an innocuous BANKING77 label even though it reports an
        # attempt to induce a payment or transfer.
        (re.compile(r"\b(?:trick(?:ed|ing)?|deceiv(?:e|ed|ing)|coerc(?:e|ed|ing)|pressur(?:e|ed|ing))\b.{0,80}\b(?:transfer(?:ring)?|send(?:ing)?(?:\s+money)?|pay(?:ing)?|mak(?:e|ing)\s+(?:a\s+)?payment)\b", re.I), "FRAUD_SUSPICION"),
        (re.compile(r"\bmy\s+card\b.{0,35}\b(?:stolen|compromised|hacked)\b", re.I), "CARD_SECURITY_RISK"),
        (re.compile(r"\bmy\s+account\b.{0,35}\b(?:stolen|compromised|hacked|taken\s+over)\b", re.I), "ACCOUNT_SECURITY_RISK"),
        (re.compile(r"\bmy\s+(?:credentials|password|login)\b.{0,35}\b(?:stolen|compromised|hacked|leaked)\b", re.I), "CREDENTIAL_SECURITY_RISK"),
        (re.compile(r"\b(?:i\s+(?:lost|misplaced)\s+my\s+card|my\s+card\s+(?:is|was|has\s+been)\s+(?:lost|missing))\b", re.I), "CARD_SECURITY_RISK"),
    )
    _COMPLAINT_INTENTS = frozenset({"complaint", "fee_dispute", "charge_dispute"})
    _machine = ComplaintStateMachine()

    @classmethod
    def urgent_reason(cls, state: AgentState, intent: str) -> str | None:
        """Use explicit safety signals even when classifier confidence is low."""

        if intent in cls._URGENT_INTENTS:
            return cls._URGENT_INTENTS[intent]
        for pattern, reason in cls._URGENT_TEXT:
            if pattern.search(state.user_text):
                return reason
        if state.understanding.risk_level == RiskLevel.HIGH:
            return "HIGH_RISK_CASE"
        return None

    @staticmethod
    def urgent_decision(state: AgentState, reason_code: str) -> Decision:
        # Keep an existing unresolved case in its current lifecycle state.
        complaint_patch = (
            ComplaintArbitrator._machine.transition(
                state.complaint_status, "OPEN", actor="agent"
            )
            if state.complaint_status in (ComplaintStatus.NONE, ComplaintStatus.RESOLVED)
            else None
        )
        return Decision(
            action=Action.ESCALATE,
            reason_code=reason_code,
            next_state=RuleStatePatch(
                complaint_status=complaint_patch,
                handoff_status=(
                    HandoffStatus.ESCALATED
                    if state.handoff_status != HandoffStatus.ESCALATED
                    else None
                ),
            ),
        )

    @classmethod
    def complaint_decision(cls, state: AgentState, intent: str) -> Decision | None:
        if not (intent.endswith("_complaint") or intent in cls._COMPLAINT_INTENTS):
            return None
        if state.complaint_status == ComplaintStatus.OPEN:
            reason, patch = "COMPLAINT_ALREADY_OPEN", None
        elif state.complaint_status == ComplaintStatus.UNDER_REVIEW:
            reason, patch = "COMPLAINT_UNDER_REVIEW", None
        else:
            reason = "FEE_COMPLAINT" if intent == "fee_complaint" else "COMPLAINT_RECORDED"
            patch = cls._machine.transition(
                state.complaint_status, "OPEN", actor="agent"
            )
        return Decision(
            action=Action.HANDLE_COMPLAINT,
            reason_code=reason,
            next_state=RuleStatePatch(complaint_status=patch),
        )
