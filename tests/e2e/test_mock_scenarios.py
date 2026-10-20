"""Run documented core scenarios with real B/D and scripted A/C."""
import json
from pathlib import Path
import unittest
from banking_agent.schemas import AgentState
from banking_agent.app.orchestrator import Orchestrator
from helpers.hybrid_e2e_modules import real_recommendation, real_retrieval, scripted_a_and_c

SCENARIOS = json.loads((Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text())

class CoreScenarioTests(unittest.IsolatedAsyncioTestCase):
    async def test_core_scenarios(self):
        self.assertEqual([s["id"] for s in SCENARIOS], [f"S{i:02}" for i in range(1, 9)])
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario["id"]):
                modules = scripted_a_and_c(scenario["mock_outputs"])
                initial = AgentState(**scenario["input"], **scenario["initial_state"])
                original = initial.model_dump()
                response = await Orchestrator(
                    modules,
                    real_retrieval(modules.calls),
                    modules,
                    real_recommendation(
                        modules.calls,
                        {"session-s06": "session-001"},
                    ),
                ).handle(initial)
                expected = scenario["expected"]
                self.assertEqual(response.status, "ok")
                self.assertEqual(response.decision.action.value, expected["action"])
                self.assertEqual(response.decision.reason_code, expected["reason_code"])
                self.assertEqual(modules.calls, expected["modules_called"])
                self.assertEqual(response.state.complaint_status.value, expected["complaint_status"])
                self.assertEqual(response.state.handoff_status.value, expected["handoff_status"])
                if "B" in expected["modules_called"] and expected["action"] == "ANSWER":
                    self.assertEqual(response.citations, response.state.retrieved_docs)
                else:
                    self.assertEqual([d.document_id for d in response.citations], expected["citation_ids"])
                if "D" in expected["modules_called"]:
                    self.assertTrue(response.recommendations)
                else:
                    self.assertEqual(len(response.recommendations), expected["recommendation_count"])
                self.assertTrue(response.text)
                self.assertEqual(initial.model_dump(), original)
                if "B" in modules.calls:
                    self.assertEqual(modules.rule_inputs[1].retrieved_docs, response.state.retrieved_docs)
                for citation in response.citations:
                    self.assertIn(citation.excerpt, response.text)
                    self.assertIn(citation.document_id, response.text)
