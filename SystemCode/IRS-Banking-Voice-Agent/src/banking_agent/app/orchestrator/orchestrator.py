"""Execute C-owned decisions without duplicating domain policy."""

import asyncio
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from banking_agent.app.observability import DecisionTrace, ModuleOutcome, TraceContext, TraceSink
from banking_agent.app.response_generator import RecommendationResponseGenerator, ResponseGenerator
from banking_agent.app.llm_agent_support import ClarificationGenerator, QueryRewriter
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
        recommendation_response_generator: RecommendationResponseGenerator | None = None,
        query_rewriter: QueryRewriter | None = None,
        clarification_generator: ClarificationGenerator | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.intent, self.retrieval = intent, retrieval
        self.rules, self.recommendation = rules, recommendation
        self.timeout_seconds = timeout_seconds
        self.trace_sink = trace_sink
        self.trace_context = trace_context or TraceContext()
        self.response_generator = response_generator
        self.recommendation_response_generator = recommendation_response_generator
        self.query_rewriter = query_rewriter
        self.clarification_generator = clarification_generator

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

    @staticmethod
    def _record_optional_llm(
        outcomes: list[ModuleOutcome], module: str, provider, *outcome_args: str
    ) -> None:
        """Record an optional LLM use/fallback without putting its content in a trace."""
        outcome = getattr(provider, "outcome", lambda *_: None)(*outcome_args)
        if outcome is not None:
            status, duration_ms, attempts, prompt_tokens, completion_tokens, total_tokens, *extra = outcome
            # The response generator may expose a bounded diagnostic code such
            # as ``invalid_citation``. It contains no model text or prompt.
            error_code = extra[0] if extra else None
            outcomes.append(ModuleOutcome(module, status, duration_ms, error_code=error_code, attempts=attempts, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens))

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
        state.context_reference_resolved, state.resolved_user_text = False, None
        request_id = request_id or str(uuid4())
        trace_started_at = perf_counter()
        outcomes: list[ModuleOutcome] = []
        failure: TechnicalError | None = None
        result_status = "error"
        try:
            contextual_analyze = getattr(self.intent, "analyze_with_context", None)
            if callable(contextual_analyze) and state.conversation_context.turns:
                outcomes.append(
                    ModuleOutcome(
                        "E.context_memory",
                        "ok",
                        0,
                        error_code=f"window_{len(state.conversation_context.turns)}",
                    )
                )
                understood = await self._call(
                    "A", contextual_analyze, IntentResult, outcomes,
                    state.session_id, state.user_text, state.conversation_context,
                )
            else:
                understood = await self._call(
                    "A", self.intent.analyze, IntentResult, outcomes,
                    state.session_id, state.user_text,
                )
            if getattr(self.intent, "last_llm_status", None) is not None:
                prompt_tokens, completion_tokens, total_tokens = self.intent.last_llm_tokens
                outcomes.append(ModuleOutcome("E.LLM.understanding", self.intent.last_llm_status, self.intent.last_llm_duration_ms, error_code=getattr(self.intent, "last_llm_disposition", None), attempts=self.intent.last_llm_attempts, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens))
            state.understanding = understood.data
            state.context_reference_resolved = bool(
                getattr(self.intent, "last_context_reference_resolved", False)
            )
            resolved_text = getattr(self.intent, "last_resolved_user_text", None)
            if state.context_reference_resolved and isinstance(resolved_text, str):
                state.resolved_user_text = resolved_text
            await self._decide(state, outcomes)
            if state.decision.action == Action.ANSWER:
                query = state.resolved_user_text or state.user_text
                if self.query_rewriter is not None:
                    rewritten = await self.query_rewriter.rewrite(state, request_id=request_id)
                    self._record_optional_llm(outcomes, "E.LLM.query_rewrite", self.query_rewriter, "retrieval query", request_id)
                    if rewritten:
                        # Preserve the original customer wording so a fluent
                        # rewrite cannot drop a B-critical term or condition.
                        query = f"{query}\n{rewritten}"
                evidence = await self._call("B", self.retrieval.retrieve, RetrievalResult, outcomes, query, 5)
                if evidence.status == "empty" and evidence.data.docs:
                    raise CallFailure("B", "invalid_result")
                state.retrieved_docs = evidence.data.docs
                # B supplies bounded ranked candidates.  The real C hook may
                # remove malformed or duplicate items, but leaves ordinary
                # relevance ranking to B and multi-document synthesis to the
                # grounded response generator. Fixture and third-party rule
                # adapters remain compatible without this hook.
                select_evidence = getattr(self.rules, "select_relevant_evidence", None)
                if callable(select_evidence):
                    state.retrieved_docs = select_evidence(
                        state.resolved_user_text or state.user_text,
                        state.retrieved_docs,
                    )
                await self._decide(state, outcomes)
                if state.decision.action != Action.ANSWER:
                    # B's candidates were supplied to C for its final
                    # evidence decision, but must not survive into a response
                    # or a request trace once C declines to answer. In
                    # particular, an ambiguous generic replacement-fee query
                    # may retrieve a lost-card branch solely to identify the
                    # missing condition; that branch is not approved evidence.
                    state.retrieved_docs = []
                elif not state.retrieved_docs:
                    raise CallFailure("C", "invalid_result")
            if state.decision.action == Action.RECOMMEND:
                products = await self._call("D", self.recommendation.recommend, RecommendationResult, outcomes, state.session_id, state.complaint_status.value, state.handoff_status.value, state.consent.value)
                if products.data.allowed and products.status == "ok":
                    state.recommendations = products.data.items
            state.final_response = build_response(state)
            if (
                state.decision.action == Action.RECOMMEND
                and self.recommendation_response_generator is not None
            ):
                introduction = await self.recommendation_response_generator.present(
                    state, request_id=request_id
                )
                self._record_optional_llm(
                    outcomes,
                    "E.LLM.recommendation_presentation",
                    self.recommendation_response_generator,
                    request_id,
                )
                if introduction and introduction.strip():
                    # Keep D's names, ranking and eligibility reasons canonical.
                    state.final_response = f"{introduction}\n\n{state.final_response}"
            if state.decision.action == Action.CLARIFY and self.clarification_generator is not None:
                clarification = await self.clarification_generator.clarify(state, request_id=request_id)
                self._record_optional_llm(outcomes, "E.LLM.clarification", self.clarification_generator, "clarifying question", request_id)
                if clarification and clarification.strip():
                    state.final_response = clarification
            if state.decision.action == Action.ANSWER and self.response_generator is not None:
                generated = await self.response_generator.generate(state, request_id=request_id)
                self._record_optional_llm(outcomes, "E.LLM.grounded_response", self.response_generator, request_id)
                if generated and generated.strip():
                    state.final_response = generated
            # Optional renderers must never replace a safe deterministic
            # response with empty/whitespace output.  Besides preventing a
            # blank customer message, a non-empty completed public turn is a
            # prerequisite for bounded E-owned conversation memory.
            if not state.final_response or not state.final_response.strip():
                state.final_response = build_response(state)
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
