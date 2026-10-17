"""Run documented core scenarios through the real E-owned orchestration."""
import json
from pathlib import Path
import unittest
from helpers.mock_modules import ScriptedModules
from banking_agent.schemas import AgentState
from banking_agent.app.orchestrator import Orchestrator

SCENARIOS = json.loads((Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text())

class MockScenarioTests(unittest.IsolatedAsyncioTestCase):
    async def test_core_scenarios(self):
        self.assertEqual([s["id"] for s in SCENARIOS], [f"S{i:02}" for i in range(1, 9)])
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario["id"]):
                modules = ScriptedModules(scenario["mock_outputs"])
                initial = AgentState(**scenario["input"], **scenario["initial_state"])
                original = initial.model_dump()
                response = await Orchestrator(modules, modules, modules, modules).handle(initial)
                expected = scenario["expected"]
                self.assertEqual(response.status, "ok")
                self.assertEqual(response.decision.action.value, expected["action"])
                self.assertEqual(response.decision.reason_code, expected["reason_code"])
                self.assertEqual(modules.calls, expected["modules_called"])
                self.assertEqual(response.state.complaint_status.value, expected["complaint_status"])
                self.assertEqual(response.state.handoff_status.value, expected["handoff_status"])
                self.assertEqual([d.document_id for d in response.citations], expected["citation_ids"])
                self.assertEqual(len(response.recommendations), expected["recommendation_count"])
                self.assertTrue(response.text)
                self.assertEqual(initial.model_dump(), original)
                if "B" in modules.calls:
                    self.assertEqual(modules.rule_inputs[1].retrieved_docs, response.state.retrieved_docs)
                for citation in response.citations:
                    self.assertIn(citation.excerpt, response.text)
                    self.assertIn(citation.document_id, response.text)
