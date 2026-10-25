"""Run the reusable A/B/C/D contract harness against deterministic fixtures."""

import json
from pathlib import Path
import unittest

from banking_agent.schemas import AgentState
from helpers.adapter_contracts import (
    assert_intent_adapter_contract,
    assert_recommendation_adapter_contract,
    assert_retrieval_adapter_contract,
    assert_rules_adapter_contract,
    validate_recommendation_result,
    validate_retrieval_result,
    validate_rules_result,
)
from banking_agent.app.demo import ScenarioModules

SCENARIOS = json.loads((Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text())


class AdapterContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_fixture_adapters_satisfy_public_contracts(self) -> None:
        policy = SCENARIOS[0]
        recommendation = SCENARIOS[5]

        intent_modules = ScenarioModules(policy["mock_outputs"])
        intent = await assert_intent_adapter_contract(intent_modules, "session", policy["input"]["user_text"])
        self.assertEqual(intent.status, "ok")

        retrieval_modules = ScenarioModules(policy["mock_outputs"])
        retrieval = await assert_retrieval_adapter_contract(retrieval_modules, policy["input"]["user_text"])
        self.assertEqual(retrieval.data.docs[0].document_id, "policy-card-fees-v1")

        rules_modules = ScenarioModules(policy["mock_outputs"])
        state = AgentState(**policy["input"], **policy["initial_state"])
        rules = await assert_rules_adapter_contract(rules_modules, state)
        self.assertEqual(rules.data.action.value, "ANSWER")

        recommendation_modules = ScenarioModules(recommendation["mock_outputs"])
        products = await assert_recommendation_adapter_contract(
            recommendation_modules, "session", "RESOLVED", "NOT_REQUIRED", "GRANTED"
        )
        self.assertTrue(products.data.allowed)

    def test_contract_harness_rejects_forbidden_empty_and_denial_shapes(self) -> None:
        with self.assertRaisesRegex(AssertionError, "C has no normal empty"):
            validate_rules_result({"status": "empty", "data": {"action": "CLARIFY", "reason_code": "TEST"}})
        with self.assertRaisesRegex(AssertionError, "B empty result"):
            validate_retrieval_result({"status": "empty", "data": {"docs": [{"document_id": "doc", "title": "Title", "source": "Source", "score": .9, "excerpt": "Excerpt"}]}})
        with self.assertRaisesRegex(AssertionError, "must not return items"):
            validate_recommendation_result({"status": "ok", "data": {"allowed": False, "reason_code": "BLOCKED", "items": [{"product_id": "product", "name": "Name", "rank": 1, "reason": "Reason"}]}})
