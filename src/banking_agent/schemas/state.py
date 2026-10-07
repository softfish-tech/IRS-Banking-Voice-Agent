"""Framework-independent shared state for the banking-agent workflow."""

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    Action,
    ComplaintStatus,
    ConsentStatus,
    EligibilityStatus,
    RiskLevel,
)


class SchemaModel(BaseModel):
    """Base model that rejects fields outside the agreed contract."""

    model_config = ConfigDict(extra="forbid")


class Entity(SchemaModel):
    """Entity extracted from a user request."""

    type: str = Field(min_length=1)
    value: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class UnderstandingResult(SchemaModel):
    """Output owned by the Intent / Risk / Entity module."""

    intent: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    entities: list[Entity] = Field(default_factory=list)


class RetrievedDocument(SchemaModel):
    """Evidence returned by the RAG module."""

    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source: str = Field(min_length=1)
    score: float
    excerpt: str = Field(min_length=1)


class RuleStatePatch(SchemaModel):
    """Whitelisted business-state changes returned by the Rules module."""

    complaint_status: ComplaintStatus | None = None


class Decision(SchemaModel):
    """Deterministic business decision returned by the Rules module."""

    action: Action
    reason_code: str = Field(min_length=1)
    next_state: RuleStatePatch = Field(default_factory=RuleStatePatch)


class RecommendationItem(SchemaModel):
    """A ranked recommendation that E may render after Rules permission."""

    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    rank: int = Field(ge=1)
    reason: str = Field(min_length=1)


class AgentState(SchemaModel):
    """Canonical per-session state shared by the orchestration workflow.

    Modules return their structured results. The E-owned orchestrator performs
    controlled merges into this state and applies only valid rule-state patches.
    """

    session_id: str = Field(min_length=1)
    user_text: str = Field(min_length=1)

    understanding: UnderstandingResult = Field(default_factory=UnderstandingResult)

    complaint_status: ComplaintStatus = ComplaintStatus.NONE
    consent: ConsentStatus = ConsentStatus.UNKNOWN
    eligibility: EligibilityStatus = EligibilityStatus.UNKNOWN

    retrieved_docs: list[RetrievedDocument] = Field(default_factory=list)
    decision: Decision | None = None
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    final_response: str | None = None
