"""One entry point for approved-data validation and offline BM25 evaluation.

Default split is dev. Test evaluation must be requested explicitly.
Run with PYTHONPATH=src python -m banking_agent.modules.rag.evaluate_retrieval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def calculate_metrics(records: list[dict[str, Any]], predictions: dict[str, dict]) -> dict:
    eligible = [r for r in records
                if r['evaluation_status'] != 'blocked_policy_conflict'
                and r['human_review_status'] == 'approved']
    evidence = [r for r in eligible if r['case_type'] in {'supported', 'unsupported'}]
    no_evidence = [r for r in eligible if r['case_type'] == 'no_evidence']
    for row in eligible:
        if row['question_id'] not in predictions:
            raise ValueError(f"Missing prediction for {row['question_id']}")
        result = predictions[row['question_id']]
        if result['status'] not in {'ok', 'empty', 'error'}:
            raise ValueError('Invalid prediction status')
        ids = [doc['document_id'] for doc in result['data']['docs']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate retrieved IDs')
        if result['status'] != 'ok' and ids:
            raise ValueError('Empty/error result cannot contain documents')
        if row['case_type'] != 'no_evidence' and not row['gold_chunk_ids']:
            raise ValueError('Evidence question requires gold')
        if row['case_type'] == 'no_evidence' and (row['gold_chunk_ids'] or row['gold_policy_ids']):
            raise ValueError('No-evidence gold must be empty')

    def ranked(row: dict) -> list[str]:
        return [d['document_id'] for d in predictions[row['question_id']]['data']['docs']][:5]

    def evidence_metrics(rows: list[dict]) -> dict:
        output = {'questions': len(rows)}
        multi = [r for r in rows if r['multi_chunk']]
        for k in (1, 3, 5):
            recall = hit = 0.0
            for row in rows:
                gold = set(row['gold_chunk_ids'])
                found = set(ranked(row)[:k]) & gold
                recall += len(found) / len(gold)
                hit += bool(found)
            output[f'recall_at_{k}'] = recall / len(rows) if rows else None
            output[f'hit_at_{k}'] = hit / len(rows) if rows else None
            output[f'all_gold_recall_at_{k}'] = (sum(set(r['gold_chunk_ids']) <= set(ranked(r)[:k]) for r in multi) / len(multi)) if multi else None
        output['multi_chunk_questions'] = len(multi)
        output['mrr_at_5'] = (sum(next((1 / i for i, cid in enumerate(ranked(r), 1) if cid in r['gold_chunk_ids']), 0.0) for r in rows) / len(rows)) if rows else None
        return output

    successful_negatives = [r for r in no_evidence if predictions[r['question_id']]['status'] != 'error']
    return {'metric_status': 'human_approved_only',
            'evaluated_questions': len(eligible), 'excluded_questions': len(records) - len(eligible),
            'evidence_cases': evidence_metrics(evidence),
            'by_case_type': {kind: evidence_metrics([r for r in evidence if r['case_type'] == kind]) for kind in ['supported', 'unsupported']},
            'no_evidence_questions': len(no_evidence), 'no_evidence_successful_calls': len(successful_negatives),
            'false_positive_retrieval_rate': (sum(bool(ranked(r)) for r in successful_negatives) / len(successful_negatives)) if successful_negatives else None,
            'technical_errors': sum(predictions[r['question_id']]['status'] == 'error' for r in eligible)}


def load_validated_data(rag: Path) -> tuple[dict[str, list[dict]], dict]:
    """Verify approved sources, IDs, exact evidence and dev/test separation."""
    evaluation = rag / 'evaluation'
    manifest = json.loads((evaluation / 'manifest.json').read_text())
    if not manifest.get('reviewed_by') or not manifest.get('reviewed_on'):
        raise ValueError('Human approval metadata is missing')
    chunks = {c['chunk_id']: c for c in map(json.loads, (rag / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_text().splitlines())}
    report = json.loads((rag / 'chunks/validation_report_v1_1.json').read_text())
    conflicting = {i for issue in report['source_issues_requiring_review'] for i in issue.get('affected_intents', [])}
    datasets, seen_ids, seen_queries = {}, set(), set()
    for split in ('dev', 'test'):
        path = evaluation / manifest['dataset_files'][split]['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['dataset_files'][split]['sha256']:
            raise ValueError(f'{split}: approved dataset hash changed')
        rows = list(map(json.loads, path.read_text().splitlines()))
        for row in rows:
            qid, query = row['question_id'], row['query'].strip().lower()
            if qid in seen_ids or query in seen_queries or not query:
                raise ValueError('Duplicate or empty evaluation record')
            seen_ids.add(qid)
            seen_queries.add(query)
            if row['split'] != split or row['human_review_status'] != 'approved' or row['evaluation_status'] != 'ready':
                raise ValueError(f'{qid}: record is not approved for this split')
            if set(row['target_intents']) & conflicting:
                raise ValueError(f'{qid}: unresolved policy conflict')
            gold = row['gold_chunk_ids']
            if row['case_type'] not in {'supported', 'unsupported', 'no_evidence'}:
                raise ValueError(f'{qid}: invalid case type')
            if row['case_type'] == 'no_evidence':
                if gold or row['gold_policy_ids']:
                    raise ValueError(f'{qid}: no-evidence gold must be empty')
            elif not gold:
                raise ValueError(f'{qid}: missing gold')
            if len(gold) != len(set(gold)) or any(cid not in chunks for cid in gold):
                raise ValueError(f'{qid}: invalid gold IDs')
            if sorted(row['gold_policy_ids']) != sorted({chunks[cid]['source_policy_id'] for cid in gold}):
                raise ValueError(f'{qid}: policy provenance mismatch')
            if row['multi_chunk'] != (len(gold) > 1):
                raise ValueError(f'{qid}: multi-chunk designation mismatch')
            if {e['chunk_id'] for e in row['gold_evidence']} != set(gold):
                raise ValueError(f'{qid}: missing gold evidence')
            for evidence in row['gold_evidence']:
                chunk = chunks[evidence['chunk_id']]
                policy = rag / evidence['source_document']
                if hashlib.sha256(policy.read_bytes()).hexdigest() != evidence['policy_sha256']:
                    raise ValueError(f'{qid}: policy changed after review')
                if hashlib.sha256(chunk['content'].encode()).hexdigest() != evidence['chunk_content_sha256']:
                    raise ValueError(f'{qid}: chunk changed after review')
                if not evidence['supporting_sentences'] or any(s not in chunk['content'] for s in evidence['supporting_sentences']):
                    raise ValueError(f'{qid}: invalid supporting sentence')
            if split == 'test' and row['leakage_flags']:
                raise ValueError(f'{qid}: known exposure in test set')
        datasets[split] = rows
    for field in ('group_id', 'target_intents', 'gold_chunk_ids'):
        def values(split: str) -> set:
            return {v for r in datasets[split] for v in ([r[field]] if field == 'group_id' else r[field])}
        if values('dev') & values('test'):
            raise ValueError(f'Dev/test overlap: {field}')
    if len(seen_ids) != manifest['total']:
        raise ValueError('Manifest count differs from dataset')
    return datasets, manifest


def apply_fixed_minus6_gate(result: dict) -> dict:
    """Frozen query-level gate: keep all original docs when max score >= -6.

    No per-document pruning, no adjustable threshold and no production enablement.
    Technical errors stay error; a pre-existing empty result stays empty.
    """
    from .retriever import validate_result
    checked = validate_result(result, 5)
    if checked['status'] == 'ok' and max(d['score'] for d in checked['data']['docs']) < -6.0:
        return {'status': 'empty', 'data': {'docs': []}}
    return checked


def load_gate_confirmation(rag: Path, require_approved: bool = True) -> tuple[list[dict], dict]:
    """Verify fixed source/dataset identity before a confirmation run."""
    folder = rag / 'evaluation/gate_minus6_confirmation_v1'
    manifest = json.loads((folder/'manifest.json').read_text())
    path = folder/'questions.jsonl'
    if manifest['threshold'] != -6.0 or manifest['candidate_k'] != 20 or manifest['top_k'] != 5:
        raise ValueError('Fixed gate protocol changed')
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['dataset_sha256']:
        raise ValueError('Confirmation dataset changed; review and update approval/hash')
    for name, expected in manifest['frozen_source_sha256'].items():
        if hashlib.sha256((rag/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen source changed: {name}')
    rows = list(map(json.loads, path.read_text().splitlines()))
    if len(rows) != manifest['questions'] or len({r['question_id'] for r in rows}) != len(rows):
        raise ValueError('Invalid confirmation count or IDs')
    if len({r['query'].strip().lower() for r in rows}) != len(rows):
        raise ValueError('Duplicate confirmation query')
    chunks = {r['chunk_id']: r for r in map(json.loads,
        (rag/'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_text().splitlines())}
    for row in rows:
        if row['case_type'] not in ('supported','unsupported','no_evidence') or not row['query'].strip():
            raise ValueError('Invalid confirmation case')
        gold = row['gold_chunk_ids']
        if row['case_type'] == 'no_evidence':
            if gold or row['gold_policy_ids']:
                raise ValueError('No-evidence case cannot have gold')
        elif not gold:
            raise ValueError('Evidence case requires gold')
        if len(set(gold)) != len(gold) or any(cid not in chunks for cid in gold):
            raise ValueError('Invalid gold IDs')
        if row['multi_chunk'] != (len(gold)>1):
            raise ValueError('Invalid multi-chunk flag')
        if set(row['gold_policy_ids']) != {chunks[cid]['source_policy_id'] for cid in gold}:
            raise ValueError('Gold policy mismatch')
        contextual_ids = {e['chunk_id'] for e in row['context_evidence']}
        if not set(gold) <= contextual_ids:
            raise ValueError('Gold evidence missing from review context')
        for e in row['context_evidence']:
            chunk = chunks[e['chunk_id']]
            if e['source_document'] != chunk['source_document'] or not e['quote'] or e['quote'] not in chunk['content']:
                raise ValueError('Invalid source quote')
            if hashlib.sha256(chunk['content'].encode()).hexdigest() != e['chunk_content_sha256']:
                raise ValueError('Reviewed chunk changed')
            if hashlib.sha256((rag/e['source_document']).read_bytes()).hexdigest() != e['policy_sha256']:
                raise ValueError('Reviewed policy changed')
        if require_approved and (row['human_review_status']!='approved' or row['evaluation_status']!='ready'
                                 or not row.get('reviewed_by') or not row.get('reviewed_on')):
            raise ValueError('Human approval required before any model scoring')
    if require_approved and (manifest['human_review_status']!='approved' or not manifest['reviewed_by'] or not manifest['reviewed_on']):
        raise ValueError('Manifest approval required')
    return rows, manifest


def run_gate_confirmation(rag: Path, output: Path) -> None:
    """One fixed comparison after approval; no threshold search or test tuning."""
    rows, manifest = load_gate_confirmation(rag)
    if output.exists():
        raise ValueError('Output exists; do not overwrite confirmation results')
    from .real_retriever import RealRetriever, DEFAULT_MODEL, DEFAULT_REVISION
    if manifest['model'] != DEFAULT_MODEL or manifest['revision'] != DEFAULT_REVISION:
        raise ValueError('Frozen model differs from real backend')
    backend = RealRetriever()
    baseline = {r['question_id']: backend.retrieve(r['query'], 5) for r in rows}
    gated = {qid: apply_fixed_minus6_gate(result) for qid,result in baseline.items()}
    positives = [r for r in rows if r['case_type']!='no_evidence']
    def found(row: dict, predictions: dict) -> set:
        return set(row['gold_chunk_ids']) & {d['document_id'] for d in predictions[row['question_id']]['data']['docs']}
    summary = {'threshold': -6, 'rule': manifest['gate_rule'], 'production_enabled': False,
        'baseline': calculate_metrics(rows, baseline), 'gated': calculate_metrics(rows, gated),
        'by_stratum': {kind: {'baseline': calculate_metrics([r for r in rows if r['stratum']==kind], baseline),
                             'gated': calculate_metrics([r for r in rows if r['stratum']==kind], gated)} for kind in manifest['strata']},
        'answerable_empty_after_gate': [r['question_id'] for r in positives if gated[r['question_id']]['status']=='empty'],
        'newly_rejected_answerable': [r['question_id'] for r in positives
            if baseline[r['question_id']]['status']=='ok' and gated[r['question_id']]['status']=='empty'],
        'lost_gold_questions': [r['question_id'] for r in positives if found(r,baseline)-found(r,gated)],
        'unsupported_gold_losses': [r['question_id'] for r in positives if r['case_type']=='unsupported' and found(r,baseline)-found(r,gated)],
        'manifest': manifest, 'model_metadata': backend.metadata,
        'interpretation': 'Fresh wording with source overlap; no new-need blind-test claim. Any tuning converts this set to development.'}
    output.mkdir(parents=True)
    (output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'rankings.jsonl').write_text(''.join(json.dumps({'question_id':r['question_id'],'query':r['query'],
        'gold_chunk_ids':r['gold_chunk_ids'],'baseline':baseline[r['question_id']], 'gated':gated[r['question_id']]})+'\n' for r in rows))
    print(json.dumps(summary,indent=2))


def main() -> None:
    """Evaluate an explicitly selected backend; default split remains dev."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gate-confirmation', action='store_true', help='Fixed -6 gate; requires approved new questions')
    parser.add_argument('--split', choices=('dev','test'), default='dev')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--backend', choices=('real','bm25','dense','hybrid'), default='real')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    rag = Path(__file__).resolve().parent
    if args.gate_confirmation:
        if args.split != 'dev' or args.backend != 'real':
            parser.error('Confirmation uses only the fixed real backend, never test')
        if args.validate_only:
            rows, _ = load_gate_confirmation(rag, require_approved=False)
            print(json.dumps({'questions': len(rows), 'pending': sum(r['human_review_status']!='approved' for r in rows)}))
        else:
            run_gate_confirmation(rag, args.output_dir or rag/'evaluation/gate_minus6_confirmation_v1/results')
        return
    datasets, manifest = load_validated_data(rag)
    if args.validate_only:
        print(json.dumps({split: len(rows) for split, rows in datasets.items()}))
        return
    output = args.output_dir or rag / 'evaluation/results' / (args.backend + '_' + args.split)
    if output.exists():
        parser.error('Output exists; choose a new --output-dir')
    from .retriever import create_retriever
    if args.backend == 'real':
        backend = create_retriever('real')
    elif args.backend == 'bm25':
        from .bm25_retriever import BM25Retriever
        backend = BM25Retriever(str(rag / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'))
    else:
        from .hybrid_retriever import HybridRetriever
        backend = HybridRetriever(str(rag / 'chunks/NovaBank_knowledge_chunks_v1_1.jsonl'), local_files_only=True)
    rows = datasets[args.split]
    predictions = {r['question_id']: (backend.retrieve(r['query'],5,mode=args.backend)
                   if args.backend in ('dense','hybrid') else backend.retrieve(r['query'],5)) for r in rows}
    metrics = calculate_metrics(rows, predictions)
    metrics.update({'backend': args.backend, 'split': args.split,
        'dataset_sha256': manifest['dataset_files'][args.split]['sha256'],
        'corpus_sha256': hashlib.sha256((rag/'chunks/NovaBank_knowledge_chunks_v1_1.jsonl').read_bytes()).hexdigest()})
    from importlib.metadata import version
    metrics['versions'] = {name: version(name) for name in ('rank_bm25', 'numpy', 'pydantic')}
    metrics['metadata'] = getattr(backend, 'metadata', getattr(backend, 'index_metadata', {}))
    metrics['code_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (rag/'real_retriever.py', rag/'bm25_retriever.py', rag/'hybrid_retriever.py', rag/'retriever.py', rag/'cross_encoder_reranker.py')}
    output.mkdir(parents=True)
    (output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    (output/'rankings.jsonl').write_text(''.join(json.dumps({'question_id':r['question_id'],
        'query':r['query'],'gold_chunk_ids':r['gold_chunk_ids'],'result':predictions[r['question_id']]})+'\n' for r in rows))
    print(json.dumps(metrics,indent=2))


if __name__ == '__main__':
    main()
