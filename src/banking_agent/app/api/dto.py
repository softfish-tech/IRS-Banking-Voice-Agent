"""Versioned public API models, deliberately separate from internal state."""

from typing import Any, Literal

from pydantic import Field

from banking_agent.schemas import Action, TranscriptionResult, TranscriptionStatus
from banking_agent.schemas.response import AgentResponse
from banking_agent.schemas.state import SchemaModel

PUBLIC_API_VERSION = "v1"


class PublicMessage(SchemaModel):
    kind: Literal[
        "answer",
        "complaint",
        "escalation",
        "clarification",
        "blocked",
        "abstention",
        "recommendation",
        "technical_error",
    ]
    text: str = Field(min_length=1)


class PublicDecision(SchemaModel):
    """A user-visible action without internal rule reason codes or state patches."""

    action: Action


class PublicCitation(SchemaModel):
    title: str = Field(min_length=1)
    source: str = Field(min_length=1)
    excerpt: str = Field(min_length=1, max_length=2_000)


class PublicRecommendation(SchemaModel):
    name: str = Field(min_length=1)
    rank: int = Field(ge=1)
    reason: str = Field(min_length=1)


class PublicError(SchemaModel):
    """Stable, non-diagnostic error information intended for a client."""

    code: Literal["agent_unavailable"]


class ChatTurnResponseV1(SchemaModel):
    api_version: Literal["v1"] = PUBLIC_API_VERSION
    request_id: str = Field(min_length=1)
    status: Literal["ok", "error"]
    message: PublicMessage
    decision: PublicDecision | None = None
    citations: list[PublicCitation] = Field(default_factory=list)
    recommendations: list[PublicRecommendation] = Field(default_factory=list)
    error: PublicError | None = None


class TranscriptionResponseV1(SchemaModel):
    """Public, non-persistent result of one local ASR attempt."""

    api_version: Literal["v1"] = PUBLIC_API_VERSION
    status: TranscriptionStatus
    text: str | None = None
    language: str | None = None
    duration_seconds: float | None = None
    error_code: str | None = None


def to_transcription_response_v1(result: TranscriptionResult) -> TranscriptionResponseV1:
    """Hide backend/model details and ASR diagnostics from the browser API."""

    return TranscriptionResponseV1(
        status=result.status,
        text=result.text,
        language=result.language,
        duration_seconds=result.duration_seconds,
        error_code=result.error_code,
    )


MESSAGE_KIND_BY_ACTION: dict[Action, str] = {
    Action.ANSWER: "answer",
    Action.HANDLE_COMPLAINT: "complaint",
    Action.ESCALATE: "escalation",
    Action.CLARIFY: "clarification",
    Action.BLOCK: "blocked",
    Action.ABSTAIN: "abstention",
    Action.RECOMMEND: "recommendation",
}


def to_chat_turn_response_v1(response: AgentResponse) -> ChatTurnResponseV1:
    """Convert an internal response without leaking state or technical details."""

    if response.status == "error":
        return ChatTurnResponseV1(
            request_id=response.request_id,
            status="error",
            message=PublicMessage(kind="technical_error", text=response.text),
            error=PublicError(code="agent_unavailable"),
        )

    if response.decision is None:
        raise ValueError("successful responses require a business decision")
    action = response.decision.action
    return ChatTurnResponseV1(
        request_id=response.request_id,
        status="ok",
        message=PublicMessage(kind=MESSAGE_KIND_BY_ACTION[action], text=response.text),
        decision=PublicDecision(action=action),
        citations=[
            PublicCitation(title=item.title, source=item.source, excerpt=item.excerpt)
            for item in response.citations
        ],
        recommendations=[
            PublicRecommendation(name=item.name, rank=item.rank, reason=item.reason)
            for item in response.recommendations
        ],
    )


class DeveloperModuleOutcomeV1(SchemaModel):
    module: str
    status: Literal["ok", "empty", "error", "fallback"]
    duration_ms: int = Field(ge=0)
    error_code: str | None = None
    attempts: int | None = Field(default=None, ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class DeveloperTraceV1(SchemaModel):
    """Restricted development-only trace view; it has no user or message text."""

    trace_id: str
    request_id: str
    created_at: int
    mode: str
    scenario_id: str | None = None
    modules: list[DeveloperModuleOutcomeV1]
    intent: str | None = None
    intent_confidence: float | None = None
    risk_level: str
    complaint_status_before: str
    complaint_status_after: str
    handoff_status_before: str
    handoff_status_after: str
    action: str | None = None
    reason_code: str | None = None
    retrieved_document_ids: list[str]
    recommendation_count: int = Field(ge=0)
    state_patch: dict[str, str]
    result_status: Literal["ok", "error"]
    technical_error_module: str | None = None
    technical_error_code: str | None = None
    duration_ms: int = Field(ge=0)


def to_developer_trace_v1(trace: dict[str, Any]) -> DeveloperTraceV1:
    """Validate the deliberately restricted database projection for the dashboard."""

    return DeveloperTraceV1.model_validate(trace)
