"""Public retrieval contract, independent of orchestration and rule decisions."""

import json
import tempfile
import unittest
from pathlib import Path

from banking_agent.modules.rag import MockRetriever, retrieve
from banking_agent.modules.rag.retriever import DEFAULT_CHUNKS, REPLACEMENT_CHUNK


class RetrievalInterfaceTests(unittest.TestCase):
    def test_s01_returns_exact_policy_evidence(self):
        result = retrieve("What is the replacement fee for my card?", top_k=3)
        self.assertEqual(set(result), {"status", "data"})
        self.assertEqual(result["status"], "ok")
        doc = result["data"]["docs"][0]
        self.assertEqual(set(doc), {"document_id", "title", "source", "score", "excerpt"})
        source = next(json.loads(line) for line in DEFAULT_CHUNKS.read_text().splitlines()
                      if json.loads(line)["chunk_id"] == REPLACEMENT_CHUNK)
        self.assertEqual(doc["excerpt"], source["content"])
        self.assertIn(source["source_policy_id"], doc["source"])
        json.dumps(result)

    def test_s08_and_unknown_queries_are_empty(self):
        for query in ("What is the bank policy for crypto wallet recovery?", "unmapped question"):
            self.assertEqual(MockRetriever().retrieve(query), {"status": "empty", "data": {"docs": []}})

    def test_normalisation_limit_and_result_isolation(self):
        backend = MockRetriever()
        first = backend.retrieve("  WHAT is the replacement fee   for my card?  ", 1)
        self.assertEqual(len(first["data"]["docs"]), 1)
        first["data"]["docs"][0]["excerpt"] = "modified"
        self.assertNotEqual(backend.retrieve("What is the replacement fee for my card?")["data"]["docs"][0]["excerpt"], "modified")

    def test_invalid_inputs_raise(self):
        for query in ("", "  ", None, 42):
            with self.assertRaises(ValueError):
                MockRetriever().retrieve(query)
        for top_k in (0, -1, True, "3", 1.5):
            with self.assertRaises(ValueError):
                MockRetriever().retrieve("known query", top_k)

    def test_missing_corrupt_duplicate_and_inactive_evidence_are_errors(self):
        original = next(json.loads(line) for line in DEFAULT_CHUNKS.read_text().splitlines()
                        if json.loads(line)["chunk_id"] == REPLACEMENT_CHUNK)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chunks.jsonl"
            self.assertEqual(MockRetriever(path).retrieve("What is the replacement fee for my card?")["status"], "error")
            for content in ("not json", "{}", json.dumps(original) + "\n" + json.dumps(original),
                            json.dumps(dict(original, status="inactive")),
                            json.dumps(dict(original, content=""))):
                path.write_text(content)
                result = MockRetriever(path).retrieve("What is the replacement fee for my card?")
                self.assertEqual(result, {"status": "error", "data": {"docs": []}})


if __name__ == "__main__":
    unittest.main()
