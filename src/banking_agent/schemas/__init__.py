"""Shared state and module-interface contracts."""

from .enums import (
    Action,
    ComplaintStatus,
    ConsentStatus,
    HandoffStatus,
    RiskLevel,
)
from .state import (
    AgentState,
    Decision,
    Entity,
    RecommendationItem,
    RetrievedDocument,
    RuleStatePatch,
    UnderstandingResult,
)

__all__ = [
    "Action",
    "AgentState",
    "ComplaintStatus",
    "ConsentStatus",
    "Decision",
    "Entity",
    "HandoffStatus",
    "RecommendationItem",
    "RetrievedDocument",
    "RiskLevel",
    "RuleStatePatch",
    "UnderstandingResult",
]

from .module_results import (
    IntentResult, ModuleResult, RecommendationData, RecommendationResult,
    RetrievalData, RetrievalResult, RulesResult,
)
from .response import AgentResponse, TechnicalError

__all__ += [
    'IntentResult', 'ModuleResult', 'RecommendationData', 'RecommendationResult',
    'RetrievalData', 'RetrievalResult', 'RulesResult', 'AgentResponse', 'TechnicalError',
]
