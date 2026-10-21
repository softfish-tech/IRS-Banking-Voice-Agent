"""Constrained LLM assistance for understanding, retrieval and clarification.

These helpers only propose typed text. C remains the sole owner of actions and
state transitions; failures always return ``None`` so E uses its safe fallback.
"""
from __future__ import annotations

import json
import os
from time import perf_counter
from typing import Protocol

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from banking_agent.app.providers import LLMClient, LLMMessage, LLMRequest, LLMSettings, create_llm_client
from banking_agent.modules.intent.taxonomy import ENTITY_TYPES, OPERATIONAL_INTENTS, UNKNOWN_INTENT, RISK_ORDER
from banking_agent.schemas import Action, AgentState, Entity, RiskLevel, UnderstandingResult
from banking_agent.schemas.module_results import IntentResult


class UnderstandingDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")
    intent: str
    confidence: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    entities: list[Entity] = Field(default_factory=list, max_length=12)

    @field_validator("intent")
    @classmethod
    def operational_intent_only(cls, value: str) -> str:
        if value not in OPERATIONAL_INTENTS | {UNKNOWN_INTENT}:
            raise ValueError("unsupported_operational_intent")
        return value

    @field_validator("entities")
    @classmethod
    def controlled_entity_types(cls, value: list[Entity]) -> list[Entity]:
        if any(item.type not in ENTITY_TYPES for item in value):
            raise ValueError("unsupported_entity_type")
        return value


class TextDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str = Field(
        min_length=1,
        max_length=600,
        validation_alias=AliasChoices("text", "question", "query"),
    )


class QueryRewriter(Protocol):
    async def rewrite(self, state: AgentState, *, request_id: str) -> str | None: ...


class ClarificationGenerator(Protocol):
    async def clarify(self, state: AgentState, *, request_id: str) -> str | None: ...


class LLMUnderstanding:
    def __init__(self, client: LLMClient, *, model: str) -> None:
        self.client, self.model = client, model
        self.last_attempts = 0
        self.last_prompt_tokens: int | None = None
        self.last_completion_tokens: int | None = None
        self.last_total_tokens: int | None = None

    async def draft(self, text: str, *, request_id: str) -> UnderstandingDraft | None:
        self.last_attempts = 0
        self.last_prompt_tokens = self.last_completion_tokens = self.last_total_tokens = None
        messages = (
            LLMMessage(role="system", content="Return JSON only. Classify banking text into the supplied operational intents; propose no business action."),
            LLMMessage(role="user", content=json.dumps({"text": text, "intents": sorted(OPERATIONAL_INTENTS | {UNKNOWN_INTENT}), "entity_types": sorted(ENTITY_TYPES), "required_json_example": {"intent": "fee_complaint", "confidence": 0.9, "risk_level": "MEDIUM", "entities": [{"type": "payment_method", "value": "card", "confidence": 0.9}]}, "entity_rule": "Use [] when unsure; each entity must use type, value, and optional confidence only."})),
        )
        # DeepSeek JSON mode can occasionally return empty content. This is a
        # non-authoritative proposal, so one fresh retry is safe; C still gets
        # A's baseline result if both attempts fail.
        for attempt in range(2):
            request = LLMRequest(model=self.model, messages=messages, max_output_tokens=1_200, temperature=0, idempotency_key=f"understanding-{request_id}-{attempt}")
            try:
                result = await self.client.generate(request, UnderstandingDraft)
                self.last_attempts += result.attempts
                self.last_prompt_tokens = result.prompt_tokens
                self.last_completion_tokens = result.completion_tokens
                self.last_total_tokens = result.total_tokens
                if result.status == "ok" and result.data:
                    return UnderstandingDraft.model_validate(result.data)
            except Exception:
                pass
        return None


class FusedIntentModule:
    """Merge public A output with an LLM proposal without weakening risk."""
    def __init__(self, baseline, llm: LLMUnderstanding) -> None:
        self.baseline, self.llm = baseline, llm
        self.last_llm_status: str | None = None
        self.last_llm_duration_ms = 0
        self.last_llm_attempts: int | None = None
        self.last_llm_tokens: tuple[int | None, int | None, int | None] = (None, None, None)

    async def analyze(self, session_id: str, user_text: str) -> dict[str, object]:
        self.last_llm_status, self.last_llm_duration_ms, self.last_llm_attempts = None, 0, None
        self.last_llm_tokens = (None, None, None)
        raw = await self.baseline.analyze(session_id, user_text)
        baseline = IntentResult.model_validate(raw)
        if baseline.status != "ok" or baseline.data is None:
            return raw
        started_at = perf_counter()
        draft = await self.llm.draft(user_text, request_id=f"{session_id}-understanding")
        self.last_llm_duration_ms = round((perf_counter() - started_at) * 1000)
        self.last_llm_attempts = self.llm.last_attempts
        self.last_llm_tokens = (self.llm.last_prompt_tokens, self.llm.last_completion_tokens, self.llm.last_total_tokens)
        if draft is None:
            self.last_llm_status = "fallback"
            return raw
        self.last_llm_status = "ok"
        data = baseline.data
        use_draft = (
            draft.confidence >= 0.75
            and (
                data.intent in {UNKNOWN_INTENT, "policy_enquiry"}
                or (data.confidence or 0) < 0.70
                # A higher risk proposal may correct a coarse low-risk route;
                # the separate max() below still prevents any downgrade.
                or RISK_ORDER[draft.risk_level] > RISK_ORDER[data.risk_level]
                or (
                    draft.confidence >= 0.90
                    and RISK_ORDER[draft.risk_level] >= RISK_ORDER[data.risk_level]
                )
            )
        )
        intent = draft.intent if use_draft else data.intent
        confidence = draft.confidence if use_draft else data.confidence
        risk = draft.risk_level if RISK_ORDER[draft.risk_level] > RISK_ORDER[data.risk_level] else data.risk_level
        entities = { (item.type, item.value): item for item in data.entities }
        entities.update({(item.type, item.value): item for item in draft.entities})
        return {"status": "ok", "data": UnderstandingResult(intent=intent, confidence=confidence, risk_level=risk, entities=list(entities.values())).model_dump(mode="json")}


class LLMTextAssistant:
    def __init__(self, client: LLMClient, *, model: str) -> None:
        self.client, self.model = client, model
        self.last_outcomes: dict[tuple[str, str], tuple[str, int, int, int | None, int | None, int | None]] = {}

    async def _text(self, kind: str, payload: dict[str, object], request_id: str) -> str | None:
        started_at = perf_counter()
        request = LLMRequest(model=self.model, messages=(
            LLMMessage(role="system", content=f"Return JSON only in the shape {{\"text\": \"...\"}}. Produce a short {kind}; do not make business decisions or add facts."),
            LLMMessage(role="user", content=json.dumps(payload)),
        ), max_output_tokens=600, temperature=0, idempotency_key=f"{kind}-{request_id}")
        try:
            result = await self.client.generate(request, TextDraft)
            text = TextDraft.model_validate(result.data).text if result.status == "ok" and result.data else None
        except Exception:
            text = None
            result = None
        self.last_outcomes[(kind, request_id)] = (
            "ok" if text is not None else "fallback",
            round((perf_counter() - started_at) * 1000),
            result.attempts if result is not None else 0,
            result.prompt_tokens if result is not None else None,
            result.completion_tokens if result is not None else None,
            result.total_tokens if result is not None else None,
        )
        return text

    def outcome(self, kind: str, request_id: str) -> tuple[str, int, int, int | None, int | None, int | None] | None:
        return self.last_outcomes.pop((kind, request_id), None)

    async def rewrite(self, state: AgentState, *, request_id: str) -> str | None:
        if state.decision is None or state.decision.action != Action.ANSWER:
            return None
        return await self._text("retrieval query", {"question": state.user_text, "intent": state.understanding.intent}, request_id)

    async def clarify(self, state: AgentState, *, request_id: str) -> str | None:
        if state.decision is None or state.decision.action != Action.CLARIFY:
            return None
        return await self._text("clarifying question", {"question": state.user_text, "reason_code": state.decision.reason_code}, request_id)


def _model() -> str:
    model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
    if not model: raise ValueError("BANKING_AGENT_LLM_MODEL_required_for_llm_assistance")
    return model


def middle_loop_enabled() -> bool:
    """Require an explicit opt-in before an LLM can affect routing or retrieval."""
    selected = os.environ.get("BANKING_AGENT_LLM_MIDDLE_LOOP", "off").strip().lower()
    if selected not in {"off", "enabled"}:
        raise ValueError("llm_middle_loop_must_be_off_or_enabled")
    return selected == "enabled"

def build_llm_understanding_from_environment() -> LLMUnderstanding | None:
    selected = os.environ.get("BANKING_AGENT_LLM_UNDERSTANDING", "off").strip().lower()
    if selected == "off": return None
    if selected != "llm": raise ValueError("llm_understanding_mode_must_be_off_or_llm")
    if not middle_loop_enabled():
        return None
    return LLMUnderstanding(create_llm_client(LLMSettings.from_environment()), model=_model())

def build_llm_text_assistant_from_environment() -> LLMTextAssistant | None:
    selected = os.environ.get("BANKING_AGENT_LLM_QUERY_REWRITE", "off").strip().lower()
    clarify = os.environ.get("BANKING_AGENT_LLM_CLARIFICATION", "off").strip().lower()
    if selected == clarify == "off": return None
    if selected not in {"off", "llm"} or clarify not in {"off", "llm"}: raise ValueError("llm_assistance_mode_must_be_off_or_llm")
    return LLMTextAssistant(create_llm_client(LLMSettings.from_environment()), model=_model())
