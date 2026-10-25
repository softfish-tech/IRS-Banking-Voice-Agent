"""Regression checks for B12–B15 and reproducible policy-derived artifacts."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[6]
RAG = ROOT / 'src/banking_agent/modules/rag'
PACK = RAG / 'novabank_category_master_policies_enriched_v1_1'


class PolicyClarificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunks = [json.loads(line) for line in (RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_text().splitlines()]
        cls.faqs = {}
        for block in (RAG / 'faqs/NovaBank_BANKING77_FAQs_v1_1.md').read_text().split('\n\n---\n\n'):
            lines = block.splitlines()
            key = next(line[8:] for line in lines if line.startswith('FAQ ID: '))
            cls.faqs[key] = json.loads(next(line[8:] for line in lines if line.startswith('Answer: ')))
        cls.drafts = (RAG / 'chunk_sources/knowledge_chunk_drafts_v1_1.txt').read_text()

    def policy_section(self, name, intent):
        text = (PACK / 'policies' / name).read_text()
        return re.search(r'^### ' + re.escape(intent) + r' — .*?\n(.*?)(?=^### |^## |\Z)', text, re.M | re.S).group(1)

    def chunks_for(self, intent):
        return ' '.join(c['content'] for c in self.chunks if c['intent'] == intent)

    def test_topup_clocks_are_distinct(self):
        policy = self.policy_section('NovaBank_card_top_ups_master_policy.md', 'pending_top_up')
        self.assertNotIn('72 hours from acceptance', policy)
        self.assertIn('72 hours from issuer authorisation', policy)
        for text in [self.faqs['FAQ-pending_top_up-003'], self.chunks_for('pending_top_up'), self.drafts]:
            self.assertIn('recorded issuer-authorisation timestamp', text)
            self.assertIn('1 business day', text)
            self.assertIn('5 business days', text)
        chunk = self.chunks_for('pending_top_up')
        self.assertIn('Ownership review does not restart', chunk)
        self.assertIn('not request initiation or NovaBank acceptance', chunk)

    def test_fee_posting_does_not_change_merchant_settlement_intake(self):
        policy = self.policy_section('NovaBank_card_payments_master_policy.md', 'card_payment_fee_charged')
        for text in [policy, self.faqs['FAQ-card_payment_fee_charged-003'], self.chunks_for('card_payment_fee_charged'), self.drafts]:
            self.assertIn('60 calendar days of the disputed fee posting', text)
        self.assertNotIn('fee error within 60 calendar days of settlement', policy)
        self.assertIn('60 calendar days of settlement', self.chunks_for('request_refund'))

    def test_atm_rate_posting_does_not_change_cash_reporting_intake(self):
        policy = self.policy_section('NovaBank_cash_withdrawals_master_policy.md', 'wrong_exchange_rate_for_cash_withdrawal')
        for text in [policy, self.faqs['FAQ-wrong_exchange_rate_for_cash_withdrawal-003'], self.chunks_for('wrong_exchange_rate_for_cash_withdrawal'), self.drafts]:
            self.assertIn('60 calendar days of the disputed withdrawal posting', text)
        self.assertNotIn('rate-calculation error within 60 calendar days of settlement', policy)
        self.assertIn('30 calendar days of withdrawal', self.chunks_for('wrong_amount_of_cash_received'))

    def test_atm_status_and_cash_routes_preserve_immediate_reporting(self):
        policy = self.policy_section('NovaBank_cash_withdrawals_master_policy.md', 'pending_cash_withdrawal')
        for text in [policy, self.faqs['FAQ-pending_cash_withdrawal-002'], self.chunks_for('pending_cash_withdrawal')]:
            self.assertIn('2 business days after complete evidence', text)
            self.assertIn('10 business days after complete evidence', text)
            self.assertIn('1 business day', text)
        self.assertIn('report a cash problem immediately even while pending', policy)
        self.assertIn('Report cash discrepancies immediately even while pending', self.chunks_for('pending_cash_withdrawal'))

    def test_default_builder_reproduces_artifact_and_closes_review_items(self):
        with tempfile.TemporaryDirectory() as target:
            subprocess.run([sys.executable, str(RAG / 'build_knowledge_chunks.py'), '--output-dir', target], cwd=ROOT, check=True, capture_output=True, text=True)
            built = Path(target) / 'NovaBank_knowledge_chunks_v1_1.jsonl'
            self.assertEqual(built.read_bytes(), (RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_bytes())
            report = json.loads((Path(target) / 'validation_report_v1_1.json').read_text())
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['source_issues_requiring_review'], [])
            self.assertEqual({x['review_id'] for x in report['resolved_source_issues']}, {'REVIEW-001', 'REVIEW-002', 'REVIEW-003', 'REVIEW-004'})
            self.assertEqual(report['output_file']['sha256'], hashlib.sha256(built.read_bytes()).hexdigest())
        self.assertEqual(len(self.faqs), 231)
        self.assertEqual(len({c['intent'] for c in self.chunks}), 77)
        self.assertEqual(len({c['chunk_id'] for c in self.chunks}), len(self.chunks))


if __name__ == '__main__':
    unittest.main()
