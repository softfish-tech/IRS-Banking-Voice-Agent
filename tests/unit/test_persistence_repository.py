"""Application persistence implementations conform to the storage boundary."""

import unittest

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
