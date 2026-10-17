"""Local-only identity and conversation persistence for the phase-one demo."""

import hashlib
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import uuid4

from banking_agent.app.observability import DecisionTrace
from banking_agent.schemas import AgentState

SESSION_LIFETIME_SECONDS = 24 * 60 * 60
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,64}$")


class StoreError(ValueError):
    """A safe error message suitable for the local API response."""


@runtime_checkable
class ApplicationStore(Protocol):
    """Persistence boundary used by the E-owned application layer."""

    def register(self, username: str, password: str) -> dict[str, object]: ...
    def login(self, username: str, password: str) -> tuple[dict[str, object], str]: ...
    def logout(self, token: str | None) -> None: ...
    def current_user(self, token: str | None) -> dict[str, object] | None: ...
    def create_conversation(self, user_id: int, title: str, initial_state: dict[str, str]) -> dict[str, object]: ...
    def list_conversations(self, user_id: int) -> list[dict[str, object]]: ...
    def get_conversation(self, user_id: int, conversation_id: str) -> dict[str, object]: ...
    def add_turn(
        self,
        user_id: int,
        conversation_id: str,
        user_text: str,
        public_response: dict[str, object],
        final_state: dict[str, object],
        expected_version: int,
    ) -> dict[str, object]: ...
    def record_trace(self, trace: DecisionTrace) -> None: ...
    def list_traces(self, user_id: int, conversation_id: str) -> list[dict[str, object]]: ...
    def close(self) -> None: ...


class SQLiteStore:
    """SQLite implementation of the application persistence boundary."""

    def __init__(self, database_path: Path | str) -> None:
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS login_sessions (
                token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL,
                complaint_status TEXT NOT NULL, handoff_status TEXT NOT NULL,
                consent TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL,
                content TEXT NOT NULL, response_json TEXT, created_at INTEGER NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS decision_traces (
                trace_id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL, conversation_id TEXT, user_id INTEGER,
                created_at INTEGER NOT NULL, mode TEXT NOT NULL, scenario_id TEXT,
                user_text_hash TEXT NOT NULL, modules_json TEXT NOT NULL,
                intent TEXT, intent_confidence REAL, risk_level TEXT NOT NULL,
                complaint_status_before TEXT NOT NULL, complaint_status_after TEXT NOT NULL,
                handoff_status_before TEXT NOT NULL, handoff_status_after TEXT NOT NULL,
                action TEXT, reason_code TEXT, retrieved_document_ids_json TEXT NOT NULL,
                recommendation_count INTEGER NOT NULL, state_patch_json TEXT NOT NULL,
                result_status TEXT NOT NULL, technical_error_module TEXT,
                technical_error_code TEXT, duration_ms INTEGER NOT NULL
            );
            """
        )
        self._migrate_conversations_version()
        self.connection.commit()

    def _migrate_conversations_version(self) -> None:
        """Add optimistic-locking support to local databases created before it existed."""
        columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(conversations)")}
        if "version" not in columns:
            self.connection.execute("ALTER TABLE conversations ADD COLUMN version INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _password_hash(password: str, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return f"{salt.hex()}${digest.hex()}"

    @classmethod
    def _verify_password(cls, password: str, encoded: str) -> bool:
        salt_hex, expected = encoded.split("$", 1)
        actual = cls._password_hash(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return secrets.compare_digest(actual, expected)

    @staticmethod
    def _validate_credentials(username: str, password: str) -> None:
        if not isinstance(username, str) or not isinstance(password, str):
            raise StoreError("username_and_password_must_be_strings")
        if not USERNAME_PATTERN.fullmatch(username):
            raise StoreError("username_must_be_3_to_64_safe_characters")
        if len(password) < 6:
            raise StoreError("password_must_be_at_least_6_characters")

    def register(self, username: str, password: str) -> dict[str, object]:
        self._validate_credentials(username, password)
        try:
            cursor = self.connection.execute(
                "INSERT INTO users(username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, self._password_hash(password), int(time.time())),
            )
        except sqlite3.IntegrityError as error:
            raise StoreError("username_already_exists") from error
        self.connection.commit()
        return {"id": cursor.lastrowid, "username": username}

    def login(self, username: str, password: str) -> tuple[dict[str, object], str]:
        if not isinstance(username, str) or not isinstance(password, str):
            raise StoreError("invalid_credentials")
        row = self.connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row is None or not self._verify_password(password, row["password_hash"]):
            raise StoreError("invalid_credentials")
        token = secrets.token_urlsafe(32)
        self.connection.execute(
            "INSERT INTO login_sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (hashlib.sha256(token.encode()).hexdigest(), row["id"], int(time.time()) + SESSION_LIFETIME_SECONDS),
        )
        self.connection.commit()
        return {"id": row["id"], "username": row["username"]}, token

    def logout(self, token: str | None) -> None:
        if token:
            self.connection.execute("DELETE FROM login_sessions WHERE token_hash = ?", (hashlib.sha256(token.encode()).hexdigest(),))
            self.connection.commit()

    def current_user(self, token: str | None) -> dict[str, object] | None:
        if not token:
            return None
        row = self.connection.execute(
            """SELECT users.id, users.username FROM login_sessions JOIN users ON users.id = login_sessions.user_id
               WHERE token_hash = ? AND expires_at > ?""",
            (hashlib.sha256(token.encode()).hexdigest(), int(time.time())),
        ).fetchone()
        return dict(row) if row else None

    def create_conversation(self, user_id: int, title: str, initial_state: dict[str, str]) -> dict[str, object]:
        now, conversation_id = int(time.time()), str(uuid4())
        self.connection.execute(
            """INSERT INTO conversations(id, user_id, title, complaint_status, handoff_status, consent, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (conversation_id, user_id, title, initial_state["complaint_status"], initial_state["handoff_status"], initial_state["consent"], now, now),
        )
        self.connection.commit()
        return self.get_conversation(user_id, conversation_id)

    def list_conversations(self, user_id: int) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC, created_at DESC", (user_id,)
        ).fetchall()
        return [self._conversation_summary(row) for row in rows]

    def get_conversation(self, user_id: int, conversation_id: str) -> dict[str, object]:
        row = self.connection.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)).fetchone()
        if row is None:
            raise StoreError("conversation_not_found")
        result = self._conversation_summary(row)
        messages = self.connection.execute(
            "SELECT role, content, response_json, created_at FROM messages WHERE conversation_id = ? ORDER BY id", (conversation_id,)
        ).fetchall()
        result["messages"] = [
            {"role": item["role"], "content": item["content"], "response": item["response_json"] and json.loads(item["response_json"]), "created_at": item["created_at"]}
            for item in messages
        ]
        return result

    @staticmethod
    def _conversation_summary(row: sqlite3.Row) -> dict[str, object]:
        return {
            key: row[key]
            for key in ("id", "title", "complaint_status", "handoff_status", "consent", "version", "created_at", "updated_at")
        }

    def add_turn(
        self,
        user_id: int,
        conversation_id: str,
        user_text: str,
        public_response: dict[str, object],
        final_state: dict[str, object],
        expected_version: int,
    ) -> dict[str, object]:
        """Atomically persist one successful turn if the caller has a current snapshot."""
        self.get_conversation(user_id, conversation_id)
        if public_response["status"] != "ok":
            raise StoreError("agent_response_not_persisted")
        if isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 0:
            raise StoreError("expected_version_must_be_non_negative_integer")
        now = int(time.time())
        with self.connection:
            updated = self.connection.execute(
                """UPDATE conversations
                   SET complaint_status = ?, handoff_status = ?, consent = ?, updated_at = ?, version = version + 1
                   WHERE id = ? AND user_id = ? AND version = ?""",
                (
                    final_state["complaint_status"], final_state["handoff_status"], final_state["consent"],
                    now, conversation_id, user_id, expected_version,
                ),
            )
            if updated.rowcount != 1:
                raise StoreError("conversation_version_conflict")
            self.connection.execute(
                "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
                (conversation_id, user_text, now),
            )
            self.connection.execute(
                "INSERT INTO messages(conversation_id, role, content, response_json, created_at) VALUES (?, 'assistant', ?, ?, ?)",
                (conversation_id, public_response["message"]["text"], json.dumps(public_response), now),
            )
        return self.get_conversation(user_id, conversation_id)

    def record_trace(self, trace: DecisionTrace) -> None:
        """Persist a sanitised trace. Failures are isolated by the orchestrator."""
        self.connection.execute(
            """INSERT INTO decision_traces(
                trace_id, request_id, session_id, conversation_id, user_id, created_at,
                mode, scenario_id, user_text_hash, modules_json, intent,
                intent_confidence, risk_level, complaint_status_before,
                complaint_status_after, handoff_status_before, handoff_status_after,
                action, reason_code, retrieved_document_ids_json, recommendation_count,
                state_patch_json, result_status, technical_error_module,
                technical_error_code, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace.trace_id, trace.request_id, trace.session_id,
                trace.context.conversation_id, trace.context.user_id, trace.created_at,
                trace.context.mode, trace.context.scenario_id, trace.user_text_hash,
                json.dumps([outcome.__dict__ for outcome in trace.modules]), trace.intent,
                trace.intent_confidence, trace.risk_level, trace.complaint_status_before,
                trace.complaint_status_after, trace.handoff_status_before,
                trace.handoff_status_after, trace.action, trace.reason_code,
                json.dumps(trace.retrieved_document_ids), trace.recommendation_count,
                json.dumps(trace.state_patch), trace.result_status,
                trace.technical_error_module, trace.technical_error_code, trace.duration_ms,
            ),
        )
        self.connection.commit()

    def list_traces(self, user_id: int, conversation_id: str) -> list[dict[str, object]]:
        """Return sanitized, developer-facing traces for a caller-owned conversation."""
        self.get_conversation(user_id, conversation_id)
        rows = self.connection.execute(
            "SELECT * FROM decision_traces WHERE conversation_id = ? AND user_id = ? ORDER BY created_at, rowid",
            (conversation_id, user_id),
        ).fetchall()
        return [
            {
                "trace_id": row["trace_id"], "request_id": row["request_id"],
                "created_at": row["created_at"], "mode": row["mode"],
                "scenario_id": row["scenario_id"], "modules": json.loads(row["modules_json"]),
                "intent": row["intent"], "intent_confidence": row["intent_confidence"],
                "risk_level": row["risk_level"],
                "complaint_status_before": row["complaint_status_before"],
                "complaint_status_after": row["complaint_status_after"],
                "handoff_status_before": row["handoff_status_before"],
                "handoff_status_after": row["handoff_status_after"],
                "action": row["action"], "reason_code": row["reason_code"],
                "retrieved_document_ids": json.loads(row["retrieved_document_ids_json"]),
                "recommendation_count": row["recommendation_count"],
                "state_patch": json.loads(row["state_patch_json"]),
                "result_status": row["result_status"],
                "technical_error_module": row["technical_error_module"],
                "technical_error_code": row["technical_error_code"],
                "duration_ms": row["duration_ms"],
            }
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()


class InMemoryStore(SQLiteStore):
    """Ephemeral repository implementation for application tests."""

    def __init__(self) -> None:
        super().__init__(":memory:")
