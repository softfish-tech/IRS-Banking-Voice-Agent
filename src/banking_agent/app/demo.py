"""Scenario-backed adapters for the local text-mock demonstration only.

These adapters deliberately select pre-scripted outputs from the approved
S01--S08 synthetic fixtures.  They are not implementations of A, B, C, or D
and must be replaced at the public interfaces when those modules arrive.
"""

from copy import deepcopy
from typing import Any

from banking_agent.schemas import AgentState


class ScenarioModules:
    """Expose one documented scenario as the four orchestrator adapters."""

    def __init__(self, outputs: dict[str, Any]) -> None:
        self._outputs = deepcopy(outputs)
        self._rule_index = 0

    async def analyze(self, session_id: str, user_text: str) -> dict[str, Any]:
        return deepcopy(self._outputs["A"])

    async def retrieve(self, query: str, top_k: int) -> dict[str, Any]:
        return deepcopy(self._outputs["B"])

    async def decide(self, state: AgentState) -> dict[str, Any]:
        result = self._outputs["C"][self._rule_index]
        self._rule_index += 1
        return deepcopy(result)

    async def recommend(
        self,
        session_id: str,
        complaint_status: str,
        handoff_status: str,
        consent: str,
    ) -> dict[str, Any]:
        return deepcopy(self._outputs["D"])
