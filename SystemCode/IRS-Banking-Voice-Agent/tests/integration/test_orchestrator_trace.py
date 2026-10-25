"""Decision traces capture safe orchestration facts for success and failures."""

import json
from pathlib import Path
import unittest

from banking_agent.app.observability import TraceContext
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.schemas import AgentState
from helpers.mock_modules import ScriptedModules

SCENARIOS = json.loads((Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text())


class CapturingTraceSink:
    def __init__(self) -> None:
        self.traces = []

    def record_trace(self, trace) -> None:
        self.traces.append(trace)


class OrchestratorTraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_grounded_answer_trace_is_sanitized_and_complete(self) -> None:
        scenario = SCENARIOS[0]
        modules, sink = ScriptedModules(scenario["mock_outputs"]), CapturingTraceSink()
        response = await Orchestrator(
            modules, modules, modules, modules,
            trace_sink=sink,
            trace_context=TraceContext(mode="fixture", scenario_id="S01", conversation_id="conversation-1", user_id=7),
        ).handle(AgentState(**scenario["input"], **scenario["initial_state"]), request_id="request-1")

        trace = sink.traces[0]
        self.assertEqual(response.status, "ok")
        self.assertEqual(trace.request_id, "request-1")
        self.assertEqual(trace.context.scenario_id, "S01")
        self.assertEqual([(event.module, event.status) for event in trace.modules], [("A", "ok"), ("C", "ok"), ("B", "ok"), ("C", "ok")])
        self.assertEqual(trace.action, "ANSWER")
        self.assertEqual(trace.reason_code, "POLICY_EVIDENCE_FOUND")
        self.assertEqual(trace.retrieved_document_ids, ("policy-card-fees-v1",))
        self.assertNotIn(scenario["input"]["user_text"], repr(trace))

    async def test_module_failure_is_traced_without_exception_detail(self) -> None:
        scenario = SCENARIOS[0]
        modules, sink = ScriptedModules(scenario["mock_outputs"]), CapturingTraceSink()
        modules.outputs["B"] = {"status": "error"}
        response = await Orchestrator(modules, modules, modules, modules, trace_sink=sink).handle(
            AgentState(**scenario["input"], **scenario["initial_state"])
        )

        trace = sink.traces[0]
        self.assertEqual(response.status, "error")
        self.assertEqual(trace.result_status, "error")
        self.assertEqual((trace.technical_error_module, trace.technical_error_code), ("B", "module_error"))
        self.assertEqual([(event.module, event.status) for event in trace.modules], [("A", "ok"), ("C", "ok"), ("B", "error")])
