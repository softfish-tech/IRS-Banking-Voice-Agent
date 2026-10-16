"""Offline mathematical/contract tests; no model download or test-set retrieval."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from banking_agent.modules.rag.hybrid_retriever import HybridRetriever


class FakeEncoder:
    def __init__(self):
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append(list(texts))
        return np.array([[2., 0.] if 'card' in t.lower() else [0., 3.] for t in texts])


class HybridTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'corpus.jsonl'
        self.rows = [dict(chunk_id=cid, title=title, content=content, source_type=kind,
                          source_policy_id='P1', source_policy_version='1.1')
                     for cid, title, content, kind in (
                         ('a', 'Card', 'Full card evidence.\n' + 'detail ' * 300, 'FAQ'),
                         ('b', 'Transfer', 'Complete transfer evidence.', 'Category Master Policy'),
                         ('c', 'Card report', 'Excluded report', 'analysis'))]
        self.path.write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        self.encoder = FakeEncoder()
        self.backend = HybridRetriever(str(self.path), encoder=self.encoder, candidate_k=2)

    def test_cosine_full_evidence_and_cached_index(self):
        self.assertEqual(len(self.encoder.calls), 1)
        self.path.unlink()
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('reread')):
            docs = self.backend.retrieve_dense('card', 10)
        self.assertEqual([d['document_id'] for d in docs], ['a', 'b'])
        self.assertEqual([d['score'] for d in docs], [1.0, 0.0])
        self.assertEqual(docs[0]['excerpt'], self.rows[0]['content'])
        docs[0]['excerpt'] = 'mutated'
        self.assertEqual(self.backend.retrieve_dense('card')[0]['excerpt'], self.rows[0]['content'])
        self.assertEqual([len(c) for c in self.encoder.calls], [2, 1, 1])

    def test_rrf_uses_ranks_deduplicates_and_breaks_ties_by_id(self):
        docs = self.backend.retrieve_dense('card')
        reverse = [dict(docs[1], score=99999.), dict(docs[0], score=-999.)]
        with patch.object(self.backend, 'retrieve_bm25', return_value=docs), \
             patch.object(self.backend, 'retrieve_dense', return_value=reverse):
            merged = self.backend.retrieve_hybrid('card')
        self.assertEqual([d['document_id'] for d in merged], ['a', 'b'])
        for d in merged:
            self.assertAlmostEqual(d['score'], 1/61 + 1/62)
        with patch.object(self.backend, 'retrieve_bm25', return_value=[docs[0], docs[0]]), \
             patch.object(self.backend, 'retrieve_dense', return_value=[]):
            self.assertAlmostEqual(self.backend.retrieve_hybrid('card')[0]['score'], 1/61)

    def test_contract_and_errors(self):
        for mode in ('bm25', 'dense', 'hybrid'):
            result = self.backend.retrieve('card', mode=mode)
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(set(result['data']['docs'][0]), {'document_id','title','source','score','excerpt'})
        for query, k, mode in [('',5,'dense'), ('card',0,'hybrid'), ('card',True,'bm25'), ('card',5,[]), (None,5,'dense')]:
            self.assertEqual(self.backend.retrieve(query,k,mode), {'status':'error','data':{'docs':[]}})
        with patch.object(self.encoder, 'encode', return_value=np.array([[np.nan, 0.]])):
            self.assertEqual(self.backend.retrieve('card')['status'], 'error')
        with patch.object(self.backend._bm25, 'retrieve', return_value={'status':'error','data':{'docs':[]}}):
            self.assertEqual(self.backend.retrieve('card')['status'], 'error')

    def test_empty_and_bad_embeddings(self):
        self.path.write_text('')
        empty = HybridRetriever(str(self.path), encoder=self.encoder)
        for mode in ('bm25','dense','hybrid'):
            self.assertEqual(empty.retrieve('card', mode=mode)['status'], 'empty')
        for vectors in ([[0.,0.]], [[1.,0.,0.]], [[float('inf'),0.]]):
            with patch.object(self.encoder,'encode',return_value=vectors):
                self.assertEqual(self.backend.retrieve('card', mode='dense')['status'],'error')

    def test_real_corpus_uses_same_allowed_documents(self):
        rag = Path(__file__).resolve().parents[2]
        backend = HybridRetriever(str(rag/'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'), encoder=FakeEncoder())
        self.assertEqual(backend.index_metadata['documents'],151)
        self.assertEqual(backend.index_metadata['dimension'],2)
        self.assertEqual(len(backend.retrieve('card')['data']['docs']),5)
