"""Run real D against E's public harness and orchestrator with scripted A/B/C.

Requires the integration-e implementation to be present; missing E is an error,
not a skipped test. No production models, external service or API server is used.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
sys.dont_write_bytecode = True

try:
    from banking_agent.app.orchestrator import Orchestrator
    from banking_agent.schemas import AgentState
    from helpers.adapter_contracts import assert_recommendation_adapter_contract
    from helpers.mock_modules import ScriptedModules
except ModuleNotFoundError as error:
    raise SystemExit(
        "E integration files are required. Merge/review E first, then rerun this check."
    ) from error

from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture


class RecordingD:
    def __init__(self, adapter, calls):
        self.adapter, self.calls = adapter, calls

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.calls.append("D")
        return await self.adapter.recommend(session_id, complaint_status, handoff_status, consent)


class RealDIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture = load_fixture(ROOT / "data/fixtures/recommendation.json")
        self.cases = json.loads(
            (ROOT / "tests/fixtures/scenarios/core.json").read_text(encoding="utf-8")
        )
        self.s06 = deepcopy(next(c for c in self.cases if c["id"] == "S06"))
        # Explicit test-only association; unknown runtime sessions still fail closed.
        self.fixture.customer_profiles["session-s06"] = self.fixture.customer_profiles["session-001"]
        self.adapter = RecommendationAdapter(self.fixture)

    async def run_case(self, case):
        mocks = ScriptedModules(case["mock_outputs"])
        state = AgentState(**case["input"], **case["initial_state"])
        before = state.model_dump(mode="json")
        response = await Orchestrator(
            mocks, mocks, mocks, RecordingD(self.adapter, mocks.calls)
        ).handle(state)
        self.assertEqual(state.model_dump(mode="json"), before)
        return response, mocks.calls

    async def test_e_harness_accepts_success_denial_and_technical_error(self):
        for session, complaint, handoff, consent, status, allowed in [
            ("session-001", "RESOLVED", "NOT_REQUIRED", "GRANTED", "ok", True),
            ("session-002", "RESOLVED", "NOT_REQUIRED", "GRANTED", "ok", False),
            ("session-001", "OPEN", "NOT_REQUIRED", "GRANTED", "ok", False),
            ("session-001", "RESOLVED", "NOT_REQUIRED", "DENIED", "ok", False),
            ("unknown", "RESOLVED", "NOT_REQUIRED", "GRANTED", "error", None),
            ("session-001", "RESOLVED", "ESCALATED", "GRANTED", "error", None),
        ]:
            with self.subTest(session=session, complaint=complaint, handoff=handoff):
                result = await assert_recommendation_adapter_contract(
                    self.adapter, session, complaint, handoff, consent
                )
                self.assertEqual(result.status, status)
                if status == "ok":
                    self.assertEqual(result.data.allowed, allowed)
                else:
                    self.assertIsNone(result.data)

    async def test_s01_to_s08_use_real_d_only_when_c_permits(self):
        for case in self.cases:
            with self.subTest(scenario=case["id"]):
                response, calls = await self.run_case(case)
                expected = case["expected"]
                self.assertEqual(response.status, "ok")
                self.assertEqual(response.decision.action.value, expected["action"])
                self.assertEqual(response.decision.reason_code, expected["reason_code"])
                self.assertEqual(calls, expected["modules_called"])
                self.assertEqual(response.state.complaint_status.value, expected["complaint_status"])
                self.assertEqual(response.state.handoff_status.value, expected["handoff_status"])
                self.assertEqual([d.document_id for d in response.citations], expected["citation_ids"])
                if case["id"] == "S06":
                    self.assertEqual([i.product_id for i in response.recommendations],
                                     ["savings-premium", "savings-flex", "emergency-reserve"])
                else:
                    self.assertEqual(response.recommendations, [])

    async def test_s10_no_eligible_product_returns_safe_success(self):
        case = deepcopy(self.s06)
        case["input"]["session_id"] = "session-002"
        response, calls = await self.run_case(case)
        self.assertEqual(response.status, "ok")
        self.assertEqual(calls, ["A", "C", "D"])
        self.assertEqual(response.recommendations, [])
        self.assertEqual(response.decision.action.value, "RECOMMEND")

    async def test_defensive_denial_survives_inconsistent_c_permission(self):
        for complaint, consent in [("OPEN", "GRANTED"), ("RESOLVED", "DENIED")]:
            with self.subTest(complaint=complaint, consent=consent):
                case = deepcopy(self.s06)
                case["initial_state"].update(complaint_status=complaint, consent=consent)
                response, calls = await self.run_case(case)
                self.assertEqual(response.status, "ok")
                self.assertEqual(calls, ["A", "C", "D"])
                self.assertEqual(response.recommendations, [])

    async def test_unknown_session_is_d_module_error_not_empty_catalog(self):
        case = deepcopy(self.s06)
        case["input"]["session_id"] = "unknown"
        response, calls = await self.run_case(case)
        self.assertEqual(calls, ["A", "C", "D"])
        self.assertEqual(response.status, "error")
        self.assertEqual(response.error.module, "D")
        self.assertEqual(response.error.code, "module_error")
        self.assertIsNone(response.decision)
        self.assertEqual(response.recommendations, [])

    async def test_c_state_patch_is_applied_before_real_d_call(self):
        case = deepcopy(self.s06)
        case["initial_state"].update(complaint_status="OPEN", consent="GRANTED")
        case["mock_outputs"]["C"][0]["data"]["next_state"] = {
            "complaint_status": "RESOLVED",
        }
        response, calls = await self.run_case(case)
        self.assertEqual(response.status, "ok")
        self.assertEqual(calls, ["A", "C", "D"])
        self.assertEqual(len(response.recommendations), 3)
        self.assertEqual(response.state.consent.value, "GRANTED")

    async def test_c_cannot_create_consent_through_state_patch(self):
        case = deepcopy(self.s06)
        case["initial_state"]["consent"] = "DENIED"
        case["mock_outputs"]["C"][0]["data"]["next_state"] = {"consent": "GRANTED"}
        response, calls = await self.run_case(case)
        self.assertEqual(response.status, "error")
        self.assertEqual(response.error.module, "C")
        self.assertEqual(response.error.code, "invalid_result")
        self.assertEqual(calls, ["A", "C"])
        self.assertEqual(response.recommendations, [])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RealDIntegrationTests)
    )
    raise SystemExit(not result.wasSuccessful() or bool(result.skipped))
