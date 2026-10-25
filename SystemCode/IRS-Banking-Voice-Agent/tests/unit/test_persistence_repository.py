"""Application persistence implementations conform to the storage boundary."""

import tempfile
import unittest
from pathlib import Path

from banking_agent.app.persistence import ApplicationStore, InMemoryStore, SQLiteStore


class PersistenceRepositoryTests(unittest.TestCase):
    def test_sqlite_and_in_memory_stores_match_the_application_protocol(self) -> None:
        in_memory = InMemoryStore()
        sqlite = SQLiteStore(":memory:")
        try:
            self.assertIsInstance(in_memory, ApplicationStore)
            self.assertIsInstance(sqlite, ApplicationStore)
        finally:
            in_memory.close()
            sqlite.close()

    def test_turn_commit_increments_version_and_rejects_stale_write_atomically(self) -> None:
        store = InMemoryStore()
        try:
            user = store.register("alice", "testpw", "session-001")
            conversation = store.create_conversation(
                int(user["id"]), "test", {"complaint_status": "NONE", "handoff_status": "NOT_REQUIRED", "consent": "UNKNOWN"}
            )
            response = {"status": "ok", "message": {"text": "safe response"}}
            state = {"complaint_status": "OPEN", "handoff_status": "ESCALATED", "consent": "UNKNOWN"}
            updated = store.add_turn(int(user["id"]), conversation["id"], "help", response, state, expected_version=0)
            self.assertEqual(updated["version"], 1)
            with self.assertRaisesRegex(ValueError, "conversation_version_conflict"):
                store.add_turn(int(user["id"]), conversation["id"], "help again", response, state, expected_version=0)
            current = store.get_conversation(int(user["id"]), conversation["id"])
            self.assertEqual(current["version"], 1)
            self.assertEqual([message["content"] for message in current["messages"]], ["help", "safe response"])
        finally:
            store.close()

    def test_existing_sqlite_database_is_migrated_with_version_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "legacy.sqlite3"
            legacy = SQLiteStore(path)
            user = legacy.register("alice", "testpw", "session-001")
            legacy.connection.execute("DROP TABLE conversations")
            legacy.connection.execute(
                """CREATE TABLE conversations (
                    id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL,
                    complaint_status TEXT NOT NULL, handoff_status TEXT NOT NULL,
                    consent TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
                )"""
            )
            legacy.connection.execute(
                """INSERT INTO conversations(
                    id, user_id, title, complaint_status, handoff_status, consent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("legacy-conversation", user["id"], "legacy", "NONE", "NOT_REQUIRED", "UNKNOWN", 1, 1),
            )
            legacy.connection.commit()
            legacy.close()

            migrated = SQLiteStore(path)
            try:
                columns = {row["name"] for row in migrated.connection.execute("PRAGMA table_info(conversations)")}
                self.assertIn("version", columns)
                conversation = migrated.get_conversation(int(user["id"]), "legacy-conversation")
                self.assertEqual(conversation["version"], 0)
            finally:
                migrated.close()

    def test_conversation_snapshots_the_account_profile(self) -> None:
        store = SQLiteStore(":memory:")
        try:
            user = store.register("alice", "testpw", "session-001")
            first = store.create_conversation(int(user["id"]), "one", {"complaint_status": "NONE", "handoff_status": "NOT_REQUIRED", "consent": "UNKNOWN"})
            store.connection.execute("UPDATE users SET synthetic_profile_key = ? WHERE id = ?", ("session-002", user["id"]))
            store.connection.commit()
            second = store.create_conversation(int(user["id"]), "two", {"complaint_status": "NONE", "handoff_status": "NOT_REQUIRED", "consent": "UNKNOWN"})
            self.assertEqual(store.conversation_profile_key(first["id"]), "session-001")
            self.assertEqual(store.conversation_profile_key(second["id"]), "session-002")
        finally:
            store.close()
