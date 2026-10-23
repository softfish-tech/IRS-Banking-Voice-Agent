"""E-owned bounded recent-turn context for the B0 delivery slice.

The persistence layer already stores public user/assistant messages. This
module converts only complete, successful pairs into a small validated window;
it does not create business state or put dialogue text into decision traces.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from typing import Any

from banking_agent.schemas import Action, ConversationContext, ConversationTurn


_MAX_USER_TEXT = 2_000
_MAX_ASSISTANT_TEXT = 8_000


def deterministic_follow_up_resolution(
    user_text: str, context: ConversationContext
) -> str | None:
    """Resolve only reviewed, unambiguous follow-up forms.

    This is a fail-closed B0 fallback for provider timeouts: it never adds a
    policy fact, and it only supplies the subject already explicit in the most
    recent customer turn. All other references remain for the LLM resolver or
    C clarification.
    """

    if not context.turns:
        return None
    prior = context.turns[-1].user_text.casefold()
    recent = "\n".join(turn.user_text.casefold() for turn in context.turns)
    current = user_text.strip().casefold().rstrip("?!.")
    prior_tokens = set(re.findall(r"[a-z]+", prior))
    is_replacement_card = {"replacement", "card"} <= prior_tokens
    if is_replacement_card:
        if current == "does that include delivery" and "fee" in prior:
            return "Does the replacement-card fee include delivery?"
        if current == "can i get it today":
            return "Can I receive a replacement card today?"
        if current == "when will it arrive":
            return "When will the replacement card arrive?"
        if current == "can i dispute it" and "fee" in prior:
            return "Can I dispute the replacement-card fee?"
        # This is an answer to E's preceding replacement-condition
        # clarification, not a fresh safety report.  It is deliberately
        # restricted to the exact damaged-card wording; lost, stolen, and
        # compromised cards keep their raw-text safety routes.
        if current in {"it was damaged", "it is damaged"}:
            if "fee" in prior or "how much" in prior:
                return "What is the replacement-card fee for a damaged card?"
            return "When will a damaged replacement card arrive?"
    if "replacement" in recent and "card" in recent and current in {"it was damaged", "it is damaged"}:
        return "When will a damaged replacement card arrive?"
    if "replacement" in recent and "card" in recent and "fee" in recent:
        if current == "how much exactly":
            return "What is the replacement-card fee?"
        if current == "back to the card fee: how much is it":
            return "What is the replacement-card fee?"
    if "damage" in recent and "card" in recent and current == "what should i do now":
        return "What should I do to replace my damaged card?"
    if "transfer" in prior_tokens and current in {
        "it is still pending", "still pending", "it is pending"
    }:
        return "My bank transfer is still pending. What should I do?"
    if "crypto" in recent and "wallet" in recent:
        if current == "what if i lost access to it":
            return "What if I lose access to my crypto wallet?"
        if current == "can you recover the crypto for me":
            return "Can NovaBank recover my crypto wallet for me?"
    return None


def context_memory_enabled() -> bool:
    """Keep semantic memory an explicit delivery opt-in during B0."""

    selected = os.environ.get("BANKING_AGENT_CONTEXT_MEMORY", "off").strip().lower()
    if selected not in {"off", "enabled"}:
        raise ValueError("context_memory_must_be_off_or_enabled")
    return selected == "enabled"


def recent_public_context(
    messages: Sequence[Mapping[str, Any]], *, max_turns: int = 3
) -> ConversationContext:
    """Return the latest complete public pairs without trusting partial rows."""

    if not 1 <= max_turns <= 3:
        raise ValueError("context_window_must_be_between_1_and_3")
    turns: list[ConversationTurn] = []
    index = 0
    while index + 1 < len(messages):
        user, assistant = messages[index], messages[index + 1]
        index += 2
        if user.get("role") != "user" or assistant.get("role") != "assistant":
            continue
        response = assistant.get("response")
        if not isinstance(response, Mapping) or response.get("status") != "ok":
            continue
        decision = response.get("decision")
        if not isinstance(decision, Mapping):
            continue
        try:
            turns.append(
                ConversationTurn(
                    # A public answer may contain several retrieved excerpts.
                    # Keep the completed pair and its action while bounding
                    # the non-authoritative LLM context; discarding the whole
                    # pair would make later resolution depend on answer size.
                    user_text=str(user["content"])[:_MAX_USER_TEXT],
                    assistant_text=str(assistant["content"])[:_MAX_ASSISTANT_TEXT],
                    action=Action(str(decision["action"])),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return ConversationContext(turns=turns[-max_turns:])
