"""Reusable adapter contract assertions for A/B/C/D implementation owners.

These helpers use only public interfaces and schemas.  They intentionally do
not test an owner's domain policy, ranking quality, or model accuracy.
"""

from typing import Any

from pydantic import ValidationError

from banking_agent.app.orchestrator.interfaces import (
    IntentModule,
    RecommendationModule,
    RetrievalModule,
    RulesModule,
)
from banking_agent.schemas import AgentState, RiskLevel
from banking_agent.schemas.module_results import (
    IntentResult,
    RecommendationResult,
    RetrievalResult,
    RulesResult,
)


def _validated(model, raw: Any, adapter_name: str):
    try:
        return model.model_validate(raw)
    except (ValidationError, TypeError, ValueError) as error:
        raise AssertionError(f"{adapter_name} returned an invalid result envelope") from error


def validate_intent_result(raw: Any) -> IntentResult:
    result = _validated(IntentResult, raw, "A")
    if result.status == "empty":
        data = result.data
        if data.intent is not None or data.confidence is not None or data.risk_level != RiskLevel.UNKNOWN or data.entities:
            raise AssertionError("A empty result must contain unknown, empty understanding")
    return result


def validate_retrieval_result(raw: Any) -> RetrievalResult:
    result = _validated(RetrievalResult, raw, "B")
    if result.status == "empty" and result.data.docs:
        raise AssertionError("B empty result must not contain documents")
    return result


def validate_rules_result(raw: Any) -> RulesResult:
    result = _validated(RulesResult, raw, "C")
    if result.status == "empty":
        raise AssertionError("C has no normal empty result; return an action or technical error")
    return result


def validate_recommendation_result(raw: Any) -> RecommendationResult:
    result = _validated(RecommendationResult, raw, "D")
    if result.status == "empty":
        raise AssertionError("D denial is an ok result with allowed=false, not an empty result")
    if result.status == "ok" and not result.data.allowed and result.data.items:
        raise AssertionError("D must not return items when allowed=false")
    return result


async def assert_intent_adapter_contract(adapter: IntentModule, session_id: str, user_text: str) -> IntentResult:
    return validate_intent_result(await adapter.analyze(session_id, user_text))


async def assert_retrieval_adapter_contract(adapter: RetrievalModule, query: str, top_k: int = 3) -> RetrievalResult:
    return validate_retrieval_result(await adapter.retrieve(query, top_k))


async def assert_rules_adapter_contract(adapter: RulesModule, state: AgentState) -> RulesResult:
    return validate_rules_result(await adapter.decide(state.model_copy(deep=True)))


async def assert_recommendation_adapter_contract(
    adapter: RecommendationModule,
    session_id: str,
    complaint_status: str,
    handoff_status: str,
    consent: str,
) -> RecommendationResult:
    return validate_recommendation_result(
        await adapter.recommend(session_id, complaint_status, handoff_status, consent)
    )
