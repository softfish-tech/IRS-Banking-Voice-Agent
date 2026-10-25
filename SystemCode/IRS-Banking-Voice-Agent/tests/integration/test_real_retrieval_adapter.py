"""Exercise the real B mock corpus through E's async adapter and orchestrator."""

import json
from pathlib import Path
import unittest

from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.retrieval_adapter import AsyncRetrievalAdapter
from banking_agent.modules.rag.retriever import MockRetriever
from banking_agent.schemas import AgentState
from helpers.mock_modules import ScriptedModules


SCENARIOS = json.loads((Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text())


class RealRetrievalAdapterIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_grounded_answer_uses_real_b_evidence_through_async_bridge(self) -> None:
        scenario = SCENARIOS[0]
        acd = ScriptedModules(scenario["mock_outputs"])
        response = await Orchestrator(
            acd,
            AsyncRetrievalAdapter(MockRetriever()),
            acd,
            acd,
        ).handle(AgentState(**scenario["input"], **scenario["initial_state"]))

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.decision.action.value, "ANSWER")
        self.assertEqual(acd.calls, ["A", "C", "C"])
        self.assertEqual(
            [document.document_id for document in response.citations],
            ["NB-v1_1-lost_or_stolen_card-002"],
        )
        self.assertIn(response.citations[0].excerpt, response.text)

    async def test_real_b_empty_result_reaches_c_post_retrieval_abstention(self) -> None:
        scenario = SCENARIOS[7]
        acd = ScriptedModules(scenario["mock_outputs"])
        response = await Orchestrator(
            acd,
            AsyncRetrievalAdapter(MockRetriever()),
            acd,
            acd,
        ).handle(AgentState(**scenario["input"], **scenario["initial_state"]))

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.decision.action.value, "ABSTAIN")
        self.assertEqual(response.citations, [])
        self.assertEqual(acd.calls, ["A", "C", "C"])
