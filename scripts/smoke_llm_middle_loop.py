"""Run a small paid DeepSeek smoke test for the constrained middle LLM loop.

This script loads the ignored repository-root .env itself. It sends only the
synthetic strings below and prints no credentials, prompts, or provider IDs.
It is intentionally not part of CI.
"""

from __future__ import annotations

import asyncio
import json
import os

from banking_agent.app.llm_agent_support import LLMTextAssistant, LLMUnderstanding
from banking_agent.app.local_env import load_local_env
from banking_agent.app.providers import LLMSettings, create_llm_client
from banking_agent.app.response_generator import GroundedResponseGenerator
from banking_agent.schemas import Action, AgentState, Decision, RetrievedDocument


async def main() -> None:
    load_local_env()
    settings = LLMSettings.from_environment()
    model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
    if not model:
        raise SystemExit("BANKING_AGENT_LLM_MODEL_required")
    client = create_llm_client(settings)
    understanding = LLMUnderstanding(client, model=model)
    assistant = LLMTextAssistant(client, model=model)
    response_generator = GroundedResponseGenerator(client, model=model)

    draft = await understanding.draft(
        "I was charged a fee that I do not understand.", request_id="smoke-understanding"
    )
    answer_state = AgentState(
        session_id="llm-middle-smoke",
        user_text="What is the synthetic replacement fee?",
        decision=Decision(action=Action.ANSWER, reason_code="POLICY_EVIDENCE_FOUND"),
        retrieved_docs=[
            RetrievedDocument(
                document_id="smoke-policy-1",
                title="Synthetic Replacement Fee Policy",
                source="Local synthetic smoke fixture",
                score=0.99,
                excerpt="The synthetic replacement fee is SGD 10.",
            )
        ],
    )
    query = await assistant.rewrite(answer_state, request_id="smoke-query")
    answer = await response_generator.generate(answer_state, request_id="smoke-answer")
    clarify_state = AgentState(
        session_id="llm-middle-smoke",
        user_text="What does it cost?",
        decision=Decision(action=Action.CLARIFY, reason_code="REPLACEMENT_REASON_REQUIRED"),
    )
    clarification = await assistant.clarify(clarify_state, request_id="smoke-clarify")

    checks = {
        "understanding": draft is not None,
        "query_rewrite": bool(query),
        "grounded_answer": bool(answer and "[Source: Synthetic Replacement Fee Policy; smoke-policy-1]" in answer),
        "clarification": bool(clarification),
    }
    print(json.dumps({"checks": checks, "all_passed": all(checks.values())}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
