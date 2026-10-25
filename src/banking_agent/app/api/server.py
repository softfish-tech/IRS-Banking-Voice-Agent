"""Local-only account, conversation, and text-mock API.

Run from the repository root with:
    PYTHONPATH=src python -m banking_agent.app.api.server
"""

import asyncio
import json
import os
from http import HTTPStatus
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from wsgiref.simple_server import make_server

from banking_agent.app.bootstrap import (
    ModuleBundle,
    ModuleFactory,
    StaticModuleFactory,
    build_module_factory,
    build_production_module_bundle,
)
from banking_agent.app.conversation_context import context_memory_enabled, recent_public_context
from banking_agent.app.delivery_profile import active_delivery_profile
from banking_agent.app.api.dto import (
    to_chat_turn_response_v1,
    to_developer_trace_v1,
    to_transcription_response_v1,
)
from banking_agent.app.local_env import load_local_env
from banking_agent.app.observability import TraceContext
from banking_agent.app.persistence import ApplicationStore, SESSION_LIFETIME_SECONDS, SQLiteStore, StoreError
from banking_agent.app.recommendation_adapter import ConversationProfileRecommendationAdapter
from banking_agent.modules.recommendation import load_fixture
from banking_agent.modules.voice import ASRService, AudioValidationError, WhisperCppBackend
from banking_agent.modules.voice.asr import MAX_AUDIO_BYTES
from banking_agent.schemas import AgentState, AudioUpload, ConsentStatus

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SCENARIOS_PATH = REPOSITORY_ROOT / "tests" / "fixtures" / "scenarios" / "core.json"
DEFAULT_DATABASE_PATH = REPOSITORY_ROOT / "data" / "processed" / "local_demo.sqlite3"
DEFAULT_RECOMMENDATION_FIXTURE_PATH = REPOSITORY_ROOT / "data" / "fixtures" / "recommendation.json"
STATIC_PATH = Path(__file__).with_name("static") / "index.html"
DEVELOPER_STATIC_PATH = Path(__file__).with_name("static") / "developer.html"
SAFE_INITIAL_STATE = {"complaint_status": "NONE", "handoff_status": "NOT_REQUIRED", "consent": "UNKNOWN"}
MAX_USER_TEXT_LENGTH = 2000


class DeveloperDashboardDisabled(Exception):
    """Do not reveal a disabled development-only surface."""


class DeveloperAccessDenied(Exception):
    """The authenticated account is not the configured local developer."""


def build_asr_service_from_environment() -> ASRService | None:
    """Build the opt-in local ASR adapter without downloading or probing models.

    A missing path is deliberately represented by the backend's sanitized
    ``backend_not_configured`` response instead of preventing the local app from
    starting.  The feature remains absent unless explicitly enabled.
    """
    if os.environ.get("BANKING_AGENT_ASR", "off").lower() != "enabled":
        return None
    executable = os.environ.get("BANKING_AGENT_ASR_EXECUTABLE", "")
    model = os.environ.get("BANKING_AGENT_ASR_MODEL", "")
    try:
        timeout_seconds = float(os.environ.get("BANKING_AGENT_ASR_TIMEOUT_SECONDS", "90"))
    except ValueError:
        timeout_seconds = 90.0
    return ASRService(
        WhisperCppBackend(Path(executable), Path(model), timeout_seconds=max(1.0, timeout_seconds))
    )


class DemoApplication:
    """WSGI application for local synthetic-data development, never production."""

    def __init__(
        self,
        scenarios_path: Path = DEFAULT_SCENARIOS_PATH,
        database_path: Path = DEFAULT_DATABASE_PATH,
        module_factory: ModuleFactory | None = None,
        store: ApplicationStore | None = None,
        recommendation_fixture_path: Path = DEFAULT_RECOMMENDATION_FIXTURE_PATH,
        developer_dashboard: bool | None = None,
        developer_username: str | None = None,
        asr_service: ASRService | None = None,
    ) -> None:
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
        self._scenarios = {scenario["id"]: scenario for scenario in scenarios}
        self.store = store or SQLiteStore(database_path)
        # The local demo requires a fresh sign-in whenever its service starts,
        # while preserving the synthetic accounts and conversation history.
        self.store.clear_login_sessions()
        fixture = load_fixture(recommendation_fixture_path)
        self.synthetic_profiles = dict(fixture.customer_profiles)
        self.synthetic_profile_keys = frozenset(self.synthetic_profiles)
        if module_factory is not None:
            self.module_factory = module_factory
        else:
            mode = os.environ.get("BANKING_AGENT_MODULE_MODE", "production")
            self.module_factory = (
                StaticModuleFactory(build_production_module_bundle(recommendation_fixture_path))
                if mode == "production"
                else build_module_factory(mode)
            )
        self.developer_dashboard = developer_dashboard if developer_dashboard is not None else (
            os.environ.get("BANKING_AGENT_DEVELOPER_DASHBOARD", "").lower() in {"1", "true", "yes"}
        )
        self.developer_username = developer_username if developer_username is not None else os.environ.get(
            "BANKING_AGENT_DEVELOPER_USERNAME", ""
        )
        self.asr_service = asr_service

    @property
    def voice_input_available(self) -> bool:
        """Voice is a production-only, explicitly configured input adapter."""
        return self.module_mode == "production" and self.asr_service is not None

    def _public_synthetic_profiles(self) -> list[dict[str, object]]:
        """Return display-safe, fixture-backed choices for the local UI."""

        residency_labels = {"SG": "Singapore resident", "OTHER": "Non-Singapore resident"}
        goal_labels = {"savings": "Savings", "emergency": "Emergency fund"}
        profiles: list[dict[str, object]] = []
        for key, profile in sorted(self.synthetic_profiles.items()):
            residency = residency_labels.get(profile.residency, profile.residency)
            goal = goal_labels.get(profile.goal, profile.goal)
            age_group = "Minor" if profile.age < 18 else "Adult"
            profiles.append(
                {
                    "id": key,
                    "label": f"{age_group} · {residency}",
                    "age": profile.age,
                    "residency": residency,
                    "available_deposit_display": f"SGD {profile.available_deposit_cents / 100:,.2f}",
                    "goal": goal,
                }
            )
        return profiles

    @staticmethod
    def _json(status: HTTPStatus, payload: Any, headers: list[tuple[str, str]] | None = None) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        base_headers = [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))]
        return status, base_headers + (headers or []), body

    @staticmethod
    def _payload(body: bytes) -> dict[str, Any]:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise StoreError("valid_json_required") from error
        if not isinstance(payload, dict):
            raise StoreError("json_object_required")
        return payload

    @staticmethod
    def _session_token(cookie_header: str = "") -> str | None:
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        item = cookie.get("banking_session")
        return item.value if item else None

    @staticmethod
    def _cookie(token: str, *, clear: bool = False) -> tuple[str, str]:
        max_age = 0 if clear else SESSION_LIFETIME_SECONDS
        value = "" if clear else token
        return ("Set-Cookie", f"banking_session={value}; HttpOnly; SameSite=Lax; Path=/; Max-Age={max_age}")

    def _user_or_error(self, cookie_header: str) -> dict[str, object]:
        user = self.store.current_user(self._session_token(cookie_header))
        if user is None:
            raise PermissionError
        return user

    def _developer_or_error(self, cookie_header: str) -> dict[str, object]:
        if not self.developer_dashboard:
            raise DeveloperDashboardDisabled
        user = self._user_or_error(cookie_header)
        if not self.developer_username or user["username"] != self.developer_username:
            raise DeveloperAccessDenied
        return user

    def _scenario(self, scenario_id: object) -> dict[str, Any]:
        if not isinstance(scenario_id, str) or scenario_id not in self._scenarios:
            raise StoreError("valid_scenario_id_required")
        return self._scenarios[scenario_id]

    def _synthetic_profile_key(self, payload: dict[str, Any]) -> str:
        profile_key = payload.get("synthetic_profile_key")
        if not isinstance(profile_key, str) or profile_key not in self.synthetic_profile_keys:
            raise StoreError("valid_synthetic_profile_key_required")
        return profile_key

    @staticmethod
    def _reject_profile_override(payload: dict[str, Any]) -> None:
        if "synthetic_profile_key" in payload:
            raise StoreError("synthetic_profile_key_is_account_bound")

    @property
    def module_mode(self) -> str:
        mode = getattr(self.module_factory, "mode", None)
        if mode not in {"fixture", "production"}:
            raise StoreError("module_factory_mode_must_be_fixture_or_production")
        return mode

    @staticmethod
    def _expected_version(payload: dict[str, Any]) -> int:
        expected_version = payload.get("expected_version")
        if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 0:
            raise StoreError("expected_version_must_be_non_negative_integer")
        return expected_version

    @staticmethod
    def _user_text(payload: dict[str, Any]) -> str:
        user_text = payload.get("user_text")
        if not isinstance(user_text, str):
            raise StoreError("user_text_must_be_1_to_2000_characters")
        user_text = user_text.strip()
        if not user_text or len(user_text) > MAX_USER_TEXT_LENGTH:
            raise StoreError("user_text_must_be_1_to_2000_characters")
        return user_text

    async def _run_turn(
        self,
        *,
        user: dict[str, object],
        conversation: dict[str, object],
        user_text: str,
        expected_version: int,
        scenario: dict[str, Any] | None = None,
    ) -> tuple[dict[str, object], dict[str, object]]:
        modules = self.module_factory.create(scenario=scenario)
        if self.module_mode == "production":
            modules = ModuleBundle(
                modules.intent,
                modules.retrieval,
                modules.rules,
                ConversationProfileRecommendationAdapter(
                    modules.recommendation,
                    self.store.conversation_profile_key,
                ),
                response_generator=modules.response_generator,
                recommendation_response_generator=modules.recommendation_response_generator,
                query_rewriter=modules.query_rewriter,
                clarification_generator=modules.clarification_generator,
            )
        # The local production surface binds one synthetic profile to an
        # authenticated account at registration.  In this delivery mode that
        # binding is the customer-authorised profile source for an explicitly
        # requested recommendation; it is not a new C business decision.
        # Fixture runs preserve their declared consent state.
        consent = str(conversation["consent"])
        if self.module_mode == "production" and conversation.get("synthetic_profile_key"):
            consent = ConsentStatus.GRANTED.value
        state_kwargs: dict[str, object] = {
            "session_id": str(conversation["id"]),
            "user_text": user_text,
            "complaint_status": str(conversation["complaint_status"]),
            "handoff_status": str(conversation["handoff_status"]),
            "consent": consent,
        }
        if context_memory_enabled():
            state_kwargs["conversation_context"] = recent_public_context(
                conversation["messages"]
            )
        response = await modules.new_orchestrator(
            trace_sink=self.store,
            trace_context=TraceContext(
                mode=self.module_mode,
                scenario_id=scenario["id"] if scenario else None,
                conversation_id=str(conversation["id"]),
                user_id=int(user["id"]),
            ),
        ).handle(
            AgentState(**state_kwargs)
        )
        public_response = to_chat_turn_response_v1(response).model_dump(mode="json")
        if response.status == "ok":
            conversation = self.store.add_turn(
                int(user["id"]),
                str(conversation["id"]),
                user_text,
                public_response,
                response.model_dump(mode="json")["state"],
                expected_version,
            )
        return public_response, conversation

    async def api(
        self,
        method: str,
        path: str,
        body: bytes = b"",
        cookie_header: str = "",
        content_type: str = "application/json",
    ) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        try:
            if method == "GET" and path == "/api/config":
                return self._json(
                    HTTPStatus.OK,
                    {
                        "module_mode": self.module_mode,
                        "synthetic_profiles": self._public_synthetic_profiles(),
                        "voice_input_available": self.voice_input_available,
                        "delivery_profile": active_delivery_profile() or "baseline",
                    },
                )
            if method == "GET" and path == "/api/scenarios":
                if self.module_mode != "fixture":
                    raise StoreError("scenarios_are_only_available_in_fixture_mode")
                scenarios = [{"id": item["id"], "user_text": item["input"]["user_text"]} for item in self._scenarios.values()]
                return self._json(HTTPStatus.OK, {"scenarios": scenarios})
            if method == "POST" and path == "/api/auth/register":
                payload = self._payload(body)
                user = self.store.register(
                    payload.get("username", ""),
                    payload.get("password", ""),
                    self._synthetic_profile_key(payload),
                )
                return self._json(HTTPStatus.CREATED, {"user": user})
            if method == "POST" and path == "/api/auth/login":
                payload = self._payload(body)
                user, token = self.store.login(payload.get("username", ""), payload.get("password", ""))
                return self._json(HTTPStatus.OK, {"user": user}, [self._cookie(token)])
            if method == "POST" and path == "/api/auth/logout":
                self.store.logout(self._session_token(cookie_header))
                return self._json(HTTPStatus.OK, {"status": "logged_out"}, [self._cookie("", clear=True)])
            if method == "GET" and path == "/api/me":
                return self._json(HTTPStatus.OK, {"user": self._user_or_error(cookie_header)})

            developer_parts = path.split("/")
            if (
                method == "GET"
                and len(developer_parts) == 6
                and developer_parts[:4] == ["", "api", "developer", "conversations"]
                and developer_parts[5] == "traces"
            ):
                developer = self._developer_or_error(cookie_header)
                traces = [
                    to_developer_trace_v1(trace).model_dump(mode="json")
                    for trace in self.store.list_traces(int(developer["id"]), developer_parts[4])
                ]
                return self._json(HTTPStatus.OK, {"api_version": "v1", "traces": traces})

            user = self._user_or_error(cookie_header)
            if method == "POST" and path == "/api/transcriptions":
                if not self.voice_input_available:
                    raise StoreError("voice_input_not_available")
                try:
                    result = await self.asr_service.transcribe(AudioUpload(content_type=content_type, data=body))
                except AudioValidationError as error:
                    raise StoreError(error.code) from error
                except Exception:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "asr_unavailable"})
                return self._json(HTTPStatus.OK, to_transcription_response_v1(result).model_dump(mode="json"))
            if method == "GET" and path == "/api/conversations":
                return self._json(HTTPStatus.OK, {"conversations": self.store.list_conversations(int(user["id"]))})
            if method == "POST" and path == "/api/conversations":
                payload = self._payload(body)
                self._reject_profile_override(payload)
                if self.module_mode == "fixture":
                    if "user_text" in payload:
                        raise StoreError("user_text_not_allowed_in_fixture_mode")
                    scenario = self._scenario(payload.get("scenario_id"))
                    conversation = self.store.create_conversation(
                        int(user["id"]), f"{scenario['id']}: {scenario['input']['user_text'][:48]}", scenario["initial_state"]
                    )
                    return self._json(HTTPStatus.CREATED, {"conversation": conversation})
                if "scenario_id" in payload:
                    raise StoreError("scenario_id_not_allowed_in_production_mode")
                user_text = self._user_text(payload)
                conversation = self.store.create_conversation(int(user["id"]), user_text[:48], SAFE_INITIAL_STATE)
                public_response, conversation = await self._run_turn(
                    user=user,
                    conversation=conversation,
                    user_text=user_text,
                    expected_version=0,
                )
                return self._json(HTTPStatus.CREATED, {"response": public_response, "conversation": conversation})

            parts = path.split("/")
            if len(parts) == 4 and parts[:3] == ["", "api", "conversations"] and method == "GET":
                return self._json(HTTPStatus.OK, {"conversation": self.store.get_conversation(int(user["id"]), parts[3])})
            if len(parts) == 5 and parts[:3] == ["", "api", "conversations"] and parts[4] == "messages" and method == "POST":
                payload = self._payload(body)
                self._reject_profile_override(payload)
                expected_version = self._expected_version(payload)
                conversation = self.store.get_conversation(int(user["id"]), parts[3])
                if self.module_mode == "fixture":
                    if "user_text" in payload:
                        raise StoreError("user_text_not_allowed_in_fixture_mode")
                    scenario = self._scenario(payload.get("scenario_id"))
                    user_text = scenario["input"]["user_text"]
                else:
                    if "scenario_id" in payload:
                        raise StoreError("scenario_id_not_allowed_in_production_mode")
                    scenario = None
                    user_text = self._user_text(payload)
                public_response, conversation = await self._run_turn(
                    user=user,
                    conversation=conversation,
                    user_text=user_text,
                    expected_version=expected_version,
                    scenario=scenario,
                )
                return self._json(HTTPStatus.OK, {"response": public_response, "conversation": conversation})
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except PermissionError:
            return self._json(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
        except DeveloperDashboardDisabled:
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except DeveloperAccessDenied:
            return self._json(HTTPStatus.FORBIDDEN, {"error": "developer_access_required"})
        except StoreError as error:
            status = (
                HTTPStatus.NOT_FOUND if str(error) == "conversation_not_found"
                else HTTPStatus.CONFLICT if str(error) == "conversation_version_conflict"
                else HTTPStatus.BAD_REQUEST
            )
            return self._json(status, {"error": str(error)})

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method, path = environ["REQUEST_METHOD"], environ["PATH_INFO"]
        if method == "GET" and path == "/":
            content = STATIC_PATH.read_bytes()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(content)))])
            return [content]
        if method == "GET" and path == "/developer":
            try:
                self._developer_or_error(environ.get("HTTP_COOKIE", ""))
            except DeveloperDashboardDisabled:
                start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
                return [b"Not found"]
            except PermissionError:
                start_response("401 Unauthorized", [("Content-Type", "text/plain; charset=utf-8")])
                return [b"Authentication required"]
            except DeveloperAccessDenied:
                start_response("403 Forbidden", [("Content-Type", "text/plain; charset=utf-8")])
                return [b"Developer access required"]
            content = DEVELOPER_STATIC_PATH.read_bytes()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(content)))])
            return [content]
        try:
            length = max(0, int(environ.get("CONTENT_LENGTH") or 0))
        except ValueError:
            length = 0
        if method == "POST" and path == "/api/transcriptions" and length > MAX_AUDIO_BYTES:
            status, headers, result = self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_audio_size"})
            start_response(f"{status.value} {status.phrase}", headers)
            return [result]
        body = environ["wsgi.input"].read(length)
        status, headers, result = asyncio.run(
            self.api(method, path, body, environ.get("HTTP_COOKIE", ""), environ.get("CONTENT_TYPE", ""))
        )
        start_response(f"{status.value} {status.phrase}", headers)
        return [result]


def main() -> None:
    load_local_env()
    app = DemoApplication(asr_service=build_asr_service_from_environment())
    with make_server("127.0.0.1", 8000, app) as server:
        print("Local account demo: http://127.0.0.1:8000")
        server.serve_forever()


if __name__ == "__main__":
    main()
