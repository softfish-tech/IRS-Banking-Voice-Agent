"""The frozen delivery profile must be explicit, reproducible and overridable."""

import os
import unittest
from unittest.mock import patch

from banking_agent.app.conversation_context import context_memory_enabled
from banking_agent.app.delivery_profile import active_delivery_profile, delivery_setting
from banking_agent.app.llm_agent_support import (
    build_llm_text_assistant_from_environment,
    build_llm_understanding_from_environment,
    middle_loop_enabled,
    understanding_mode_from_environment,
)
from banking_agent.app.response_generator import (
    build_recommendation_response_generator_from_environment,
    build_response_generator_from_environment,
)


class DeliveryProfileTests(unittest.TestCase):
    def test_baseline_keeps_the_offline_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(active_delivery_profile())
            self.assertEqual(delivery_setting("BANKING_AGENT_LLM_UNDERSTANDING", "off"), "off")
            self.assertFalse(context_memory_enabled())
            self.assertFalse(middle_loop_enabled())
            self.assertEqual(understanding_mode_from_environment(), "shadow")

    def test_frozen_profile_selects_the_full_evaluated_llm_chain(self) -> None:
        with patch.dict(os.environ, {"BANKING_AGENT_DELIVERY_PROFILE": "frozen-20261023"}, clear=True):
            self.assertEqual(active_delivery_profile(), "frozen-20261023")
            self.assertTrue(context_memory_enabled())
            self.assertTrue(middle_loop_enabled())
            self.assertEqual(understanding_mode_from_environment(), "fuse")
            self.assertEqual(delivery_setting("BANKING_AGENT_LLM_UNDERSTANDING", "off"), "llm")
            self.assertEqual(delivery_setting("BANKING_AGENT_LLM_QUERY_REWRITE", "off"), "llm")
            self.assertEqual(delivery_setting("BANKING_AGENT_LLM_CLARIFICATION", "off"), "llm")
            self.assertEqual(delivery_setting("BANKING_AGENT_RESPONSE_GENERATOR", "template"), "llm")
            self.assertEqual(
                delivery_setting("BANKING_AGENT_RECOMMENDATION_RESPONSE_GENERATOR", "template"), "llm"
            )

    def test_explicit_environment_value_overrides_the_profile(self) -> None:
        with patch.dict(os.environ, {
            "BANKING_AGENT_DELIVERY_PROFILE": "frozen-20261023",
            "BANKING_AGENT_LLM_QUERY_REWRITE": "off",
        }, clear=True):
            self.assertEqual(delivery_setting("BANKING_AGENT_LLM_QUERY_REWRITE", "off"), "off")

    def test_frozen_profile_builds_every_llm_helper_with_an_explicit_model(self) -> None:
        with patch.dict(os.environ, {
            "BANKING_AGENT_DELIVERY_PROFILE": "frozen-20261023",
            "BANKING_AGENT_LLM_MODEL": "test-model",
        }, clear=True):
            self.assertIsNotNone(build_llm_understanding_from_environment())
            self.assertIsNotNone(build_llm_text_assistant_from_environment())
            self.assertIsNotNone(build_response_generator_from_environment())
            self.assertIsNotNone(build_recommendation_response_generator_from_environment())

    def test_unknown_profile_fails_closed(self) -> None:
        with patch.dict(os.environ, {"BANKING_AGENT_DELIVERY_PROFILE": "unreviewed"}, clear=True):
            with self.assertRaisesRegex(ValueError, "delivery_profile"):
                active_delivery_profile()
