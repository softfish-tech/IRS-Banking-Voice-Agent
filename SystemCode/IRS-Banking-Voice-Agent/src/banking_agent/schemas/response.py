"""Application responses distinguish technical failures from business actions."""
from typing import Literal
from pydantic import Field
from .state import SchemaModel, AgentState, Decision, RetrievedDocument, RecommendationItem

class TechnicalError(SchemaModel):
    module: Literal["A", "B", "C", "D"]
    code: Literal["timeout", "invalid_result", "module_error", "exception"]

class AgentResponse(SchemaModel):
    request_id: str
    session_id: str
    status: Literal["ok", "error"]
    decision: Decision | None = None
    text: str
    citations: list[RetrievedDocument] = Field(default_factory=list)
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    error: TechnicalError | None = None
    state: AgentState
