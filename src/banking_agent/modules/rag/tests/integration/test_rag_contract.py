"""B/E boundary compatibility without implementing C's sufficiency decisions."""
import json
import unittest
from unittest.mock import Mock, patch

from banking_agent.modules.rag import configure_retriever, retrieve
from banking_agent.modules.rag.real_retriever import RealRetriever
from banking_agent.modules.rag.retriever import validate_result
from banking_agent.schemas.state import AgentState, RetrievedDocument


class RAGContractTests(unittest.TestCase):
    def tearDown(self):
        configure_retriever('mock')

    def test_public_entry_serializes_and_fits_canonical_state(self):
        ranker=Mock()
        ranker.rerank.side_effect=lambda q,docs,k: [dict(d,score=float(100-i)) for i,d in enumerate(docs[:k])]
        configure_retriever('real',reranker=ranker)
        result=retrieve('lost card replacement fees',3)
        self.assertEqual(result['status'],'ok')
        state=AgentState(session_id='integration',user_text='synthetic fixture',
                         retrieved_docs=[RetrievedDocument.model_validate(d) for d in result['data']['docs']])
        self.assertEqual(len(state.retrieved_docs),3)
        self.assertEqual(json.loads(json.dumps(result,allow_nan=False)),result)
        self.assertIsNone(state.decision)  # B does not decide ANSWER/ABSTAIN.

    def test_every_runtime_exception_is_error_at_public_boundary(self):
        with patch('banking_agent.modules.rag.retriever._default_retriever') as backend:
            for failure in (KeyError('bad'),TypeError('bad'),RuntimeError('bad')):
                backend.retrieve.side_effect=failure
                self.assertEqual(retrieve('synthetic query'),{'status':'error','data':{'docs':[]}})
        for query,k in [('',5),(None,5),('q',0),('q',True)]:
            self.assertEqual(retrieve(query,k)['status'],'error')

    def test_malformed_results_and_altered_evidence_fail_closed(self):
        for result in ({'status':'ok','data':{'docs':[]}},
                       {'status':'empty','data':{'docs':[]},'action':'ANSWER'},
                       {'status':'error','data':{'docs':[{}]}}):
            with self.assertRaises(ValueError): validate_result(result,5)
        ranker=Mock()
        ranker.rerank.side_effect=lambda q,docs,k: [dict(docs[0],excerpt='invented')]
        self.assertEqual(RealRetriever(reranker=ranker).retrieve('card')['status'],'error')
        ranker.rerank.side_effect=lambda q,docs,k: [dict(docs[0],score=float('nan'))]
        self.assertEqual(RealRetriever(reranker=ranker).retrieve('card')['status'],'error')
        ranker.rerank.side_effect=KeyError('bad')
        self.assertEqual(RealRetriever(reranker=ranker).retrieve('card')['status'],'error')

    def test_delivery_corpus_manifest_matches_active_evidence(self):
        import hashlib
        from pathlib import Path
        rag=Path(__file__).resolve().parents[2]
        manifest=json.loads((rag/'chunks/corpus_manifest.json').read_text())
        raw=(rag/'chunks'/manifest['corpus_file']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),manifest['corpus_sha256'])
        records=list(map(json.loads,raw.decode().splitlines()))
        self.assertEqual(len(records),151)
        self.assertEqual(len({r['chunk_id'] for r in records}),151)
        for row in records:
            self.assertTrue(all(isinstance(row.get(k),str) and row[k].strip() for k in manifest['required_fields']))
            self.assertIn(row['source_type'],('Category Master Policy','FAQ'))
