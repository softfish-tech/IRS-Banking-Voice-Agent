"""Published encoder classifier checked through E's adapter contract."""

import unittest

from helpers.adapter_contracts import assert_intent_adapter_contract

from banking_agent.modules.intent import EncoderIntentClassifier, IntentModuleAdapter
from banking_agent.modules.intent.taxonomy import OPERATIONAL_INTENTS

try:
    import numpy as np
except ImportError:  # pragma: no cover - CI installs only the base package
    np = None


class _ConstantEncoder:
    def encode(self, texts, **kwargs):
        vectors = np.ones((len(texts), 384), dtype=np.float32)
        return vectors / np.sqrt(384.0)


@unittest.skipUnless(np is not None, "encoder inference extra not installed")
class EncoderAdapterContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_encoder_classifier_passes_the_intent_adapter_contract(self) -> None:
        classifier = EncoderIntentClassifier.from_pretrained(
            encoder=_ConstantEncoder()
        )
        result = await assert_intent_adapter_contract(
            IntentModuleAdapter(classifier=classifier.classify),
            "session-encoder-001",
            "Someone used my card without my permission.",
        )
        self.assertEqual(result.status, "ok")
        self.assertIn(result.data.intent, OPERATIONAL_INTENTS)
        self.assertEqual(result.data.risk_level.value, "HIGH")


if __name__ == "__main__":
    unittest.main()
