"""The composition root keeps module selection out of API routes."""

import json
from pathlib import Path
import unittest

from banking_agent.app.bootstrap import FixtureModuleFactory, ModuleBundle, StaticModuleFactory, build_module_factory
from banking_agent.app.demo import ScenarioModules

SCENARIOS = json.loads((Path(__file__).parents[1] / "fixtures/scenarios/core.json").read_text())


class BootstrapTests(unittest.TestCase):
    def test_fixture_factory_creates_a_fresh_bundle_per_turn(self) -> None:
        factory = FixtureModuleFactory()
        first = factory.create(scenario=SCENARIOS[0])
        second = factory.create(scenario=SCENARIOS[0])
        self.assertIsNot(first.intent, second.intent)
        self.assertIs(first.intent, first.rules)

    def test_static_factory_preserves_owner_supplied_adapters(self) -> None:
        adapter = ScenarioModules(SCENARIOS[0]["mock_outputs"])
        bundle = ModuleBundle(adapter, adapter, adapter, adapter)
        factory = StaticModuleFactory(bundle)
        self.assertIs(factory.create().rules, adapter)

    def test_unconfigured_production_mode_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit_module_bundle"):
            build_module_factory("production")
