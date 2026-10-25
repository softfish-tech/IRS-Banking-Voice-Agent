"""Contract, strict loading and cached-index behavior for real BM25."""
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from banking_agent.modules.rag.bm25_retriever import BM25Retriever, ChunkValidationError


class BM25RetrieverTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "chunks.jsonl"
        self.rows = [self.row("card", "lost card replacement", "Complete card evidence.\n" + "Details. " * 200),
                     self.row("transfer", "domestic transfer", "Domestic transfers are free."),
                     self.row("analysis", "lost card replacement", "Untrusted analysis.", "analysis")]

    @staticmethod
    def row(identifier, title, content, source_type="Category Master Policy"):
        return dict(chunk_id=identifier, title=title, content=content,
                    source_type=source_type, source_policy_id="DOC-001", source_policy_version="1.1")

    def build(self, rows=None):
        self.path.write_text("".join(json.dumps(row) + "\n" for row in (self.rows if rows is None else rows)), encoding="utf-8")
        return BM25Retriever(str(self.path))

    def test_contract_filter_ranking_full_excerpt_and_cached_index(self):
        retriever = self.build()
        self.path.unlink()
        with patch("banking_agent.modules.rag.bm25_retriever.BM25Okapi", side_effect=AssertionError("rebuilt")):
            result = retriever.retrieve("LOST card replacement!", 99)
            self.assertEqual(result, retriever.retrieve("LOST card replacement!", 99))
        self.assertEqual(set(result), {"status", "data"})
        self.assertEqual(set(result["data"]), {"docs"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual([d["document_id"] for d in result["data"]["docs"]], ["card"])
        doc = result["data"]["docs"][0]
        self.assertEqual(set(doc), {"document_id", "title", "source", "score", "excerpt"})
        self.assertEqual(doc["excerpt"], self.rows[0]["content"])
        self.assertIsInstance(doc["score"], float)
        self.assertIn("DOC-001 | v1.1", doc["source"])

    def test_invalid_queries_and_top_k(self):
        retriever = self.build()
        for query, k in [("", 5), ("   ", 5), (None, 5), ("!!!", 5), ("card", 0), ("card", -1), ("card", True), ("card", 1.5)]:
            with self.subTest(query=query, k=k), self.assertRaises(ValueError):
                retriever.retrieve(query, k)

    def test_empty_unknown_and_fully_filtered(self):
        for rows in ([], [self.rows[2]]):
            self.assertEqual(self.build(rows).retrieve("card"), {"status": "empty", "data": {"docs": []}})
        self.assertEqual(self.build().retrieve("nebula" )["status"], "empty")

    def test_invalid_records_and_duplicates(self):
        for key in ("chunk_id", "title", "content", "source_type", "source_policy_id", "source_policy_version"):
            row = self.rows[0].copy()
            del row[key]
            with self.subTest(key=key), self.assertRaisesRegex(ChunkValidationError, ":1:"):
                self.build([row])
        with self.assertRaisesRegex(ChunkValidationError, "duplicate"):
            self.build([self.rows[0], self.rows[0]])
        for text in ('{bad}\n', '[]\n'):
            self.path.write_text(text)
            with self.assertRaises(ChunkValidationError):
                BM25Retriever(str(self.path))
        self.path.write_bytes(b'\xff')
        with self.assertRaisesRegex(ChunkValidationError, "UTF-8"):
            BM25Retriever(str(self.path))

    def test_excerpt_alias_single_document_and_sorting(self):
        row = self.rows[0].copy()
        row["excerpt"] = row.pop("content")
        retriever = self.build([row])
        self.assertEqual(retriever.retrieve("replacement")["status"], "ok")
        retriever = self.build()
        result = retriever.retrieve("card transfer", 2)["data"]["docs"]
        self.assertEqual(len(result), 2)
        self.assertEqual([d["score"] for d in result], sorted([d["score"] for d in result], reverse=True))
        self.assertEqual(len(retriever.retrieve("card transfer", 1)["data"]["docs"]), 1)

    def test_scoring_failure_is_error(self):
        retriever = self.build()
        with patch.object(retriever._index, "get_scores", side_effect=RuntimeError("failure")):
            self.assertEqual(retriever.retrieve("card"), {"status": "error", "data": {"docs": []}})

    def test_real_corpus_loads_with_policy_source_types_and_full_evidence(self):
        """Exercise the actual generated corpus, not only synthetic fixtures."""
        rag = Path(__file__).resolve().parents[2]
        path = rag / "chunks/NovaBank_knowledge_chunks_v1_1.jsonl"
        chunks = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(chunks), 151)
        for chunk in chunks:
            policy = (rag / chunk["source_document"]).read_text()
            frontmatter = policy.split("---", 2)[1]
            source_type = re.search(r"^source_type: (.+)$", frontmatter, re.MULTILINE)
            self.assertIsNotNone(source_type)
            self.assertEqual(chunk["source_type"], source_type.group(1).strip())
        retriever = BM25Retriever(str(path))
        self.assertEqual(len(retriever._documents), len(chunks))
        result = retriever.retrieve("lost card replacement fees", 5)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["data"]["docs"]), 5)
        by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
        for doc in result["data"]["docs"]:
            chunk = by_id[doc["document_id"]]
            self.assertEqual(doc["excerpt"], chunk["content"])
            self.assertEqual(doc["source"], f"{chunk['source_policy_id']} | v{chunk['source_policy_version']} | {chunk['source_type']}")
        report = json.loads((rag / "chunks/validation_report_v1_1.json").read_text())
        self.assertTrue(report["checks"]["source_type_matches_policy_metadata"])


if __name__ == "__main__":
    unittest.main()
