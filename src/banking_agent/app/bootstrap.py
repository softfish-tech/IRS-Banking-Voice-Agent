"""Application composition root for interchangeable A/B/C/D adapters.

This module owns adapter selection only.  It does not contain domain policy or
module implementation logic.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from banking_agent.app.demo import ScenarioModules
from banking_agent.app.observability import TraceContext, TraceSink
from banking_agent.app.orchestrator import Orchestrator
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

    def new_orchestrator(
        self,
        *,
        trace_sink: TraceSink | None = None,
        trace_context: TraceContext | None = None,
    ) -> Orchestrator:
        return Orchestrator(
            self.intent,
            self.retrieval,
            self.rules,
            self.recommendation,
            trace_sink=trace_sink,
            trace_context=trace_context,
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
