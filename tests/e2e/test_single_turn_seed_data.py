"""Exercise draft single-turn E2E seeds with real B/D and scripted A/C.

The fixture is deliberately marked ``draft_pending_c_approval``.  These tests
verify E's execution semantics and B/D integration; C remains the authority
for actions, reason codes, and business-state patches.
"""

import json
from pathlib import Path
import unittest

from banking_agent.app.api.dto import to_chat_turn_response_v1
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.schemas import AgentState
from helpers.hybrid_e2e_modules import real_recommendation, real_retrieval, scripted_a_and_c


FIXTURE_DIRECTORY = Path(__file__).parent / "single_turn"


def load_cases() -> list[dict]:
    cases = []
    for fixture_path in sorted(FIXTURE_DIRECTORY.glob("*.json")):
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        if fixture["schema_version"] != "v0":
            raise AssertionError(f"Unsupported fixture schema: {fixture_path}")
        if fixture["status"] != "draft_pending_c_approval":
            raise AssertionError(f"Unexpected fixture status: {fixture_path}")
        cases.extend(fixture["cases"])
    return cases


class SingleTurnSeedDataTests(unittest.IsolatedAsyncioTestCase):
    async def test_scripted_cases_exercise_the_declared_e_paths(self) -> None:
        cases = load_cases()
        self.assertEqual(len(cases), 42)
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))

        for case in cases:
            with self.subTest(case=case["case_id"]):
                modules = scripted_a_and_c(case["scripted_module_envelopes"])
                initial = AgentState(**case["input"], **case["initial_state"])
                original = initial.model_dump()
                response = await Orchestrator(
                    modules,
                    real_retrieval(modules.calls),
                    modules,
                    real_recommendation(modules.calls),
                ).handle(initial)
                expected = case["expected"]

                self.assertEqual(response.status, expected["status"])
                self.assertEqual(modules.calls, expected["module_call_order"])
                for module in expected["modules_not_called"]:
                    self.assertNotIn(module, modules.calls)
                self.assertEqual(initial.model_dump(), original)
                self.assertEqual(response.state.complaint_status.value, expected["state_after"]["complaint_status"])
                self.assertEqual(response.state.handoff_status.value, expected["state_after"]["handoff_status"])
                self.assertEqual(response.state.consent.value, expected["state_after"]["consent"])
                if "B" in expected["module_call_order"] and expected["action"] == "ANSWER":
                    # IDs and cardinality are owned by the real retriever, not
                    # by the former fixture mock.  An ANSWER may cite only the
                    # evidence that B actually returned.
                    self.assertEqual(response.citations, response.state.retrieved_docs)
                else:
                    self.assertEqual([item.document_id for item in response.citations], expected["citation_ids"])
                self.assertEqual(len(response.recommendations), expected["recommendation_count"])
                acceptance = case["acceptance"]
                understanding = acceptance["understanding"]
                if understanding.get("available", True):
                    self.assertEqual(response.state.understanding.intent, understanding["intent"])
                    self.assertEqual(response.state.understanding.risk_level.value, understanding["risk_level"])

                rag = acceptance["rag"]
                self.assertEqual("B" in modules.calls, rag["should_call"])
                if rag["should_call"] and expected["action"] == "ANSWER":
                    # The second C decision receives B's actual output.  A real
                    # retriever may return different IDs than the old mock.
                    self.assertEqual(
                        modules.rule_inputs[-1].retrieved_docs,
                        response.state.retrieved_docs,
                    )
                    if expected["action"] == "ANSWER":
                        self.assertTrue(response.citations)
                elif rag["should_call"]:
                    self.assertTrue(modules.rule_inputs[-1].retrieved_docs)
                    self.assertEqual(response.state.retrieved_docs, [])

                recommendation = acceptance["recommendation"]
                self.assertEqual("D" in modules.calls, recommendation["should_call"])
                if recommendation["should_call"]:
                    self.assertEqual(
                        bool(response.recommendations),
                        recommendation["expected_allowed"],
                    )

                if expected["status"] == "ok":
                    self.assertIsNotNone(response.decision)
                    self.assertEqual(response.decision.action.value, expected["action"])
                    self.assertEqual(response.decision.reason_code, expected["reason_code"])
                    self.assertTrue(response.text)
                    if "recommendation_product_ids" in expected:
                        self.assertEqual([item.product_id for item in response.recommendations], expected["recommendation_product_ids"])
                else:
                    self.assertIsNone(response.decision)
                    self.assertIsNotNone(response.error)
                    self.assertEqual(response.error.module, expected["technical_error"]["module"])
                    self.assertEqual(response.error.code, expected["technical_error"]["code"])

                response_assertions = acceptance["public_response"]
                public_response = to_chat_turn_response_v1(response)
                self.assertEqual(public_response.message.kind, response_assertions["kind"])
                self.assertEqual(public_response.status, expected["status"])
                self.assertEqual(len(public_response.citations), len(response.citations))
                self.assertEqual(
                    len(public_response.recommendations), expected["recommendation_count"]
                )
                if "B" in expected["module_call_order"]:
                    for document in response.citations:
                        self.assertIn(document.document_id, response.text)
                else:
                    for text in response_assertions["must_contain"]:
                        self.assertIn(text, response.text)
                for text in response_assertions["must_not_contain"]:
                    self.assertNotIn(text, response.text)


if __name__ == "__main__":
    unittest.main()
