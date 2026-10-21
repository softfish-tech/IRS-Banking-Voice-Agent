"""Run S01--S08 with real A, B, and D implementations.

C remains scenario-scripted until its branch is integrated.  This isolates the
real Part A adapter in the existing end-to-end composition without changing
the accepted fixture decisions that C owns.
"""

import json
from pathlib import Path
import unittest

from banking_agent.app.orchestrator import Orchestrator
from banking_agent.modules.intent import IntentModuleAdapter
from banking_agent.schemas import AgentState
from helpers.hybrid_e2e_modules import real_recommendation, real_retrieval, scripted_a_and_c


SCENARIOS = json.loads(
    (Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text(encoding="utf-8")
)


class RecordingIntentAdapter:
    """Make the real A adapter visible in the existing shared call trace."""

    def __init__(self, calls: list[str]) -> None:
        self._adapter = IntentModuleAdapter()
        self._calls = calls

    async def analyze(self, session_id: str, user_text: str) -> dict[str, object]:
        self._calls.append("A")
        return await self._adapter.analyze(session_id, user_text)


class RealIntentScenarioE2ETests(unittest.IsolatedAsyncioTestCase):
    async def test_core_scenarios_with_real_intent_adapter(self) -> None:
        self.assertEqual([scenario["id"] for scenario in SCENARIOS], [f"S{i:02}" for i in range(1, 9)])

        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario["id"]):
                scripted_c = scripted_a_and_c(scenario["mock_outputs"])
                initial = AgentState(**scenario["input"], **scenario["initial_state"])
                original = initial.model_dump()
                response = await Orchestrator(
                    RecordingIntentAdapter(scripted_c.calls),
                    real_retrieval(scripted_c.calls),
                    scripted_c,
                    real_recommendation(scripted_c.calls, {"session-s06": "session-001"}),
                ).handle(initial)

                expected = scenario["expected"]
                expected_understanding = scenario["mock_outputs"]["A"]["data"]
                self.assertEqual(response.status, "ok")
                self.assertEqual(scripted_c.calls, expected["modules_called"])
                self.assertEqual(response.decision.action.value, expected["action"])
                self.assertEqual(response.decision.reason_code, expected["reason_code"])
                self.assertEqual(response.state.understanding.intent, expected_understanding["intent"])
                self.assertEqual(response.state.understanding.confidence, expected_understanding["confidence"])
                self.assertEqual(
                    response.state.understanding.risk_level.value,
                    expected_understanding["risk_level"],
                )
                self.assertEqual(response.state.complaint_status.value, expected["complaint_status"])
                self.assertEqual(response.state.handoff_status.value, expected["handoff_status"])
                self.assertEqual(initial.model_dump(), original)

                if "B" in scripted_c.calls:
                    self.assertEqual(scripted_c.rule_inputs[-1].retrieved_docs, response.state.retrieved_docs)
                if expected["action"] == "ANSWER":
                    self.assertEqual(response.citations, response.state.retrieved_docs)
                    self.assertTrue(response.citations)
                else:
                    self.assertEqual(response.citations, [])
                if expected["action"] == "RECOMMEND":
                    self.assertTrue(response.recommendations)
                else:
                    self.assertEqual(response.recommendations, [])


if __name__ == "__main__":
    unittest.main()
