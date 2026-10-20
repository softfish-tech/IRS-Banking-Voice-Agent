"""Run draft multi-turn fixtures through state hand-off with real B/D."""

import json
from pathlib import Path
import unittest

from banking_agent.app.api.dto import to_chat_turn_response_v1
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.schemas import AgentState
from helpers.hybrid_e2e_modules import real_recommendation, real_retrieval, scripted_a_and_c


FIXTURE_ROOT = Path(__file__).parent / "multi_turn"


def load_sequences() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURE_ROOT.glob("**/*.json"))
    ]


class MultiTurnSequenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_sequences_preserve_declared_business_state(self) -> None:
        sequences = load_sequences()
        self.assertEqual(len(sequences), 16)
        self.assertEqual(len({item["sequence_id"] for item in sequences}), 16)

        for sequence in sequences:
            with self.subTest(sequence=sequence["sequence_id"]):
                current_state = sequence["initial_state"]
                all_calls: list[str] = []
                for turn in sequence["turns"]:
                    self.assertEqual(current_state, turn["expected_state_before"])
                    initial = AgentState(
                        session_id=sequence["sequence_id"],
                        user_text=turn["user_text"],
                        **current_state,
                    )
                    modules = scripted_a_and_c(turn["scripted_module_envelopes"])
                    response = await Orchestrator(
                        modules,
                        real_retrieval(modules.calls),
                        modules,
                        real_recommendation(modules.calls),
                    ).handle(initial)
                    expected = turn["expected"]
                    self.assertEqual(response.status, expected["status"])
                    self.assertEqual(modules.calls, expected["module_call_order"])
                    for module in expected.get("modules_not_called", []):
                        self.assertNotIn(module, modules.calls)
                    public = to_chat_turn_response_v1(response)
                    self.assertEqual(public.message.kind, expected["public_message_kind"])
                    current_state = {
                        "complaint_status": response.state.complaint_status.value,
                        "handoff_status": response.state.handoff_status.value,
                        "consent": response.state.consent.value,
                    }
                    self.assertEqual(current_state, expected["state_after"])
                    all_calls.extend(modules.calls)

                assertions = sequence.get("sequence_assertions", {})
                if assertions.get("unauthorised_d_call_count") == 0:
                    self.assertNotIn("D", all_calls)
                if assertions.get("state_is_carried_between_turns"):
                    self.assertEqual(current_state, sequence["turns"][-1]["expected"]["state_after"])


if __name__ == "__main__":
    unittest.main()
