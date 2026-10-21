"""Paid terminal E2E check: real MiniLM, B/C/D, and constrained DeepSeek help."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from banking_agent.app.llm_agent_support import FusedIntentModule, LLMTextAssistant, LLMUnderstanding
from banking_agent.app.local_env import load_local_env
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.providers import LLMSettings, create_llm_client
from banking_agent.app.response_generator import GroundedResponseGenerator
from banking_agent.app.retrieval_adapter import AsyncRetrievalAdapter
from banking_agent.modules.intent import EncoderIntentClassifier, IntentModuleAdapter
from banking_agent.modules.rag.retriever import create_retriever
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture
from banking_agent.modules.rules import RuleEngine
from banking_agent.schemas import AgentState


ROOT = Path(__file__).resolve().parents[1]


class DeterministicReranker:
    def rerank(self, query, candidates, top_k=5):
        return [dict(item, score=float(top_k - index)) for index, item in enumerate(candidates[:top_k])]


class Recording:
    def __init__(self, name, delegate, calls): self.name, self.delegate, self.calls = name, delegate, calls
    async def analyze(self, *args): self.calls.append(self.name); return await self.delegate.analyze(*args)
    async def retrieve(self, *args): self.calls.append(self.name); return await self.delegate.retrieve(*args)
    async def decide(self, *args): self.calls.append(self.name); return await self.delegate.decide(*args)
    async def recommend(self, *args): self.calls.append(self.name); return await self.delegate.recommend(*args)


async def main() -> None:
    load_local_env()
    model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
    if not model: raise SystemExit("BANKING_AGENT_LLM_MODEL_required")
    client = create_llm_client(LLMSettings.from_environment())
    classifier = EncoderIntentClassifier.from_pretrained()
    intent = FusedIntentModule(IntentModuleAdapter(classifier=classifier.classify), LLMUnderstanding(client, model=model))
    retrieval = AsyncRetrievalAdapter(create_retriever("real", reranker=DeterministicReranker()))
    recommendation = RecommendationAdapter(load_fixture(ROOT / "data/fixtures/recommendation.json"))
    cases = [
        ("answer", "How much does express card delivery cost?", {}, "ANSWER"),
        ("no_evidence", "What is the bank policy for crypto wallet recovery?", {}, "ABSTAIN"),
        ("fraud", "I think someone is trying to trick me into making this transfer.", {}, "ESCALATE"),
        ("complaint", "I was charged a fee I do not understand.", {}, "HANDLE_COMPLAINT"),
        ("recommend", "Can you recommend a suitable savings product?", {"complaint_status": "RESOLVED", "consent": "GRANTED"}, "RECOMMEND"),
    ]
    rows = []
    for name, text, state_values, expected in cases:
        calls = []
        orchestrator = Orchestrator(
            Recording("A", intent, calls), Recording("B", retrieval, calls), Recording("C", RuleEngine(), calls), Recording("D", recommendation, calls),
            query_rewriter=LLMTextAssistant(client, model=model),
            clarification_generator=LLMTextAssistant(client, model=model),
            response_generator=GroundedResponseGenerator(client, model=model),
            timeout_seconds=60,
        )
        response = await orchestrator.handle(AgentState(session_id="session-001", user_text=text, **state_values), request_id=f"real-e2e-{name}")
        rows.append({"case": name, "expected": expected, "actual": response.decision.action.value if response.decision else None, "passed": response.status == "ok" and response.decision and response.decision.action.value == expected, "modules": calls})
    print(json.dumps({"all_passed": all(row["passed"] for row in rows), "rows": rows}, indent=2))
    if not all(row["passed"] for row in rows): raise SystemExit(1)


if __name__ == "__main__": asyncio.run(main())
