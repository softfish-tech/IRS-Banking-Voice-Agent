"""Exercise the documented core paths with real A, B, C, D, and E adapters."""

import json
from pathlib import Path
import unittest

from banking_agent.app.orchestrator import Orchestrator
from banking_agent.app.intent_provider import build_intent_module
from banking_agent.modules.rules import RuleEngine
from banking_agent.schemas import AgentState
from helpers.hybrid_e2e_modules import real_recommendation, real_retrieval


SCENARIOS = json.loads(
    (Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text(encoding="utf-8")
)

# The maintained B corpus has a reason-specific lost-card fee rather than the
# generic fee assumed by the legacy S01 fixture.  Real C therefore asks for the
# missing replacement reason; this is a safe, intentional divergence.
REAL_EXPECTATIONS = {
    "S01": ("CLARIFY", "REPLACEMENT_REASON_REQUIRED", ["A", "C", "B", "C"]),
    "S02": ("HANDLE_COMPLAINT", "FEE_COMPLAINT", ["A", "C"]),
    "S03": ("ESCALATE", "HIGH_RISK_TRANSACTION", ["A", "C"]),
    "S04": ("ESCALATE", "FRAUD_SUSPICION", ["A", "C"]),
    "S05": ("BLOCK", "UNRESOLVED_COMPLAINT", ["A", "C"]),
    "S06": ("RECOMMEND", "RECOMMENDATION_PERMITTED", ["A", "C", "D"]),
    "S07": ("CLARIFY", "LOW_INTENT_CONFIDENCE", ["A", "C"]),
    "S08": ("ABSTAIN", "INSUFFICIENT_EVIDENCE", ["A", "C", "B", "C"]),
}


class RecordingIntentAdapter:
    def __init__(self, calls: list[str]) -> None:
        self._adapter = build_intent_module()
        self._calls = calls

    async def analyze(self, session_id: str, user_text: str) -> dict[str, object]:
        self._calls.append("A")
        return await self._adapter.analyze(session_id, user_text)


class RecordingRuleEngine:
    def __init__(self, calls: list[str]) -> None:
        self._engine = RuleEngine()
        self._calls = calls

    async def decide(self, state: AgentState) -> dict[str, object]:
        self._calls.append("C")
        return await self._engine.decide(state)


class RealModuleScenarioE2ETests(unittest.IsolatedAsyncioTestCase):
    async def test_core_scenarios_with_real_module_bundle(self) -> None:
        self.assertEqual([scenario["id"] for scenario in SCENARIOS], list(REAL_EXPECTATIONS))

        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario["id"]):
                calls: list[str] = []
                initial = AgentState(**scenario["input"], **scenario["initial_state"])
                original = initial.model_dump()
                response = await Orchestrator(
                    RecordingIntentAdapter(calls),
                    real_retrieval(calls),
                    RecordingRuleEngine(calls),
                    real_recommendation(calls, {"session-s06": "session-001"}),
                ).handle(initial)

                expected_action, expected_reason, expected_calls = REAL_EXPECTATIONS[scenario["id"]]
                self.assertEqual(response.status, "ok")
                self.assertEqual(calls, expected_calls)
                self.assertEqual(response.decision.action.value, expected_action)
                self.assertEqual(response.decision.reason_code, expected_reason)
                self.assertEqual(initial.model_dump(), original)
                if expected_action == "RECOMMEND":
                    self.assertTrue(response.recommendations)
                else:
                    self.assertEqual(response.recommendations, [])
                if expected_action == "ANSWER":
                    self.assertTrue(response.citations)
                else:
                    self.assertEqual(response.citations, [])

    async def test_social_engineering_transfer_escalates_despite_low_risk_intent(
        self,
    ) -> None:
        """C must retain the safety route when the real classifier misses it."""

        calls: list[str] = []
        initial = AgentState(
            session_id="social-engineering-transfer",
            user_text="I think someone is trying to trick me into making this transfer.",
        )
        response = await Orchestrator(
            RecordingIntentAdapter(calls),
            real_retrieval(calls),
            RecordingRuleEngine(calls),
            real_recommendation(calls, {}),
        ).handle(initial)

        self.assertEqual(response.status, "ok")
        self.assertEqual(calls, ["A", "C"])
        self.assertEqual(response.decision.action.value, "ESCALATE")
        self.assertEqual(response.decision.reason_code, "FRAUD_SUSPICION")
        self.assertEqual(response.state.complaint_status.value, "OPEN")
        self.assertEqual(response.state.handoff_status.value, "ESCALATED")


if __name__ == "__main__":
    unittest.main()
