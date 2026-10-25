"""E's async bridge must preserve B's public retrieval contract."""

import unittest

from banking_agent.app.retrieval_adapter import AsyncRetrievalAdapter
from banking_agent.modules.rag.real_retriever import RealRetriever
from banking_agent.modules.rag.retriever import MockRetriever
from helpers.adapter_contracts import assert_retrieval_adapter_contract


class BrokenRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        raise RuntimeError("backend detail must not escape")


class DeterministicReranker:
    """Avoid a local model dependency while exercising B's real BM25 backend."""

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        return [dict(document, score=float(top_k - index)) for index, document in enumerate(candidates[:top_k])]


class AsyncRetrievalAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_bridges_the_real_mock_retriever_to_e_async_contract(self) -> None:
        adapter = AsyncRetrievalAdapter(MockRetriever())

        result = await assert_retrieval_adapter_contract(
            adapter, "What is the replacement fee for my card?", top_k=3
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data.docs[0].document_id, "NB-v1_1-lost_or_stolen_card-002")

    async def test_preserves_b_normal_empty_result(self) -> None:
        result = await assert_retrieval_adapter_contract(
            AsyncRetrievalAdapter(MockRetriever()), "What is the bank policy for crypto wallet recovery?"
        )

        self.assertEqual(result.status, "empty")
        self.assertEqual(result.data.docs, [])

    async def test_bridges_b_real_backend_with_the_delivered_corpus(self) -> None:
        adapter = AsyncRetrievalAdapter(RealRetriever(reranker=DeterministicReranker()))

        result = await assert_retrieval_adapter_contract(adapter, "lost card replacement fees", top_k=2)

        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.data.docs), 2)
        self.assertTrue(all(document.excerpt for document in result.data.docs))

    async def test_backend_exception_becomes_a_sanitized_error_envelope(self) -> None:
        result = await AsyncRetrievalAdapter(BrokenRetriever()).retrieve("synthetic query", 3)

        self.assertEqual(result, {"status": "error"})
