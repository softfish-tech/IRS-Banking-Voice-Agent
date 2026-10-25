"""Current-main E orchestration with the actual C adapter."""

import json
import unittest
from pathlib import Path

from banking_agent.app.orchestrator import Orchestrator
from banking_agent.modules.rules import RuleEngine
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture
from banking_agent.modules.rag import MockRetriever
from banking_agent.schemas import AgentState


FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text()
)


class ScriptedModules:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []
        self.rules = RuleEngine()

    async def analyze(self, session_id, user_text):
        self.calls.append("A")
        return self.outputs["A"]

    async def retrieve(self, query, top_k):
        self.calls.append("B")
        return self.outputs["B"]

    async def decide(self, state):
        self.calls.append("C")
        return await self.rules.decide(state)

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.calls.append("D")
        return self.outputs["D"]


class CWithEOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_s01_to_s08_with_real_c_adapter(self):
        for fixture in FIXTURES:
            with self.subTest(scenario=fixture["id"]):
                modules = ScriptedModules(fixture["mock_outputs"])
                state = AgentState(
                    **fixture["input"], **fixture["initial_state"]
                )
                result = await Orchestrator(
                    modules, modules, modules, modules
                ).handle(state)
                expected = fixture["expected"]
                self.assertEqual(result.status, "ok")
                self.assertEqual(result.decision.action, expected["action"])
                self.assertEqual(result.decision.reason_code, expected["reason_code"])
                self.assertEqual(modules.calls, expected["modules_called"])
                self.assertEqual(result.state.complaint_status, expected["complaint_status"])
                self.assertEqual(result.state.handoff_status, expected["handoff_status"])
                self.assertEqual(
                    [doc.document_id for doc in result.citations],
                    expected["citation_ids"],
                )
                self.assertEqual(
                    len(result.recommendations), expected["recommendation_count"]
                )

    async def test_irrelevant_candidates_do_not_become_a_policy_answer(self):
        fixture = next(item for item in FIXTURES if item["id"] == "S08")
        outputs = dict(fixture["mock_outputs"])
        outputs["B"] = {
            "status": "ok", "data": {"docs": [{
                "document_id": "irrelevant-card-fee",
                "title": "Card Fees Policy", "source": "Synthetic Bank Policy",
                "score": 100.0,
                "excerpt": "The replacement card fee is SGD 10.",
            }]},
        }
        modules = ScriptedModules(outputs)
        state = AgentState(**fixture["input"], **fixture["initial_state"])
        result = await Orchestrator(modules, modules, modules, modules).handle(state)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.decision.action, "ABSTAIN")
        self.assertEqual(result.citations, [])

    async def test_shipping_price_is_not_rendered_as_replacement_fee(self):
        for joiner in (",", " and"):
            with self.subTest(joiner=joiner):
                excerpt = (
                    "The replacement card fee is pending"
                    f"{joiner} express shipping costs SGD 10."
                )
                modules = ScriptedModules({
                    "A": {"status": "ok", "data": {
                        "intent": "card_fee_enquiry", "confidence": 0.94,
                        "risk_level": "LOW", "entities": [],
                    }},
                    "B": {"status": "ok", "data": {"docs": [{
                        "document_id": "shipping-only",
                        "title": "Card replacement fee",
                        "source": "Synthetic policy", "score": 100.0,
                        "excerpt": excerpt,
                    }]}},
                })
                state = AgentState(
                    session_id="shipping-price", user_text="What is the replacement fee for my card?"
                )
                result = await Orchestrator(modules, modules, modules, modules).handle(state)
                self.assertEqual(result.status, "ok")
                self.assertEqual(result.decision.action, "ABSTAIN")
                self.assertEqual(result.citations, [])
                self.assertNotIn("SGD 10", result.text)
                self.assertEqual(modules.calls, ["A", "C", "B", "C"])

    async def test_consent_denial_never_calls_d(self):
        fixture = next(item for item in FIXTURES if item["id"] == "S06")
        modules = ScriptedModules(fixture["mock_outputs"])
        state = AgentState(
            **fixture["input"], complaint_status="RESOLVED",
            handoff_status="NOT_REQUIRED", consent="DENIED",
        )
        result = await Orchestrator(modules, modules, modules, modules).handle(state)
        self.assertEqual(result.decision.action, "BLOCK")
        self.assertEqual(result.decision.reason_code, "CONSENT_REQUIRED")
        self.assertEqual(modules.calls, ["A", "C"])

    async def test_generic_fee_clarifies_and_lost_card_fee_escalates(self):
        corpus = (
            Path(__file__).resolve().parents[2]
            / "src/banking_agent/modules/rag/chunks/NovaBank_knowledge_chunks_v1_1.jsonl"
        )

        class BAdapter:
            def __init__(self):
                self.backend = MockRetriever(corpus)

            async def retrieve(self, query, top_k):
                return self.backend.retrieve(query, top_k)

        for question, expected in (
            ("What is the replacement fee for my card?", "CLARIFY"),
            ("How much does replacing a lost card cost?", "ESCALATE"),
        ):
            with self.subTest(question=question):
                modules = ScriptedModules({
                    "A": {"status": "ok", "data": {
                        "intent": "card_fee_enquiry", "confidence": 0.94,
                        "risk_level": "LOW", "entities": [],
                    }}
                })
                state = AgentState(session_id="synthetic-fee", user_text=question)
                result = await Orchestrator(
                    modules, BAdapter(), modules, modules
                ).handle(state)
                self.assertEqual(result.status, "ok")
                self.assertEqual(result.decision.action, expected)
                self.assertEqual(len(result.citations), int(expected == "ANSWER"))
                self.assertEqual(
                    len(result.state.retrieved_docs), int(expected == "ANSWER")
                )

    async def test_c_permission_and_real_d_synthetic_ranking(self):
        fixture = next(item for item in FIXTURES if item["id"] == "S06")
        modules = ScriptedModules(fixture["mock_outputs"])
        catalog = load_fixture(
            Path(__file__).parents[2] / "data/fixtures/recommendation.json"
        )
        profiles = dict(catalog.customer_profiles)
        profiles["session-s06"] = profiles["session-001"]
        recommendation = RecommendationAdapter({
            "customer_profiles": profiles, "products": catalog.products,
        })
        state = AgentState(**fixture["input"], **fixture["initial_state"])
        result = await Orchestrator(
            modules, modules, modules, recommendation
        ).handle(state)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.decision.action, "RECOMMEND")
        self.assertEqual([item.rank for item in result.recommendations], [1, 2, 3])
        self.assertEqual(modules.calls, ["A", "C"])

    async def test_real_d_cannot_be_called_after_c_blocks_open_case(self):
        fixture = next(item for item in FIXTURES if item["id"] == "S05")
        modules = ScriptedModules(fixture["mock_outputs"])
        catalog = load_fixture(
            Path(__file__).parents[2] / "data/fixtures/recommendation.json"
        )
        recommendation = RecommendationAdapter(catalog)
        state = AgentState(**fixture["input"], **fixture["initial_state"])
        result = await Orchestrator(
            modules, modules, modules, recommendation
        ).handle(state)
        self.assertEqual(result.decision.action, "BLOCK")
        self.assertEqual(result.recommendations, [])
        self.assertEqual(modules.calls, ["A", "C"])


if __name__ == "__main__":
    unittest.main()
