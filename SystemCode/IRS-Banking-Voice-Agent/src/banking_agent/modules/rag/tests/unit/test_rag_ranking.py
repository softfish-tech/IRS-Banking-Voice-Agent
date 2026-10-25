"""Optimized ranking must retain original evidence and initialization guarantees."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from banking_agent.modules.rag.bm25_retriever import BM25Retriever

RAG = Path(__file__).resolve().parents[2]


class RankingTests(unittest.TestCase):
    def test_normalization_retains_negation_numbers_and_units(self):
        backend = BM25Retriever(str(RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'), normalize=True)
        tokens = backend._tokenize('My cards are not charged 15.50 SGD and never free')
        for token in ('card', 'not', 'charge', '15.50', 'sgd', 'never', 'free'):
            self.assertIn(token, tokens)
        self.assertNotIn('my', tokens)
        self.assertEqual(backend.retrieve('the and my')['status'], 'empty')

    def test_optimized_path_is_cached_and_preserves_evidence(self):
        corpus = RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'
        originals = {r['chunk_id']: r for r in map(json.loads, corpus.read_text().splitlines())}
        backend = BM25Retriever(str(corpus), normalize=True, title_weight=1.0,
                                faq_weight=0.5, faq_path=str(RAG / 'chunks/NovaBank_faq_chunk_mapping_v1_1.jsonl'))
        with patch.object(Path, 'read_text', side_effect=AssertionError('read during query')), \
             patch('banking_agent.modules.rag.bm25_retriever.BM25Okapi', side_effect=AssertionError('rebuild')):
            docs = backend.retrieve('lost card replacement fees', 5)['data']['docs']
        self.assertEqual(len(docs), 5)
        self.assertEqual([d['score'] for d in docs], sorted((d['score'] for d in docs), reverse=True))
        for doc in docs:
            self.assertEqual(doc['excerpt'], originals[doc['document_id']]['content'])
        with patch.object(backend._faq_index, 'get_scores', side_effect=RuntimeError('failed')):
            self.assertEqual(backend.retrieve('card')['status'], 'error')

    def test_weights_are_validated(self):
        for config in ({'title_weight': -1}, {'faq_weight': 1}, {'coverage_weight': float('nan')}):
            with self.assertRaises(ValueError):
                BM25Retriever('unused', **config)

    def test_coverage_is_deterministic_and_bounded(self):
        backend = BM25Retriever(str(RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'), coverage_weight=1)
        result = backend.retrieve('replacement card delivery fees', 3)
        self.assertEqual(result, backend.retrieve('replacement card delivery fees', 3))
        docs = result['data']['docs']
        self.assertEqual(len(docs), 3)
        self.assertEqual(len({d['document_id'] for d in docs}), 3)
