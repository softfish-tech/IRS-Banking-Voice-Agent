"""Fixed-rule confirmation must not score unapproved questions or tune thresholds."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from banking_agent.modules.rag.evaluate_retrieval import (
    apply_fixed_minus6_gate, load_gate_confirmation, run_gate_confirmation,
)

RAG=Path(__file__).resolve().parents[2]


class GateConfirmationTests(unittest.TestCase):
    @staticmethod
    def result(score):
        return {'status':'ok','data':{'docs':[{'document_id':'a','title':'title','source':'P v1',
                                                'score':score,'excerpt':'full evidence'}]}}

    def test_fixed_boundary_and_complete_list_retention(self):
        self.assertEqual(apply_fixed_minus6_gate(self.result(-6.01))['status'],'empty')
        result=self.result(-6.)
        result['data']['docs'].append(dict(result['data']['docs'][0],document_id='b',score=-15.))
        self.assertEqual(apply_fixed_minus6_gate(result),result)
        self.assertEqual(len(result['data']['docs']),2)
        for status in ('empty','error'):
            self.assertEqual(apply_fixed_minus6_gate({'status':status,'data':{'docs':[]}})['status'],status)

    def test_dataset_is_reviewable_and_has_required_strata(self):
        rows,manifest=load_gate_confirmation(RAG,require_approved=False)
        self.assertEqual(len(rows),32)
        self.assertEqual(sum(r['multi_chunk'] for r in rows),2)
        self.assertEqual({k:sum(r['stratum']==k for r in rows) for k in manifest['strata']},manifest['strata'])
        self.assertTrue(all(r['context_evidence'] for r in rows))

    def test_no_model_is_called_before_human_approval(self):
        rows,_=load_gate_confirmation(RAG,require_approved=False)
        if all(r['human_review_status']=='approved' for r in rows):
            self.skipTest('Approval has since been recorded; pending guard tested via injection')
        with TemporaryDirectory() as tmp,patch('banking_agent.modules.rag.real_retriever.RealRetriever') as constructor:
            target=Path(tmp)/'results'
            with self.assertRaisesRegex(ValueError,'Human approval'):
                run_gate_confirmation(RAG,target)
            constructor.assert_not_called()
            self.assertFalse(target.exists())
