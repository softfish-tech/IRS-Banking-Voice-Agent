"""Integration of cached candidate retrieval, ranking and public startup entry."""
from pathlib import Path
from unittest.mock import Mock, patch
import unittest
from banking_agent.modules.rag import create_retriever, configure_retriever, retrieve
from banking_agent.modules.rag.real_retriever import RealRetriever, _expand_replacement_fee_query


class RealRetrieverTests(unittest.TestCase):
    def tearDown(self):
        configure_retriever('mock')

    def test_public_startup_initializes_once_and_preserves_full_evidence(self):
        reranker=Mock()
        reranker.rerank.side_effect=lambda q,docs,k: [dict(d,score=float(len(docs)-i)) for i,d in enumerate(docs[:k])]
        backend=configure_retriever('real',reranker=reranker)
        with patch.object(Path,'read_text',side_effect=AssertionError('reread')), \
             patch.object(Path,'read_bytes',side_effect=AssertionError('reread')):
            first=retrieve('lost card replacement fees',3)
            self.assertEqual(first,retrieve('lost card replacement fees',3))
        self.assertEqual(len(reranker.rerank.call_args.args[1]),20)
        originals={d['document_id']:d for d in backend._backend.evidence_documents()}
        for d in first['data']['docs']:
            self.assertEqual(d['excerpt'],originals[d['document_id']]['excerpt'])
            self.assertEqual(set(d),{'document_id','title','source','score','excerpt'})

    def test_empty_error_and_invalid_are_distinct(self):
        ranker=Mock()
        backend=RealRetriever(reranker=ranker)
        self.assertEqual(backend.retrieve('xylophonicallyxyz')['status'],'empty')
        ranker.rerank.assert_not_called()
        ranker.rerank.side_effect=RuntimeError('failed')
        self.assertEqual(backend.retrieve('card'),{'status':'error','data':{'docs':[]}})
        for q,k in [('',5),(None,5),('card',True),('card',0)]:
            self.assertEqual(backend.retrieve(q,k), {'status':'error','data':{'docs':[]}})
        with patch.object(backend._backend,'retrieve',return_value={'status':'error','data':{'docs':[]}}):
            self.assertEqual(backend.retrieve('card')['status'],'error')

    def test_initialization_failure_does_not_replace_default(self):
        with self.assertRaises(OSError):configure_retriever('real',jsonl_path='/missing/corpus.jsonl')
        self.assertEqual(retrieve('What is the replacement fee for my card?')['status'],'ok')
        with self.assertRaises(ValueError):create_retriever('unknown')

    def test_replacement_fee_wording_is_normalised_before_ranking(self):
        self.assertEqual(
            _expand_replacement_fee_query("Is there a charge to get a replacement debit card?"),
            "Is there a charge to get a replacement debit card?\nreplacement card fee",
        )
        self.assertEqual(
            _expand_replacement_fee_query("Do I pay anything when I replace my card?"),
            "Do I pay anything when I replace my card?\nreplacement card fee",
        )
        self.assertEqual(_expand_replacement_fee_query("When will my card arrive?"), "When will my card arrive?")
        self.assertEqual(
            _expand_replacement_fee_query("how much to replace my card lol"),
            "how much to replace my card lol\nreplacement card fee",
        )
        self.assertEqual(
            _expand_replacement_fee_query("card replcement fee?"),
            "card replcement fee?\nreplacement card fee",
        )

    def test_crypto_wallet_recovery_uses_only_unsupported_service_expansion(self):
        self.assertEqual(
            _expand_replacement_fee_query("Can NovaBank recover my cryptocurrency wallet?"),
            "Can NovaBank recover my cryptocurrency wallet?\ncryptocurrency unsupported",
        )
        self.assertEqual(
            _expand_replacement_fee_query("How do I add a wallet token?"),
            "How do I add a wallet token?",
        )
        self.assertEqual(
            _expand_replacement_fee_query("Does the bank support recovering crypto wallets?"),
            "Does the bank support recovering crypto wallets?\ncryptocurrency unsupported",
        )

    def test_crypto_wallet_recovery_promotes_reviewed_boundary_policy_for_reranking(self):
        ranker = Mock()
        ranker.rerank.side_effect = lambda query, candidates, top_k: candidates[:top_k]
        backend = RealRetriever(reranker=ranker)

        result = backend.retrieve("Can NovaBank recover my cryptocurrency wallet?", 3)

        self.assertEqual(result["data"]["docs"][0]["document_id"], "NB-v1_1-fiat_currency_support-001")
        self.assertEqual(ranker.rerank.call_args.args[1][0]["document_id"], "NB-v1_1-fiat_currency_support-001")

    def test_crypto_wallet_recovery_retains_boundary_after_reranking(self):
        ranker = Mock()
        ranker.rerank.side_effect = lambda query, candidates, top_k: candidates[1:top_k + 1]
        backend = RealRetriever(reranker=ranker)

        result = backend.retrieve("Can NovaBank recover my cryptocurrency wallet?", 3)

        self.assertEqual(result["data"]["docs"][0]["document_id"], "NB-v1_1-fiat_currency_support-001")
