"""Contract failures must not produce successful answers or recommendations."""
import asyncio
import json
from pathlib import Path
import unittest
from helpers.mock_modules import ScriptedModules
from banking_agent.schemas import AgentState
from banking_agent.app.orchestrator import Orchestrator

SCENARIOS = json.loads((Path(__file__).parents[1] / 'fixtures/scenarios/core.json').read_text())

class FailureTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, modules, timeout=1):
        return await Orchestrator(modules, modules, modules, modules, timeout_seconds=timeout).handle(AgentState(session_id='test', user_text='Hello'))

    async def test_c_error_stops_downstream(self):
        modules = ScriptedModules(SCENARIOS[0]['mock_outputs'])
        modules.outputs['C'][0] = {'status':'error'}
        result = await self.run_case(modules)
        self.assertEqual(result.status, 'error')
        self.assertEqual(result.error.code, 'module_error')
        self.assertEqual(modules.calls, ['A', 'C'])
        self.assertIsNone(result.decision)
        self.assertEqual(result.recommendations, [])

    async def test_illegal_patch_is_rejected(self):
        modules = ScriptedModules(SCENARIOS[0]['mock_outputs'])
        modules.outputs['C'][0]['data']['next_state'] = {'consent':'GRANTED'}
        result = await self.run_case(modules)
        self.assertEqual(result.error.code, 'invalid_result')
        self.assertEqual(result.state.consent.value, 'UNKNOWN')
        self.assertEqual(modules.calls, ['A', 'C'])

    async def test_c_cannot_authorize_answer_without_evidence(self):
        modules = ScriptedModules(SCENARIOS[7]['mock_outputs'])
        modules.outputs['C'][1] = modules.outputs['C'][0]
        result = await self.run_case(modules)
        self.assertEqual(result.status, 'error')
        self.assertEqual(result.error.module, 'C')
        self.assertEqual(result.citations, [])

    async def test_timeout(self):
        class Slow(ScriptedModules):
            async def analyze(self, *args):
                await asyncio.sleep(1)
        result = await self.run_case(Slow(SCENARIOS[0]['mock_outputs']), timeout=.01)
        self.assertEqual(result.error.code, 'timeout')
        self.assertEqual(result.error.module, 'A')

    async def test_exception_is_sanitized(self):
        class Broken(ScriptedModules):
            async def analyze(self, *args):
                raise RuntimeError('sensitive implementation detail')
        result = await self.run_case(Broken(SCENARIOS[0]['mock_outputs']))
        self.assertEqual(result.error.code, 'exception')
        self.assertNotIn('sensitive', result.model_dump_json())

    async def test_d_denial_hides_items(self):
        modules = ScriptedModules(SCENARIOS[5]['mock_outputs'])
        modules.outputs['D']['data']['allowed'] = False
        result = await self.run_case(modules)
        self.assertEqual(result.status, 'ok')
        self.assertEqual(result.recommendations, [])
        self.assertNotIn('Smart Savings', result.text)

    async def test_previous_request_outputs_are_cleared(self):
        modules = ScriptedModules(SCENARIOS[0]['mock_outputs'])
        previous = await self.run_case(modules)
        previous.state.recommendations = []
        new_modules = ScriptedModules(SCENARIOS[2]['mock_outputs'])
        response = await Orchestrator(new_modules, new_modules, new_modules, new_modules).handle(previous.state)
        self.assertEqual(response.state.retrieved_docs, [])
        self.assertEqual(response.citations, [])
        self.assertEqual(new_modules.calls, ['A', 'C'])

    async def test_b_error_does_not_render_answer(self):
        modules = ScriptedModules(SCENARIOS[0]['mock_outputs'])
        modules.outputs['B'] = {'status':'error'}
        result = await self.run_case(modules)
        self.assertEqual(result.status, 'error')
        self.assertEqual(result.error.module, 'B')
        self.assertIsNone(result.decision)
        self.assertEqual(result.citations, [])
