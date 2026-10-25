"""Expression preservation, source isolation and deterministic build regressions."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[6]
RAG = ROOT / 'src/banking_agent/modules/rag'
spec = importlib.util.spec_from_file_location('rag_builder', RAG / 'build_knowledge_chunks.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class FAQExpressionTests(unittest.TestCase):
    def setUp(self):
        self.text = (RAG / 'faqs/NovaBank_BANKING77_FAQs_v1_1.md').read_text()
        self.faqs = builder.parse_faqs(self.text)
        self.chunks = [json.loads(line) for line in (RAG / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_text().splitlines()]

    def test_preserves_every_primary_and_alternative_without_answer_evidence(self):
        self.assertEqual(len(self.faqs), 231)
        self.assertEqual(sum(len(f['alternatives']) for f in self.faqs), 693)
        self.assertEqual(sum(len(f['expressions']) for f in self.faqs), 924)
        self.assertTrue(all('answer' not in f for f in self.faqs))
        changed = '\n'.join('Answer: "UNSUPPORTED NEW FEE SGD 99999"' if line.startswith('Answer: ') else line for line in self.text.splitlines())
        self.assertEqual(builder.parse_faqs(changed), self.faqs)

    def test_invalid_alternative_and_duplicate_id_are_rejected(self):
        first = self.text.split('\n\n---\n\n')[0]
        self.assertRaises(ValueError, builder.parse_faqs, first + '\n\n---\n\n' + first)
        malformed = first.replace('- "', '- unquoted ', 1)
        self.assertRaises(ValueError, builder.parse_faqs, malformed)

    def test_candidates_stay_within_source_version_and_declared_intent(self):
        mappings = builder.build_faq_mapping(self.faqs, self.chunks, lambda s: set(s.lower().split()))
        by_id = {c['chunk_id']: c for c in self.chunks}
        self.assertTrue(all(m['candidate_chunks'] for m in mappings))
        for m in mappings:
            for candidate in m['candidate_chunks']:
                c = by_id[candidate['chunk_id']]
                self.assertEqual(c['source_policy_id'], m['source_policy_id'])
                self.assertEqual(c['source_policy_version'], m['source_policy_version'])
                self.assertIn(m['intent'], [c['intent']] + c['related_intents'])
        wrong_version = dict(self.chunks[0], source_policy_version='1.0')
        no_matches = builder.build_faq_mapping(self.faqs, [wrong_version], lambda s: set(s.split()))
        self.assertTrue(all(m['status'] == 'review_required' for m in no_matches))

    def test_alternative_expression_changes_candidate_ranking(self):
        faq = dict(self.faqs[0], question='help', alternatives=['protect freeze', 'protect frozen', 'freeze protection'], expressions=['help', 'protect freeze', 'protect frozen', 'freeze protection'])
        base = next(c for c in self.chunks if c['intent'] == faq['intent'])
        a = dict(base, chunk_id='A', title='help', content='help')
        b = dict(base, chunk_id='B', title='protect freeze frozen protection', content='protect freeze frozen protection')
        tokenize = lambda s: set(s.lower().split())
        row = builder.build_faq_mapping([faq], [a, b], tokenize)[0]
        self.assertEqual(row['candidate_chunks'][0]['chunk_id'], 'B')
        self.assertEqual(row['expressions'], faq['expressions'])

    def test_default_rebuild_preserves_both_jsonl_outputs(self):
        with tempfile.TemporaryDirectory() as target:
            subprocess.run([sys.executable, str(RAG / 'build_knowledge_chunks.py'), '--output-dir', target], check=True, capture_output=True)
            for name in ['NovaBank_knowledge_chunks_v1_1.jsonl', 'NovaBank_faq_chunk_mapping_v1_1.jsonl']:
                self.assertEqual((Path(target) / name).read_bytes(), (RAG / 'chunks' / name).read_bytes())
            report = json.loads((Path(target) / 'validation_report_v1_1.json').read_text())
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['faq_expression_coverage']['expressions_preserved'], 924)
            self.assertEqual(report['faq_expression_coverage']['unmatched_faq_ids'], [])
            self.assertEqual(len(report['resolved_source_issues']), 4)


if __name__ == '__main__':
    unittest.main()
