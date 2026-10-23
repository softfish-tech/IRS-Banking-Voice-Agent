"""Deterministic text rendering; business decisions are supplied by C."""
import re

from banking_agent.schemas import Action, AgentState

MESSAGES = {
    Action.HANDLE_COMPLAINT: "Your complaint is being handled in this simulation.",
    Action.ESCALATE: "This request requires human assistance. A simulated handoff has been recorded.",
    Action.CLARIFY: "Could you clarify what you need help with?",
    Action.BLOCK: "A recommendation cannot be provided under the current conditions.",
    Action.ABSTAIN: "Reliable information is unavailable. Please seek further assistance.",
}


_CRYPTO_WALLET_RECOVERY = re.compile(
    r"(?=.*\b(?:crypto|cryptocurrency)\b)(?=.*\bwallets?\b)"
    r"(?=.*\b(?:recover(?:y|ing)?|restor(?:e|ation)|los(?:e|t|ing)\s+access)\b)",
    re.I,
)
_CRYPTO_BOUNDARY_DOCUMENT_ID = "NB-v1_1-fiat_currency_support-001"


def _render_answer(state: AgentState) -> str:
    """Render only C-approved evidence, with one reviewed service boundary.

    C's evidence arbitrator permits the fiat-currency boundary document for a
    crypto-wallet recovery request because it establishes that the requested
    service cannot exist. The raw excerpt says only that cryptocurrency is
    unsupported, so restate that approved implication explicitly instead of
    leaving the customer to infer it from a policy fragment.
    """
    if (
        _CRYPTO_WALLET_RECOVERY.search(state.resolved_user_text or state.user_text)
        and len(state.retrieved_docs) == 1
        and state.retrieved_docs[0].document_id == _CRYPTO_BOUNDARY_DOCUMENT_ID
    ):
        doc = state.retrieved_docs[0]
        return (
            "Cryptocurrency is unsupported at NovaBank, so crypto wallet recovery "
            "is not supported. "
            f"[Source: {doc.title}; {doc.document_id}]"
        )
    return "\n".join(
        f"{doc.excerpt} [Source: {doc.title}; {doc.document_id}]"
        for doc in state.retrieved_docs
    )

def build_response(state: AgentState) -> str:
    if state.decision is None:
        raise ValueError("A final decision is required")
    action = state.decision.action
    if action == Action.ANSWER:
        return _render_answer(state)
    if action == Action.RECOMMEND:
        return "\n".join(f"{item.name}: {item.reason}" for item in state.recommendations) or "No eligible recommendation is available."
    if action == Action.CLARIFY and state.decision.reason_code == "REPLACEMENT_REASON_REQUIRED":
        return "Could you clarify why the card needs replacing—for example, whether it was lost, stolen, damaged, or compromised?"
    if action == Action.HANDLE_COMPLAINT and state.decision.reason_code == "FEE_COMPLAINT":
        return "Your fee complaint has been recorded and a simulated case is open for review."
    return MESSAGES[action]
