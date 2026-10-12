"""Local account API keeps identity, history, and agent state outside modules."""

import asyncio
import json
import unittest

from banking_agent.app.api.server import DemoApplication
from banking_agent.app.bootstrap import FixtureModuleFactory
from banking_agent.app.persistence import InMemoryStore


class RecordingFactory:
    mode = "test"

    def __init__(self) -> None:
        self.scenarios = []
        self.delegate = FixtureModuleFactory()

    def create(self, *, scenario):
        self.scenarios.append(scenario["id"])
        return self.delegate.create(scenario=scenario)


class DemoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = DemoApplication(store=InMemoryStore())

    def tearDown(self) -> None:
        self.app.store.close()

    def api(self, method: str, path: str, body: dict | None = None, cookie: str = ""):
        raw = json.dumps(body).encode() if body is not None else b""
        status, headers, response = asyncio.run(self.app.api(method, path, raw, cookie))
        return status, dict(headers), json.loads(response)

    def account(self, username: str) -> str:
        password = "testpw"
        status, _, _ = self.api("POST", "/api/auth/register", {"username": username, "password": password})
        self.assertEqual(status.value, 201)
        status, headers, _ = self.api("POST", "/api/auth/login", {"username": username, "password": password})
        self.assertEqual(status.value, 200)
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_lists_all_core_scenarios(self) -> None:
        _, _, body = self.api("GET", "/api/scenarios")
        self.assertEqual([item["id"] for item in body["scenarios"]], [f"S{i:02}" for i in range(1, 9)])

    def test_login_conversation_and_safe_turn_are_persisted(self) -> None:
        cookie = self.account("alice")
        status, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, cookie)
        self.assertEqual(status.value, 201)
        conversation_id = created["conversation"]["id"]
        status, _, result = self.api("POST", f"/api/conversations/{conversation_id}/messages", {"scenario_id": "S03"}, cookie)
        self.assertEqual(status.value, 200)
        self.assertEqual(result["response"]["api_version"], "v1")
        self.assertEqual(result["response"]["decision"]["action"], "ESCALATE")
        self.assertNotIn("reason_code", result["response"])
        self.assertNotIn("state", result["response"])
        conversation = result["conversation"]
        self.assertEqual(conversation["complaint_status"], "OPEN")
        self.assertEqual(conversation["handoff_status"], "ESCALATED")
        self.assertEqual([message["role"] for message in conversation["messages"]], ["user", "assistant"])
        self.assertNotIn("state", conversation["messages"][1]["response"])
        self.assertNotIn("reason_code", str(conversation["messages"][1]["response"]))
        self.assertEqual(conversation["messages"][1]["response"]["api_version"], "v1")
        trace = self.app.store.list_traces(1, conversation_id)[0]
        self.assertEqual([(item["module"], item["status"]) for item in trace["modules"]], [("A", "ok"), ("C", "ok")])
        self.assertTrue(all(isinstance(item["duration_ms"], int) for item in trace["modules"]))
        self.assertEqual(trace["action"], "ESCALATE")
        self.assertEqual(trace["state_patch"], {"complaint_status": "OPEN", "handoff_status": "ESCALATED"})

    def test_conversations_are_isolated_between_users(self) -> None:
        alice = self.account("alice")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S01"}, alice)
        bob = self.account("bob")
        status, _, body = self.api("GET", f"/api/conversations/{created['conversation']['id']}", cookie=bob)
        self.assertEqual(status.value, 404)
        self.assertEqual(body["error"], "conversation_not_found")

    def test_conversation_endpoints_require_login(self) -> None:
        status, _, body = self.api("GET", "/api/conversations")
        self.assertEqual(status.value, 401)
        self.assertEqual(body["error"], "authentication_required")

    def test_route_uses_injected_module_factory(self) -> None:
        self.app.store.close()
        factory = RecordingFactory()
        self.app = DemoApplication(store=InMemoryStore(), module_factory=factory)
        cookie = self.account("alice")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, cookie)
        self.api("POST", f"/api/conversations/{created['conversation']['id']}/messages", {"scenario_id": "S03"}, cookie)
        self.assertEqual(factory.scenarios, ["S03"])

    def test_developer_trace_endpoint_requires_explicit_mode_and_configured_account(self) -> None:
        developer = self.account("developer")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, developer)
        conversation_id = created["conversation"]["id"]
        status, _, body = self.api("GET", f"/api/developer/conversations/{conversation_id}/traces", cookie=developer)
        self.assertEqual(status.value, 404)
        self.assertEqual(body["error"], "not_found")

        self.app.store.close()
        self.app = DemoApplication(
            store=InMemoryStore(), developer_dashboard=True, developer_username="developer"
        )
        developer = self.account("developer")
        other_user = self.account("otheruser")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, developer)
        conversation_id = created["conversation"]["id"]
        self.api("POST", f"/api/conversations/{conversation_id}/messages", {"scenario_id": "S03"}, developer)

        status, _, body = self.api("GET", f"/api/developer/conversations/{conversation_id}/traces", cookie=other_user)
        self.assertEqual(status.value, 403)
        self.assertEqual(body["error"], "developer_access_required")
        status, _, body = self.api("GET", f"/api/developer/conversations/{conversation_id}/traces", cookie=developer)
        self.assertEqual(status.value, 200)
        trace = body["traces"][0]
        self.assertEqual(trace["action"], "ESCALATE")
        self.assertEqual(trace["reason_code"], "HIGH_RISK_TRANSACTION")
        self.assertEqual([(item["module"], item["status"]) for item in trace["modules"]], [("A", "ok"), ("C", "ok")])
        self.assertNotIn("Someone used my card", str(body))
