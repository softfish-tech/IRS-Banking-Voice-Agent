"""Sanitized E-owned decision traces for diagnostics and evaluation."""

from dataclasses import dataclass, field
from hashlib import sha256
from time import time
from typing import Literal, Protocol
from uuid import uuid4

from banking_agent.schemas import AgentState


@dataclass(frozen=True)
class TraceContext:
    """Application metadata that is safe to associate with an agent turn."""

    mode: str = "unknown"
    scenario_id: str | None = None
    conversation_id: str | None = None
    user_id: int | None = None


@dataclass(frozen=True)
class ModuleOutcome:
    module: Literal["A", "B", "C", "D"]
    status: Literal["ok", "empty", "error"]
    duration_ms: int
    error_code: str | None = None


@dataclass(frozen=True)
class DecisionTrace:
    """A privacy-minimised account of one orchestrated request.

    It intentionally excludes raw user text, assistant text, credentials,
    cookies, full evidence excerpts, and exception details.
    """

    trace_id: str
    request_id: str
    session_id: str
    created_at: int
    context: TraceContext
    user_text_hash: str
    modules: tuple[ModuleOutcome, ...]
    intent: str | None
    intent_confidence: float | None
    risk_level: str
    complaint_status_before: str
    complaint_status_after: str
    handoff_status_before: str
    handoff_status_after: str
    action: str | None
    reason_code: str | None
    retrieved_document_ids: tuple[str, ...]
    recommendation_count: int
    state_patch: dict[str, str]
    result_status: Literal["ok", "error"]
    technical_error_module: str | None
    technical_error_code: str | None
    duration_ms: int

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        initial_state: AgentState,
        final_state: AgentState,
        context: TraceContext,
        modules: list[ModuleOutcome],
        result_status: Literal["ok", "error"],
        technical_error_module: str | None,
        technical_error_code: str | None,
        duration_ms: int,
    ) -> "DecisionTrace":
        decision = final_state.decision
        patch = decision.next_state.model_dump(exclude_none=True) if decision else {}
        return cls(
            trace_id=str(uuid4()),
            request_id=request_id,
            session_id=final_state.session_id,
            created_at=int(time()),
            context=context,
            user_text_hash=sha256(final_state.user_text.encode("utf-8")).hexdigest(),
            modules=tuple(modules),
            intent=final_state.understanding.intent,
            intent_confidence=final_state.understanding.confidence,
            risk_level=final_state.understanding.risk_level.value,
            complaint_status_before=initial_state.complaint_status.value,
            complaint_status_after=final_state.complaint_status.value,
            handoff_status_before=initial_state.handoff_status.value,
            handoff_status_after=final_state.handoff_status.value,
            action=decision.action.value if decision else None,
            reason_code=decision.reason_code if decision else None,
            retrieved_document_ids=tuple(document.document_id for document in final_state.retrieved_docs),
            recommendation_count=len(final_state.recommendations),
            state_patch={key: value.value for key, value in patch.items()},
            result_status=result_status,
            technical_error_module=technical_error_module,
            technical_error_code=technical_error_code,
            duration_ms=duration_ms,
        )


class TraceSink(Protocol):
    def record_trace(self, trace: DecisionTrace) -> None: ...
