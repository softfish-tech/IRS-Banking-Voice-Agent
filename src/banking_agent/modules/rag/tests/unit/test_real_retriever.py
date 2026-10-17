"""Integration of cached candidate retrieval, ranking and public startup entry."""
from pathlib import Path
from unittest.mock import Mock, patch
import unittest
from banking_agent.modules.rag import create_retriever, configure_retriever, retrieve
from banking_agent.modules.rag.real_retriever import RealRetriever


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
