"""Local account API keeps identity, history, and agent state outside modules."""

import asyncio
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import patch

from banking_agent.app.api.server import DEFAULT_RECOMMENDATION_FIXTURE_PATH, DemoApplication
from banking_agent.app.bootstrap import FixtureModuleFactory, ModuleBundle, StaticModuleFactory
from banking_agent.app.persistence import InMemoryStore, SQLiteStore
from banking_agent.modules.recommendation import RecommendationAdapter, load_fixture
from banking_agent.modules.voice import ASRService, MockASRBackend
from banking_agent.schemas import TranscriptionResult, TranscriptionStatus


def pcm_wav() -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16_000)
        writer.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()


class RecordingFactory:
    mode = "fixture"

    def __init__(self) -> None:
        self.scenarios = []
        self.delegate = FixtureModuleFactory()

    def create(self, *, scenario):
        self.scenarios.append(scenario["id"])
        return self.delegate.create(scenario=scenario)


class ProductionModules:
    """E-owned fake adapters for exercising the production integration path."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.user_texts: list[str] = []

    async def analyze(self, session_id, user_text):
        self.calls.append("A")
        self.user_texts.append(user_text)
        return {
            "status": "ok",
            "data": {"intent": "policy_enquiry", "confidence": 0.95, "risk_level": "LOW", "entities": []},
        }

    async def retrieve(self, query, top_k):
        self.calls.append("B")
        return {
            "status": "ok",
            "data": {"docs": [{"document_id": "synthetic-policy-v1", "title": "Synthetic Policy", "source": "Test", "score": 0.9, "excerpt": "Synthetic evidence."}]},
        }

    async def decide(self, state):
        self.calls.append("C")
        return {"status": "ok", "data": {"action": "ANSWER", "reason_code": "POLICY_EVIDENCE_FOUND", "next_state": {}}}

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.calls.append("D")
        return {"status": "ok", "data": {"allowed": False, "reason_code": "NOT_REQUESTED", "items": []}}


class RecommendationRouteModules(ProductionModules):
    async def analyze(self, session_id, user_text):
        self.calls.append("A")
        return {
            "status": "ok",
            "data": {"intent": "product_recommendation", "confidence": 0.95, "risk_level": "LOW", "entities": []},
        }

    async def decide(self, state):
        self.calls.append("C")
        return {"status": "ok", "data": {"action": "RECOMMEND", "reason_code": "RECOMMENDATION_PERMITTED", "next_state": {}}}


class RecordingRecommendation:
    def __init__(self) -> None:
        self.session_ids: list[str] = []
        self.delegate = RecommendationAdapter(load_fixture(DEFAULT_RECOMMENDATION_FIXTURE_PATH))

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.session_ids.append(session_id)
        return await self.delegate.recommend(session_id, complaint_status, handoff_status, consent)


class DemoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = DemoApplication(store=InMemoryStore(), module_factory=FixtureModuleFactory())

    def tearDown(self) -> None:
        self.app.store.close()

    def api(self, method: str, path: str, body: dict | bytes | None = None, cookie: str = "", content_type: str = "application/json"):
        raw = json.dumps(body).encode() if isinstance(body, dict) else body or b""
        status, headers, response = asyncio.run(self.app.api(method, path, raw, cookie, content_type))
        return status, dict(headers), json.loads(response)

    def account(self, username: str, profile: str = "session-001") -> str:
        password = "testpw"
        status, _, _ = self.api(
            "POST", "/api/auth/register", {"username": username, "password": password, "synthetic_profile_key": profile}
        )
        self.assertEqual(status.value, 201)
        status, headers, _ = self.api("POST", "/api/auth/login", {"username": username, "password": password})
        self.assertEqual(status.value, 200)
        return headers["Set-Cookie"].split(";", 1)[0]

    def use_production_modules(self) -> ProductionModules:
        self.app.store.close()
        modules = ProductionModules()
        bundle = ModuleBundle(modules, modules, modules, modules)
        self.app = DemoApplication(store=InMemoryStore(), module_factory=StaticModuleFactory(bundle))
        return modules

    def test_lists_all_core_scenarios(self) -> None:
        _, _, body = self.api("GET", "/api/scenarios")
        self.assertEqual([item["id"] for item in body["scenarios"]], [f"S{i:02}" for i in range(1, 9)])

    def test_service_start_invalidates_prior_browser_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "demo.sqlite3"
            original = SQLiteStore(database_path)
            original.register("alice", "testpw", "session-001")
            _, token = original.login("alice", "testpw")
            original.close()

            restarted = DemoApplication(database_path=database_path, module_factory=FixtureModuleFactory())
            try:
                self.assertIsNone(restarted.store.current_user(token))
            finally:
                restarted.store.close()

    def test_default_application_composes_the_real_production_bundle(self) -> None:
        self.app.store.close()
        modules = ProductionModules()
        bundle = ModuleBundle(modules, modules, modules, modules)
        with patch("banking_agent.app.api.server.build_production_module_bundle", return_value=bundle) as builder:
            self.app = DemoApplication(store=InMemoryStore())
        self.assertEqual(self.app.module_mode, "production")
        builder.assert_called_once_with(DEFAULT_RECOMMENDATION_FIXTURE_PATH)

    def test_production_mode_runs_free_text_and_keeps_trace_sanitized(self) -> None:
        modules = self.use_production_modules()
        status, _, config = self.api("GET", "/api/config")
        self.assertEqual(status.value, 200)
        self.assertEqual(config["module_mode"], "production")
        self.assertEqual({item["id"] for item in config["synthetic_profiles"]}, {"session-001", "session-002", "session-003", "session-004"})
        profile = next(item for item in config["synthetic_profiles"] if item["id"] == "session-001")
        self.assertEqual(profile["label"], "Adult · Singapore resident")
        self.assertEqual(profile["available_deposit_display"], "SGD 1,500.00")
        self.assertEqual(profile["goal"], "Savings")
        cookie = self.account("alice")
        text = "What is the synthetic replacement fee?"
        status, _, created = self.api("POST", "/api/conversations", {"user_text": text}, cookie)
        self.assertEqual(status.value, 201)
        self.assertEqual(created["response"]["decision"]["action"], "ANSWER")
        conversation = created["conversation"]
        self.assertEqual(conversation["title"], text[:48])
        self.assertEqual(conversation["version"], 1)
        self.assertEqual([item["role"] for item in conversation["messages"]], ["user", "assistant"])
        self.assertEqual(modules.calls, ["A", "C", "B", "C"])

        status, _, updated = self.api(
            "POST", f"/api/conversations/{conversation['id']}/messages",
            {"user_text": "Can you repeat that?", "expected_version": 1}, cookie,
        )
        self.assertEqual(status.value, 200)
        self.assertEqual(updated["conversation"]["version"], 2)
        self.assertEqual(modules.user_texts, [text, "Can you repeat that?"])
        trace = self.app.store.list_traces(1, conversation["id"])[0]
        self.assertIsNone(trace["scenario_id"])
        self.assertNotIn(text, str(trace))

    def test_registration_requires_a_known_synthetic_profile_and_requests_cannot_override_it(self) -> None:
        status, _, body = self.api(
            "POST", "/api/auth/register", {"username": "alice", "password": "testpw", "synthetic_profile_key": "unknown"}
        )
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "valid_synthetic_profile_key_required"})
        cookie = self.account("alice", "session-002")
        status, _, body = self.api(
            "POST", "/api/conversations", {"scenario_id": "S01", "synthetic_profile_key": "session-001"}, cookie
        )
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "synthetic_profile_key_is_account_bound"})

    def test_production_recommendation_resolves_conversation_uuid_to_profile_snapshot(self) -> None:
        self.app.store.close()
        modules = RecommendationRouteModules()
        recommendation = RecordingRecommendation()
        self.app = DemoApplication(
            store=InMemoryStore(),
            module_factory=StaticModuleFactory(ModuleBundle(modules, modules, modules, recommendation)),
        )
        cookie = self.account("alice", "session-002")
        status, _, created = self.api(
            "POST", "/api/conversations", {"user_text": "Recommend a synthetic savings product."}, cookie
        )
        self.assertEqual(status.value, 201)
        self.assertEqual(created["response"]["decision"]["action"], "RECOMMEND")
        self.assertEqual(recommendation.session_ids, ["session-002"])
        self.assertNotEqual(created["conversation"]["id"], "session-002")

    def test_bound_production_profile_is_the_authorized_recommendation_source(self) -> None:
        self.app.store.close()
        modules = RecommendationRouteModules()
        recommendation = RecordingRecommendation()
        self.app = DemoApplication(
            store=InMemoryStore(),
            module_factory=StaticModuleFactory(ModuleBundle(modules, modules, modules, recommendation)),
        )
        cookie = self.account("profile_recommendation", "session-001")
        status, _, created = self.api(
            "POST", "/api/conversations", {"user_text": "Recommend a savings product."}, cookie
        )
        self.assertEqual(status.value, 201)
        self.assertEqual(created["response"]["decision"]["action"], "RECOMMEND")
        self.assertEqual(created["conversation"]["consent"], "GRANTED")
        self.assertEqual(recommendation.session_ids, ["session-001"])

    def test_bound_profile_recommendation_remains_authorized_on_a_later_turn(self) -> None:
        """A local account's profile binding is stable for the whole conversation."""

        self.app.store.close()
        modules = RecommendationRouteModules()
        recommendation = RecordingRecommendation()
        self.app = DemoApplication(
            store=InMemoryStore(),
            module_factory=StaticModuleFactory(ModuleBundle(modules, modules, modules, recommendation)),
        )
        cookie = self.account("profile_recommendation_later", "session-001")
        status, _, created = self.api(
            "POST", "/api/conversations", {"user_text": "Recommend a savings product."}, cookie
        )
        self.assertEqual(status.value, 201)
        conversation = created["conversation"]
        status, _, continued = self.api(
            "POST", f"/api/conversations/{conversation['id']}/messages",
            {"user_text": "Please show the recommendation again.", "expected_version": 1}, cookie,
        )

        self.assertEqual(status.value, 200)
        self.assertEqual(continued["response"]["decision"]["action"], "RECOMMEND")
        self.assertEqual(continued["conversation"]["consent"], "GRANTED")
        self.assertEqual(continued["conversation"]["version"], 2)
        self.assertEqual(recommendation.session_ids, ["session-001", "session-001"])

    def test_modes_reject_the_other_mode_input_shape(self) -> None:
        cookie = self.account("alice")
        status, _, body = self.api("POST", "/api/conversations", {"user_text": "hello"}, cookie)
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "user_text_not_allowed_in_fixture_mode"})

        self.use_production_modules()
        cookie = self.account("alice")
        status, _, body = self.api("GET", "/api/scenarios", cookie=cookie)
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "scenarios_are_only_available_in_fixture_mode"})
        status, _, body = self.api("POST", "/api/conversations", {"scenario_id": "S01"}, cookie)
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "scenario_id_not_allowed_in_production_mode"})

    def test_production_text_requires_non_blank_text_within_limit(self) -> None:
        self.use_production_modules()
        cookie = self.account("alice")
        for text in ("   ", "x" * 2001):
            status, _, body = self.api("POST", "/api/conversations", {"user_text": text}, cookie)
            self.assertEqual(status.value, 400)
            self.assertEqual(body, {"error": "user_text_must_be_1_to_2000_characters"})

    def test_voice_transcription_is_production_only_transient_and_requires_login(self) -> None:
        status, _, body = self.api("POST", "/api/transcriptions", pcm_wav(), content_type="audio/wav")
        self.assertEqual(status.value, 401)
        self.assertEqual(body, {"error": "authentication_required"})

        cookie = self.account("alice")
        status, _, body = self.api("POST", "/api/transcriptions", pcm_wav(), cookie, "audio/wav")
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "voice_input_not_available"})

        self.app.store.close()
        modules = ProductionModules()
        self.app = DemoApplication(
            store=InMemoryStore(),
            module_factory=StaticModuleFactory(ModuleBundle(modules, modules, modules, modules)),
            asr_service=ASRService(MockASRBackend([
                TranscriptionResult(status=TranscriptionStatus.OK, text="Synthetic spoken question", backend="test"),
            ])),
        )
        cookie = self.account("voiceuser")
        status, _, config = self.api("GET", "/api/config")
        self.assertTrue(config["voice_input_available"])
        status, _, body = self.api("POST", "/api/transcriptions", pcm_wav(), cookie, "audio/wav")
        self.assertEqual(status.value, 200)
        self.assertEqual(body["status"], "OK")
        self.assertEqual(body["text"], "Synthetic spoken question")
        self.assertNotIn("backend", body)
        self.assertNotIn("quality", body)
        self.assertEqual(self.app.store.list_conversations(1), [])

    def test_voice_transcription_rejects_invalid_wav_before_backend(self) -> None:
        self.app.store.close()
        modules = ProductionModules()
        self.app = DemoApplication(
            store=InMemoryStore(),
            module_factory=StaticModuleFactory(ModuleBundle(modules, modules, modules, modules)),
            asr_service=ASRService(MockASRBackend([])),
        )
        cookie = self.account("voiceuser")
        status, _, body = self.api("POST", "/api/transcriptions", b"not-wav", cookie, "audio/wav")
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "invalid_wav"})

    def test_login_conversation_and_safe_turn_are_persisted(self) -> None:
        cookie = self.account("alice")
        status, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, cookie)
        self.assertEqual(status.value, 201)
        conversation_id = created["conversation"]["id"]
        self.assertEqual(created["conversation"]["version"], 0)
        status, _, result = self.api(
            "POST", f"/api/conversations/{conversation_id}/messages",
            {"scenario_id": "S03", "expected_version": 0},
            cookie,
        )
        self.assertEqual(status.value, 200)
        self.assertEqual(result["response"]["api_version"], "v1")
        self.assertEqual(result["response"]["decision"]["action"], "ESCALATE")
        self.assertNotIn("reason_code", result["response"])
        self.assertNotIn("state", result["response"])
        conversation = result["conversation"]
        self.assertEqual(conversation["complaint_status"], "OPEN")
        self.assertEqual(conversation["handoff_status"], "ESCALATED")
        self.assertEqual(conversation["version"], 1)
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
        self.api(
            "POST", f"/api/conversations/{created['conversation']['id']}/messages",
            {"scenario_id": "S03", "expected_version": 0},
            cookie,
        )
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
            store=InMemoryStore(), module_factory=FixtureModuleFactory(),
            developer_dashboard=True, developer_username="developer"
        )
        developer = self.account("developer")
        other_user = self.account("otheruser")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, developer)
        conversation_id = created["conversation"]["id"]
        self.api(
            "POST", f"/api/conversations/{conversation_id}/messages",
            {"scenario_id": "S03", "expected_version": 0},
            developer,
        )

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

    def test_stale_conversation_version_is_rejected_without_partial_turn(self) -> None:
        cookie = self.account("alice")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, cookie)
        conversation_id = created["conversation"]["id"]
        payload = {"scenario_id": "S03", "expected_version": 0}

        status, _, _ = self.api("POST", f"/api/conversations/{conversation_id}/messages", payload, cookie)
        self.assertEqual(status.value, 200)
        status, _, body = self.api("POST", f"/api/conversations/{conversation_id}/messages", payload, cookie)
        self.assertEqual(status.value, 409)
        self.assertEqual(body, {"error": "conversation_version_conflict"})

        status, _, body = self.api("GET", f"/api/conversations/{conversation_id}", cookie=cookie)
        self.assertEqual(status.value, 200)
        self.assertEqual(body["conversation"]["version"], 1)
        self.assertEqual([message["role"] for message in body["conversation"]["messages"]], ["user", "assistant"])

    def test_message_requires_a_non_negative_integer_version(self) -> None:
        cookie = self.account("alice")
        _, _, created = self.api("POST", "/api/conversations", {"scenario_id": "S03"}, cookie)
        conversation_id = created["conversation"]["id"]
        status, _, body = self.api(
            "POST", f"/api/conversations/{conversation_id}/messages", {"scenario_id": "S03"}, cookie
        )
        self.assertEqual(status.value, 400)
        self.assertEqual(body, {"error": "expected_version_must_be_non_negative_integer"})
