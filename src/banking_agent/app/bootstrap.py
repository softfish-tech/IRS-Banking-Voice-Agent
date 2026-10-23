"""Application composition root for interchangeable A/B/C/D adapters.

This module owns adapter selection only.  It does not contain domain policy or
module implementation logic.
"""

from dataclasses import dataclass
import os
from typing import Any, Mapping, Protocol

from banking_agent.app.demo import ScenarioModules
from banking_agent.app.observability import TraceContext, TraceSink
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.response_generator import (
    RecommendationResponseGenerator,
    ResponseGenerator,
    build_recommendation_response_generator_from_environment,
    build_response_generator_from_environment,
)
from banking_agent.app.llm_agent_support import (
    ClarificationGenerator,
    QueryRewriter,
    build_llm_text_assistant_from_environment,
    middle_loop_enabled,
)
from banking_agent.app.orchestrator.interfaces import (
    IntentModule,
    RecommendationModule,
    RetrievalModule,
    RulesModule,
)


@dataclass(frozen=True)
class ModuleBundle:
    """The four independently owned adapters required for one agent turn."""

    intent: IntentModule
    retrieval: RetrievalModule
    rules: RulesModule
    recommendation: RecommendationModule
    response_generator: ResponseGenerator | None = None
    recommendation_response_generator: RecommendationResponseGenerator | None = None
    query_rewriter: QueryRewriter | None = None
    clarification_generator: ClarificationGenerator | None = None

    def new_orchestrator(
        self,
        *,
        trace_sink: TraceSink | None = None,
        trace_context: TraceContext | None = None,
    ) -> Orchestrator:
        response_generator = self.response_generator
        if response_generator is None:
            response_generator = build_response_generator_from_environment()
        recommendation_response_generator = self.recommendation_response_generator
        if recommendation_response_generator is None:
            recommendation_response_generator = build_recommendation_response_generator_from_environment()
        assistant = build_llm_text_assistant_from_environment()
        query_rewriter = self.query_rewriter or (
            assistant
            if middle_loop_enabled()
            and os.environ.get("BANKING_AGENT_LLM_QUERY_REWRITE", "off").lower() == "llm"
            else None
        )
        clarification_generator = self.clarification_generator or (
            assistant if os.environ.get("BANKING_AGENT_LLM_CLARIFICATION", "off").lower() == "llm" else None
        )
        return Orchestrator(
            self.intent,
            self.retrieval,
            self.rules,
            self.recommendation,
            trace_sink=trace_sink,
            trace_context=trace_context,
            response_generator=response_generator,
            recommendation_response_generator=recommendation_response_generator,
            query_rewriter=query_rewriter,
            clarification_generator=clarification_generator,
        )


class ModuleFactory(Protocol):
    """Build a fresh adapter bundle without exposing selection to routes."""

    mode: str

    def create(self, *, scenario: Mapping[str, Any] | None = None) -> ModuleBundle: ...


class FixtureModuleFactory:
    """Development-only factory that replays a documented synthetic scenario."""

    mode = "fixture"

    def create(self, *, scenario: Mapping[str, Any] | None = None) -> ModuleBundle:
        if scenario is None or not isinstance(scenario.get("mock_outputs"), dict):
            raise ValueError("fixture_mode_requires_scenario_outputs")
        modules = ScenarioModules(dict(scenario["mock_outputs"]))
        return ModuleBundle(modules, modules, modules, modules)


class StaticModuleFactory:
    """Adapter factory for real module implementations supplied by their owners.

    The supplied adapters must implement the public orchestrator Protocols.
    Future production composition injects this factory; it never changes routes,
    persistence, UI, or the orchestrator itself.
    """

    mode = "production"

    def __init__(self, modules: ModuleBundle) -> None:
        self._modules = modules

    def create(self, *, scenario: Mapping[str, Any] | None = None) -> ModuleBundle:
        return self._modules


def build_module_factory(mode: str, *, production_modules: ModuleBundle | None = None) -> ModuleFactory:
    """Select an adapter mode and fail closed for an unconfigured production mode."""

    if mode == "fixture":
        return FixtureModuleFactory()
    if mode == "production" and production_modules is not None:
        return StaticModuleFactory(production_modules)
    if mode == "production":
        raise ValueError("production_mode_requires_explicit_module_bundle")
    raise ValueError("module_mode_must_be_fixture_or_production")
