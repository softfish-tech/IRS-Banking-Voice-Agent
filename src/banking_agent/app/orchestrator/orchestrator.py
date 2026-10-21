"""Execute C-owned decisions without duplicating domain policy."""

import asyncio
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from banking_agent.app.observability import DecisionTrace, ModuleOutcome, TraceContext, TraceSink
from banking_agent.app.response_generator import ResponseGenerator
from banking_agent.schemas import Action, AgentState
from banking_agent.schemas.module_results import IntentResult, RecommendationResult, RetrievalResult, RulesResult
from banking_agent.schemas.response import AgentResponse, TechnicalError

from .interfaces import IntentModule, RecommendationModule, RetrievalModule, RulesModule
from .response_builder import build_response


class CallFailure(Exception):
    def __init__(self, module: str, code: str) -> None:
        self.error = TechnicalError(module=module, code=code)


class Orchestrator:
    def __init__(
        self,
        intent: IntentModule,
        retrieval: RetrievalModule,
        rules: RulesModule,
        recommendation: RecommendationModule,
        *,
        timeout_seconds: float = 10,
        trace_sink: TraceSink | None = None,
        trace_context: TraceContext | None = None,
        response_generator: ResponseGenerator | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.intent, self.retrieval = intent, retrieval
        self.rules, self.recommendation = rules, recommendation
        self.timeout_seconds = timeout_seconds
        self.trace_sink = trace_sink
        self.trace_context = trace_context or TraceContext()
        self.response_generator = response_generator

    async def _call(self, module: str, method, model, outcomes: list[ModuleOutcome], *args):
        started_at = perf_counter()
        try:
            raw = await asyncio.wait_for(method(*args), self.timeout_seconds)
        except TimeoutError:
            outcomes.append(ModuleOutcome(module, "error", round((perf_counter() - started_at) * 1000), "timeout"))
            raise CallFailure(module, "timeout") from None
        except Exception:
            outcomes.append(ModuleOutcome(module, "error", round((perf_counter() - started_at) * 1000), "exception"))
            raise CallFailure(module, "exception") from None
        try:
            result = model.model_validate(raw)
        except (ValidationError, TypeError, ValueError):
            outcomes.append(ModuleOutcome(module, "error", round((perf_counter() - started_at) * 1000), "invalid_result"))
            raise CallFailure(module, "invalid_result") from None
        if result.status == "error":
            outcomes.append(ModuleOutcome(module, "error", round((perf_counter() - started_at) * 1000), "module_error"))
            raise CallFailure(module, "module_error")
        outcomes.append(ModuleOutcome(module, result.status, round((perf_counter() - started_at) * 1000)))
        return result

    async def _decide(self, state: AgentState, outcomes: list[ModuleOutcome]) -> None:
        result = await self._call("C", self.rules.decide, RulesResult, outcomes, state.model_copy(deep=True))
        if result.status != "ok":
            raise CallFailure("C", "invalid_result")
        state.decision = result.data
        for key, value in result.data.next_state.model_dump(exclude_none=True).items():
            setattr(state, key, value)

    def _record_trace(
        self,
        *,
        request_id: str,
        initial_state: AgentState,
        final_state: AgentState,
        outcomes: list[ModuleOutcome],
        result_status: str,
        failure: TechnicalError | None,
        started_at: float,
    ) -> None:
        if self.trace_sink is None:
            return
        trace = DecisionTrace.create(
            request_id=request_id,
            initial_state=initial_state,
            final_state=final_state,
            context=self.trace_context,
            modules=outcomes,
            result_status=result_status,
            technical_error_module=failure.module if failure else None,
            technical_error_code=failure.code if failure else None,
            duration_ms=round((perf_counter() - started_at) * 1000),
        )
        try:
            self.trace_sink.record_trace(trace)
        except Exception:
            # Observability must not turn a completed safe decision into an API failure.
            pass

    async def handle(self, initial_state: AgentState, *, request_id: str | None = None) -> AgentResponse:
        state = initial_state.model_copy(deep=True)
        # Request-local outputs must not leak from a previous conversation turn.
        state.retrieved_docs, state.recommendations = [], []
        state.decision, state.final_response = None, None
        request_id = request_id or str(uuid4())
        trace_started_at = perf_counter()
        outcomes: list[ModuleOutcome] = []
        failure: TechnicalError | None = None
        result_status = "error"
        try:
            understood = await self._call("A", self.intent.analyze, IntentResult, outcomes, state.session_id, state.user_text)
            state.understanding = understood.data
            await self._decide(state, outcomes)
            if state.decision.action == Action.ANSWER:
                evidence = await self._call("B", self.retrieval.retrieve, RetrievalResult, outcomes, state.user_text, 3)
                if evidence.status == "empty" and evidence.data.docs:
                    raise CallFailure("B", "invalid_result")
                state.retrieved_docs = evidence.data.docs
                await self._decide(state, outcomes)
                if state.decision.action == Action.ANSWER and not state.retrieved_docs:
                    raise CallFailure("C", "invalid_result")
            if state.decision.action == Action.RECOMMEND:
                products = await self._call("D", self.recommendation.recommend, RecommendationResult, outcomes, state.session_id, state.complaint_status.value, state.handoff_status.value, state.consent.value)
                if products.data.allowed and products.status == "ok":
                    state.recommendations = products.data.items
            state.final_response = build_response(state)
            if state.decision.action == Action.ANSWER and self.response_generator is not None:
                generated = await self.response_generator.generate(state, request_id=request_id)
                if generated is not None:
                    state.final_response = generated
            result_status = "ok"
            return AgentResponse(request_id=request_id, session_id=state.session_id, status="ok", decision=state.decision, text=state.final_response, citations=state.retrieved_docs if state.decision.action == Action.ANSWER else [], recommendations=state.recommendations, state=state)
        except CallFailure as caught_failure:
            failure = caught_failure.error
            state.recommendations = []
            state.final_response = "The request could not be completed because a module failed. Please try again."
            return AgentResponse(request_id=request_id, session_id=state.session_id, status="error", text=state.final_response, error=failure, state=state)
        finally:
            self._record_trace(
                request_id=request_id,
                initial_state=initial_state,
                final_state=state,
                outcomes=outcomes,
                result_status=result_status,
                failure=failure,
                started_at=trace_started_at,
            )
