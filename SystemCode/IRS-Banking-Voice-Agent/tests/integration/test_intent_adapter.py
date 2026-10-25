"""Part A's async adapter checked against E's reusable contract harness."""

import unittest

from helpers.adapter_contracts import assert_intent_adapter_contract

from banking_agent.modules.intent import IntentModuleAdapter


class IntentAdapterContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_adapter_passes_the_shared_contract(self) -> None:
        result = await assert_intent_adapter_contract(
            IntentModuleAdapter(),
            "session-001",
            "Someone used my card without my permission.",
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data.intent, "unauthorized_transaction")
        self.assertEqual(result.data.risk_level.value, "HIGH")

    async def test_blank_text_is_a_valid_technical_error_envelope(self) -> None:
        result = await assert_intent_adapter_contract(
            IntentModuleAdapter(), "session-001", "   "
        )
        self.assertEqual(result.status, "error")
        self.assertIsNone(result.data)


if __name__ == "__main__":
    unittest.main()
