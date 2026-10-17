"""Deterministic text rendering; business decisions are supplied by C."""
from banking_agent.schemas import Action, AgentState

MESSAGES = {
    Action.HANDLE_COMPLAINT: "Your complaint is being handled in this simulation.",
    Action.ESCALATE: "This request requires human assistance. A simulated handoff has been recorded.",
    Action.CLARIFY: "Could you clarify what you need help with?",
    Action.BLOCK: "A recommendation cannot be provided under the current conditions.",
    Action.ABSTAIN: "Reliable information is unavailable. Please seek further assistance.",
}

def build_response(state: AgentState) -> str:
    if state.decision is None:
        raise ValueError("A final decision is required")
    action = state.decision.action
    if action == Action.ANSWER:
        return "\n".join(f"{doc.excerpt} [Source: {doc.title}; {doc.document_id}]" for doc in state.retrieved_docs)
    if action == Action.RECOMMEND:
        return "\n".join(f"{item.name}: {item.reason}" for item in state.recommendations) or "No eligible recommendation is available."
    return MESSAGES[action]
