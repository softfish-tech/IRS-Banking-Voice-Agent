"""Configuration tests for E's selection of A's public adapter."""

import unittest
from unittest.mock import patch

from banking_agent.app.intent_provider import build_intent_module
from banking_agent.schemas import UnderstandingResult


class _EncoderDouble:
    def classify(self, text: str) -> UnderstandingResult:
        del text
        return UnderstandingResult(intent="policy_enquiry", confidence=0.9, risk_level="LOW")


class IntentProviderTests(unittest.TestCase):
    def test_rules_is_the_dependency_free_default(self) -> None:
        adapter = build_intent_module("rules")
        self.assertEqual(adapter.__class__.__name__, "IntentModuleAdapter")

    def test_unknown_provider_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "intent_provider_must_be_rules_trained_or_minilm_encoder"):
            build_intent_module("unknown")

    @patch("banking_agent.app.intent_provider.EncoderIntentClassifier.from_pretrained")
    def test_minilm_encoder_uses_a_public_classifier_contract(self, load) -> None:
        load.return_value = _EncoderDouble()
        adapter = build_intent_module("minilm_encoder")
        self.assertEqual(adapter.__class__.__name__, "IntentModuleAdapter")
        load.assert_called_once_with()

    def test_trained_provider_requires_an_explicit_artifact(self) -> None:
        with self.assertRaisesRegex(ValueError, "trained_intent_model_path_required"):
            build_intent_module("trained", None)
        with self.assertRaisesRegex(ValueError, "trained_intent_model_not_found"):
            build_intent_module("trained", "/private/tmp/missing-intent-model.joblib")

    @patch.dict("os.environ", {"BANKING_AGENT_LLM_UNDERSTANDING": "llm", "BANKING_AGENT_LLM_MIDDLE_LOOP": "off"}, clear=False)
    def test_llm_understanding_requires_explicit_middle_loop_opt_in(self) -> None:
        adapter = build_intent_module("rules")
        self.assertEqual(adapter.__class__.__name__, "IntentModuleAdapter")


if __name__ == "__main__":
    unittest.main()
