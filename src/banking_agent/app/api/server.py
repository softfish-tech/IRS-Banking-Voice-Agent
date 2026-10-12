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

from banking_agent.app.bootstrap import ModuleFactory, build_module_factory
from banking_agent.app.api.dto import to_chat_turn_response_v1, to_developer_trace_v1
from banking_agent.app.observability import TraceContext
from banking_agent.app.persistence import ApplicationStore, SESSION_LIFETIME_SECONDS, SQLiteStore, StoreError
from banking_agent.schemas import AgentState

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SCENARIOS_PATH = REPOSITORY_ROOT / "tests" / "fixtures" / "scenarios" / "core.json"
DEFAULT_DATABASE_PATH = REPOSITORY_ROOT / "data" / "processed" / "local_demo.sqlite3"
STATIC_PATH = Path(__file__).with_name("static") / "index.html"
DEVELOPER_STATIC_PATH = Path(__file__).with_name("static") / "developer.html"


class DeveloperDashboardDisabled(Exception):
    """Do not reveal a disabled development-only surface."""


class DeveloperAccessDenied(Exception):
    """The authenticated account is not the configured local developer."""


class DemoApplication:
    """WSGI application for local synthetic-data development, never production."""

    def __init__(
        self,
        scenarios_path: Path = DEFAULT_SCENARIOS_PATH,
        database_path: Path = DEFAULT_DATABASE_PATH,
        module_factory: ModuleFactory | None = None,
        store: ApplicationStore | None = None,
        developer_dashboard: bool | None = None,
        developer_username: str | None = None,
    ) -> None:
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
        self._scenarios = {scenario["id"]: scenario for scenario in scenarios}
        self.store = store or SQLiteStore(database_path)
        self.module_factory = module_factory or build_module_factory(
            os.environ.get("BANKING_AGENT_MODULE_MODE", "fixture")
        )
        self.developer_dashboard = developer_dashboard if developer_dashboard is not None else (
            os.environ.get("BANKING_AGENT_DEVELOPER_DASHBOARD", "").lower() in {"1", "true", "yes"}
        )
        self.developer_username = developer_username if developer_username is not None else os.environ.get(
            "BANKING_AGENT_DEVELOPER_USERNAME", ""
        )

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

    async def api(self, method: str, path: str, body: bytes = b"", cookie_header: str = "") -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        try:
            if method == "GET" and path == "/api/scenarios":
                scenarios = [{"id": item["id"], "user_text": item["input"]["user_text"]} for item in self._scenarios.values()]
                return self._json(HTTPStatus.OK, {"scenarios": scenarios})
            if method == "POST" and path == "/api/auth/register":
                payload = self._payload(body)
                user = self.store.register(payload.get("username", ""), payload.get("password", ""))
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
            if method == "GET" and path == "/api/conversations":
                return self._json(HTTPStatus.OK, {"conversations": self.store.list_conversations(int(user["id"]))})
            if method == "POST" and path == "/api/conversations":
                scenario = self._scenario(self._payload(body).get("scenario_id"))
                conversation = self.store.create_conversation(int(user["id"]), f"{scenario['id']}: {scenario['input']['user_text'][:48]}", scenario["initial_state"])
                return self._json(HTTPStatus.CREATED, {"conversation": conversation})

            parts = path.split("/")
            if len(parts) == 4 and parts[:3] == ["", "api", "conversations"] and method == "GET":
                return self._json(HTTPStatus.OK, {"conversation": self.store.get_conversation(int(user["id"]), parts[3])})
            if len(parts) == 5 and parts[:3] == ["", "api", "conversations"] and parts[4] == "messages" and method == "POST":
                scenario = self._scenario(self._payload(body).get("scenario_id"))
                conversation = self.store.get_conversation(int(user["id"]), parts[3])
                modules = self.module_factory.create(scenario=scenario)
                initial_state = AgentState(
                    session_id=conversation["id"], user_text=scenario["input"]["user_text"],
                    complaint_status=conversation["complaint_status"], handoff_status=conversation["handoff_status"], consent=conversation["consent"],
                )
                response = await modules.new_orchestrator(
                    trace_sink=self.store,
                    trace_context=TraceContext(
                        mode=getattr(self.module_factory, "mode", "custom"),
                        scenario_id=scenario["id"],
                        conversation_id=conversation["id"],
                        user_id=int(user["id"]),
                    ),
                ).handle(initial_state)
                public_response = to_chat_turn_response_v1(response).model_dump(mode="json")
                persisted_response = response.model_dump(mode="json")
                if response.status == "ok":
                    self.store.add_turn(
                        int(user["id"]),
                        parts[3],
                        scenario["input"]["user_text"],
                        public_response,
                        persisted_response["state"],
                    )
                return self._json(HTTPStatus.OK, {"response": public_response, "conversation": self.store.get_conversation(int(user["id"]), parts[3])})
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except PermissionError:
            return self._json(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
        except DeveloperDashboardDisabled:
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except DeveloperAccessDenied:
            return self._json(HTTPStatus.FORBIDDEN, {"error": "developer_access_required"})
        except StoreError as error:
            status = HTTPStatus.NOT_FOUND if str(error) == "conversation_not_found" else HTTPStatus.BAD_REQUEST
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
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length)
        status, headers, result = asyncio.run(self.api(method, path, body, environ.get("HTTP_COOKIE", "")))
        start_response(f"{status.value} {status.phrase}", headers)
        return [result]


def main() -> None:
    app = DemoApplication()
    with make_server("127.0.0.1", 8000, app) as server:
        print("Local account demo: http://127.0.0.1:8000")
        server.serve_forever()


if __name__ == "__main__":
    main()
