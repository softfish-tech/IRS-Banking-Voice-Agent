"""Verify that Part A's real adapter is safely wired into E's orchestrator.

Rules, retrieval, and recommendations stay scripted here on purpose: these
tests isolate the A -> E boundary before C's implementation is integrated.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from banking_agent.app.observability import DecisionTrace
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.modules.intent import IntentModuleAdapter
from banking_agent.schemas import AgentState


SCENARIOS = {
    scenario["id"]: scenario
    for scenario in json.loads(
        (Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text(encoding="utf-8")
    )
}


class TraceRecorder:
    def __init__(self) -> None:
        self.traces: list[DecisionTrace] = []

    def record_trace(self, trace: DecisionTrace) -> None:
        self.traces.append(trace)


class RecordingIntentAdapter:
    def __init__(self, calls: list[str]) -> None:
        self._adapter = IntentModuleAdapter()
        self._calls = calls

    async def analyze(self, session_id: str, user_text: str) -> dict[str, object]:
        self._calls.append("A")
        return await self._adapter.analyze(session_id, user_text)


class ScriptedDownstreamModules:
    """B/C/D test doubles that share a call log with the real A adapter."""

    def __init__(self, outputs: dict[str, object], calls: list[str]) -> None:
        self._outputs = deepcopy(outputs)
        self._calls = calls
        self.rule_inputs: list[AgentState] = []
        self._rule_index = 0

    async def retrieve(self, query: str, top_k: int) -> dict[str, object]:
        self._calls.append("B")
        return deepcopy(self._outputs["B"])

    async def decide(self, state: AgentState) -> dict[str, object]:
        self._calls.append("C")
        self.rule_inputs.append(state.model_copy(deep=True))
        result = self._outputs["C"][self._rule_index]
        self._rule_index += 1
        return deepcopy(result)

    async def recommend(
        self, session_id: str, complaint_status: str, handoff_status: str, consent: str
    ) -> dict[str, object]:
        self._calls.append("D")
        return deepcopy(self._outputs["D"])


class RealIntentOrchestratorIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_intent_output_drives_declared_orchestrator_paths(self) -> None:
        for scenario_id in ("S01", "S03", "S04", "S07"):
            with self.subTest(scenario=scenario_id):
                scenario = SCENARIOS[scenario_id]
                calls: list[str] = []
                downstream = ScriptedDownstreamModules(scenario["mock_outputs"], calls)
                trace_recorder = TraceRecorder()
                state = AgentState(**scenario["input"], **scenario["initial_state"])

                response = await Orchestrator(
                    RecordingIntentAdapter(calls),
                    downstream,
                    downstream,
                    downstream,
                    trace_sink=trace_recorder,
                ).handle(state)

                expected = scenario["expected"]
                expected_understanding = scenario["mock_outputs"]["A"]["data"]
                self.assertEqual(response.status, "ok")
                self.assertEqual(calls, expected["modules_called"])
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
                self.assertEqual(len(trace_recorder.traces), 1)
                trace = trace_recorder.traces[0]
                self.assertEqual([outcome.module for outcome in trace.modules], calls)
                self.assertEqual(trace.intent, expected_understanding["intent"])
                self.assertEqual(trace.risk_level, expected_understanding["risk_level"])

                for rule_input in downstream.rule_inputs:
                    self.assertEqual(rule_input.understanding, response.state.understanding)
                if scenario_id == "S01":
                    self.assertEqual(len(downstream.rule_inputs), 2)
                    self.assertTrue(response.citations)
                else:
                    self.assertEqual(response.citations, [])
                    self.assertNotIn("B", calls)
                    self.assertNotIn("D", calls)

    async def test_real_intent_technical_error_stops_before_downstream_modules(self) -> None:
        calls: list[str] = []
        downstream = ScriptedDownstreamModules(SCENARIOS["S01"]["mock_outputs"], calls)
        trace_recorder = TraceRecorder()

        response = await Orchestrator(
            RecordingIntentAdapter(calls),
            downstream,
            downstream,
            downstream,
            trace_sink=trace_recorder,
        ).handle(AgentState(session_id="blank-text", user_text="   "))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.error.module, "A")
        self.assertEqual(response.error.code, "module_error")
        self.assertEqual(calls, ["A"])
        self.assertIsNone(response.decision)
        self.assertEqual(response.citations, [])
        self.assertEqual(response.recommendations, [])
        self.assertEqual(len(trace_recorder.traces), 1)
        trace = trace_recorder.traces[0]
        self.assertEqual([(outcome.module, outcome.status) for outcome in trace.modules], [("A", "error")])
        self.assertEqual(trace.technical_error_module, "A")
        self.assertEqual(trace.technical_error_code, "module_error")


if __name__ == "__main__":
    unittest.main()
