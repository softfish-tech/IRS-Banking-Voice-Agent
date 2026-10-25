"""Approved evidence integrity, split isolation and metric behavior."""
import json
from pathlib import Path
import unittest

from banking_agent.modules.rag.evaluate_retrieval import calculate_metrics, load_validated_data


class RetrievalEvalTests(unittest.TestCase):
    def setUp(self):
        self.rag = Path(__file__).resolve().parents[2]

    def test_approved_data_and_provenance(self):
        data, manifest = load_validated_data(self.rag)
        self.assertEqual((len(data['dev']), len(data['test'])), (76, 32))
        self.assertEqual(manifest['reviewed_by'], '当前用户（不记录姓名）')
        self.assertEqual(manifest['reviewed_on'], '2026-10-14')
        self.assertTrue(all(not r['leakage_flags'] for r in data['test']))
        self.assertEqual(len({i for rows in data.values() for r in rows for i in r['target_intents']}), 77)

    @staticmethod
    def row(qid, kind='supported', gold=None, status='approved'):
        return {'question_id': qid, 'case_type': kind, 'gold_chunk_ids': gold or [],
                'gold_policy_ids': ['P'] if gold else [], 'multi_chunk': len(gold or []) > 1,
                'human_review_status': status, 'evaluation_status': 'ready'}

    def test_partial_hit_does_not_satisfy_all_required_evidence(self):
        row = self.row('q', gold=['A', 'B'])
        predictions = {'q': {'status': 'ok', 'data': {'docs': [{'document_id': 'A'}, {'document_id': 'B'}]}}}
        result = calculate_metrics([row], predictions)['evidence_cases']
        self.assertEqual(result['recall_at_1'], .5)
        self.assertEqual(result['hit_at_1'], 1)
        self.assertEqual(result['all_gold_recall_at_1'], 0)
        self.assertEqual(result['all_gold_recall_at_3'], 1)
        self.assertEqual(result['mrr_at_5'], 1)

    def test_unapproved_and_policy_conflicts_are_excluded(self):
        pending = self.row('pending', gold=['A'], status='pending')
        blocked = self.row('blocked', gold=['A'])
        blocked['evaluation_status'] = 'blocked_policy_conflict'
        self.assertEqual(calculate_metrics([pending, blocked], {})['evaluated_questions'], 0)

    def test_no_evidence_and_technical_failure_are_separate(self):
        rows = [self.row(q, kind='no_evidence') for q in ('empty', 'false', 'error')]
        predictions = {'empty': {'status': 'empty', 'data': {'docs': []}},
                       'false': {'status': 'ok', 'data': {'docs': [{'document_id': 'irrelevant'}]}},
                       'error': {'status': 'error', 'data': {'docs': []}}}
        result = calculate_metrics(rows, predictions)
        self.assertIsNone(result['evidence_cases']['recall_at_5'])
        self.assertEqual(result['false_positive_retrieval_rate'], .5)
        self.assertEqual(result['technical_errors'], 1)

    def test_missing_and_duplicate_predictions_fail(self):
        row = self.row('q', gold=['A'])
        with self.assertRaises(ValueError):
            calculate_metrics([row], {})
        with self.assertRaises(ValueError):
            calculate_metrics([row], {'q': {'status': 'ok', 'data': {'docs': [{'document_id': 'A'}, {'document_id': 'A'}]}}})


if __name__ == '__main__':
    unittest.main()
