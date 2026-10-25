"""Async public adapter interfaces; domain implementations remain owner-managed."""
from typing import Protocol, Mapping, Any
from banking_agent.schemas.state import AgentState
from banking_agent.schemas.module_results import IntentResult, RetrievalResult, RulesResult, RecommendationResult

RawResult = Mapping[str, Any]

class IntentModule(Protocol):
    async def analyze(self, session_id: str, user_text: str) -> IntentResult | RawResult: ...

class RetrievalModule(Protocol):
    async def retrieve(self, query: str, top_k: int) -> RetrievalResult | RawResult: ...

class RulesModule(Protocol):
    async def decide(self, state: AgentState) -> RulesResult | RawResult: ...

class RecommendationModule(Protocol):
    async def recommend(self, session_id: str, complaint_status: str, handoff_status: str, consent: str) -> RecommendationResult | RawResult: ...
