"""Regression checks for refund cap semantics and complete timing conditions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[6]
RAG = ROOT / 'src/banking_agent/modules/rag'
PACK = RAG / 'novabank_category_master_policies_enriched_v1_1'

class KnowledgeQualityFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunks = [json.loads(l) for l in (RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_text().splitlines()]
        cls.byid = {c['chunk_id']: c for c in cls.chunks}
        cls.faq = (RAG / 'faqs/NovaBank_BANKING77_FAQs_v1_1.md').read_text()
        cls.drafts = (RAG / 'chunk_sources/knowledge_chunk_drafts_v1_1.txt').read_text()

    def test_refund_caps_have_different_bases(self):
        policy = (PACK / 'policies/NovaBank_refunds_master_policy.md').read_text()
        chunk = self.byid['NB-v1_1-request_refund-004']['content']
        for text in [policy, chunk, self.drafts, self.faq]:
            self.assertIn('Aggregate credited refunds', text)
            self.assertIn('cannot exceed the original settled principal.', text)
            self.assertNotIn('Aggregate principal recovery cannot exceed the original settled principal less prior credits', text)
            self.assertNotIn('Total NovaBank refund recovery cannot exceed the original settled principal less prior credited refunds', text)
        self.assertIn('Additional NovaBank refund recovery', chunk)
        self.assertIn('less prior credited refunds', chunk)
        self.assertIn('merchant credits and bank-approved principal corrections', chunk)

    def test_all_delivery_cutoff_contexts_include_nonbusiness_branch(self):
        affected = [c for c in self.chunks if 'Delivery Day 0 is processing acceptance by 14:00' in c['content']]
        self.assertEqual(len(affected), 7)
        for chunk in affected:
            self.assertIn('later or non-business-day acceptance uses the next business day', chunk['content'], chunk['chunk_id'])
        self.assertIn('later or non-business-day acceptance uses the next business day', (RAG / 'build_knowledge_chunks.py').read_text())

    def test_identity_notification_starts_intake_not_review(self):
        policy = (PACK / 'policies/NovaBank_identity_verification_master_policy.md').read_text()
        chunk = self.byid['NB-v1_1-unable_to_verify_identity-002']['content']
        for text in [policy, chunk, self.drafts, self.faq]:
            self.assertIn('within 30 calendar days after', text)
            self.assertIn('notified', text) if text != self.faq else self.assertIn('after notification', text)
            self.assertIn('registered contact channel', text)
            self.assertIn('5 business days after complete evidence', text)
        self.assertIn('Internal recording or additional uploads do not start or restart', chunk)
        self.assertIn('one staff reconsideration', chunk)

    def test_default_rebuild_preserves_ids_and_updates_source_hashes(self):
        self.assertEqual(len(self.chunks), 151)
        self.assertEqual(len(self.byid), 151)
        self.assertEqual(len({c['intent'] for c in self.chunks}), 77)
        self.assertEqual(self.faq.count('FAQ ID: '), 231)
        manifest = json.loads((PACK / 'manifest.json').read_text())
        for record in manifest['policies']:
            self.assertEqual(record['sha256'], hashlib.sha256((PACK / record['path']).read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory() as target:
            subprocess.run([sys.executable, str(RAG / 'build_knowledge_chunks.py'), '--output-dir', target], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertEqual((Path(target) / 'NovaBank_knowledge_chunks_v1_1.jsonl').read_bytes(), (RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_bytes())

if __name__ == '__main__':
    unittest.main()
