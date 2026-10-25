"""Validated envelopes shared by mock and real module adapters."""
from typing import Generic, Literal, TypeVar
from pydantic import Field, model_validator
from .state import SchemaModel, UnderstandingResult, Decision, RetrievedDocument, RecommendationItem

T = TypeVar("T")

class ModuleResult(SchemaModel, Generic[T]):
    status: Literal["ok", "empty", "error"]
    data: T | None = None

    @model_validator(mode="after")
    def require_data(self):
        if self.status != "error" and self.data is None:
            raise ValueError("Non-error results require data")
        return self

class RetrievalData(SchemaModel):
    docs: list[RetrievedDocument] = Field(default_factory=list)

class RecommendationData(SchemaModel):
    allowed: bool
    reason_code: str = Field(min_length=1)
    items: list[RecommendationItem] = Field(default_factory=list)

IntentResult = ModuleResult[UnderstandingResult]
RetrievalResult = ModuleResult[RetrievalData]
RulesResult = ModuleResult[Decision]
RecommendationResult = ModuleResult[RecommendationData]
