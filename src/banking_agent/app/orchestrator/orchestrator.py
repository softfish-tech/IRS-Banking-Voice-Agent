"""Execute C-owned decisions without duplicating domain policy."""
import asyncio
from uuid import uuid4
from pydantic import ValidationError
from banking_agent.schemas import Action, AgentState
from banking_agent.schemas.module_results import IntentResult, RetrievalResult, RulesResult, RecommendationResult
from banking_agent.schemas.response import AgentResponse, TechnicalError
from .interfaces import IntentModule, RetrievalModule, RulesModule, RecommendationModule
from .response_builder import build_response

class CallFailure(Exception):
    def __init__(self, module, code):
        self.error = TechnicalError(module=module, code=code)

class Orchestrator:
    def __init__(self, intent: IntentModule, retrieval: RetrievalModule, rules: RulesModule, recommendation: RecommendationModule, *, timeout_seconds: float = 10):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.intent, self.retrieval = intent, retrieval
        self.rules, self.recommendation = rules, recommendation
        self.timeout_seconds = timeout_seconds

    async def _call(self, module, method, model, *args):
        try:
            raw = await asyncio.wait_for(method(*args), self.timeout_seconds)
        except TimeoutError:
            raise CallFailure(module, "timeout") from None
        except Exception:
            raise CallFailure(module, "exception") from None
        try:
            result = model.model_validate(raw)
        except (ValidationError, TypeError, ValueError):
            raise CallFailure(module, "invalid_result") from None
        if result.status == "error":
            raise CallFailure(module, "module_error")
        return result

    async def _decide(self, state):
        result = await self._call("C", self.rules.decide, RulesResult, state.model_copy(deep=True))
        if result.status != "ok":
            raise CallFailure("C", "invalid_result")
        state.decision = result.data
        for key, value in result.data.next_state.model_dump(exclude_none=True).items():
            setattr(state, key, value)

    async def handle(self, initial_state: AgentState, *, request_id: str | None = None) -> AgentResponse:
        state = initial_state.model_copy(deep=True)
        # Request-local outputs must not leak from a previous conversation turn.
        state.retrieved_docs, state.recommendations = [], []
        state.decision, state.final_response = None, None
        request_id = request_id or str(uuid4())
        try:
            understood = await self._call("A", self.intent.analyze, IntentResult, state.session_id, state.user_text)
            state.understanding = understood.data
            await self._decide(state)
            if state.decision.action == Action.ANSWER:
                evidence = await self._call("B", self.retrieval.retrieve, RetrievalResult, state.user_text, 3)
                if evidence.status == "empty" and evidence.data.docs:
                    raise CallFailure("B", "invalid_result")
                state.retrieved_docs = evidence.data.docs
                await self._decide(state)
                if state.decision.action == Action.ANSWER and not state.retrieved_docs:
                    # Invalid permission is a contract failure, not an E-owned ABSTAIN decision.
                    raise CallFailure("C", "invalid_result")
            if state.decision.action == Action.RECOMMEND:
                products = await self._call("D", self.recommendation.recommend, RecommendationResult, state.session_id, state.complaint_status.value, state.handoff_status.value, state.consent.value)
                if products.data.allowed and products.status == "ok":
                    state.recommendations = products.data.items
            state.final_response = build_response(state)
            return AgentResponse(request_id=request_id, session_id=state.session_id, status="ok", decision=state.decision, text=state.final_response, citations=state.retrieved_docs if state.decision.action == Action.ANSWER else [], recommendations=state.recommendations, state=state)
        except CallFailure as failure:
            state.recommendations = []
            state.final_response = "The request could not be completed because a module failed. Please try again."
            return AgentResponse(request_id=request_id, session_id=state.session_id, status="error", text=state.final_response, error=failure.error, state=state)
