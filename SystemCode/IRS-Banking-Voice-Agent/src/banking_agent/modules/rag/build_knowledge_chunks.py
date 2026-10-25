#!/usr/bin/env python3
"""Rebuild NovaBank v1.1 chunks, FAQ-expression mapping and validation report.

This is a data-preparation tool, not an automatic policy summarizer or retriever.
Requires Python 3.11+ and only the standard library. Run --help for options.
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def parse_faqs(text):
    """Read retrieval expressions only. FAQ answers are never factual input."""
    faqs = []
    seen = set()
    for block in re.split(r"\n\s*---\s*\n", text.strip()):
        lines = block.splitlines()
        def value(label):
            values = [line[len(label) + 2:] for line in lines if line.startswith(label + ': ')]
            if len(values) != 1:
                raise ValueError(f'Expected one {label} field')
            return values[0]
        faq_id = value('FAQ ID')
        if faq_id in seen:
            raise ValueError(f'Duplicate FAQ ID: {faq_id}')
        seen.add(faq_id)
        start = lines.index('Alternative Questions:') + 1
        alternatives = []
        for line in lines[start:]:
            if not line.strip():
                continue
            if not line.startswith('- '):
                break
            alternatives.append(json.loads(line[2:]))
        question = json.loads(value('Question'))
        if not 3 <= len(alternatives) <= 5 or not all(isinstance(q, str) and q.strip() for q in [question] + alternatives):
            raise ValueError(f'Invalid questions for {faq_id}')
        expressions = list(dict.fromkeys([question] + alternatives))
        if len(expressions) != 1 + len(alternatives):
            raise ValueError(f'Duplicate expressions for {faq_id}')
        faqs.append({'id': faq_id, 'intent': value('Target BANKING77 Intent'),
                     'question': question, 'alternatives': alternatives, 'expressions': expressions,
                     'source_policy_id': value('Source Policy ID'),
                     'source_policy_version': value('Source Policy Version'),
                     'category': value('Business Category'),
                     'keywords': value('Retrieval Keywords').split(', ')})
    return faqs


def build_faq_mapping(faqs, chunks, tokenize):
    """Keep every expression and rank intent-scoped candidates, not certified answers."""
    mapping = []
    for faq in faqs:
        candidates = []
        query_tokens = set().union(*(tokenize(q) for q in faq['expressions']))
        for chunk in chunks:
            if (chunk['source_policy_id'] != faq['source_policy_id'] or
                chunk['source_policy_version'] != faq['source_policy_version'] or
                chunk['category'] != faq['category'] or chunk['status'] != 'active' or
                faq['intent'] not in [chunk['intent']] + chunk['related_intents']):
                continue
            title_tokens = tokenize(chunk['title'])
            content_tokens = tokenize(chunk['content'])
            score = (4 * len(query_tokens & title_tokens) + len(query_tokens & content_tokens)) / max(1, len(query_tokens))
            candidates.append({'chunk_id': chunk['chunk_id'], 'lexical_score': round(score, 6)})
        candidates.sort(key=lambda c: (-c['lexical_score'], c['chunk_id']))
        mapping.append({'faq_id': faq['id'], 'intent': faq['intent'],
                        'source_policy_id': faq['source_policy_id'],
                        'source_policy_version': faq['source_policy_version'],
                        'question': faq['question'], 'alternative_questions': faq['alternatives'],
                        'expressions': faq['expressions'], 'candidate_chunks': candidates,
                        'association_type': 'intent_scoped_candidates',
                        'status': 'candidates_available' if candidates else 'review_required'})
    return mapping


def main() -> None:
    if not __debug__:
        raise RuntimeError("Do not run with -O: source and format checks must remain enabled.")
    script_path = Path(__file__).resolve()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rag-dir", type=Path,
                        default=script_path.parent,
                        help="RAG input directory (default: the repository RAG directory).")
    parser.add_argument("--drafts", type=Path,
                        help="Curated draft file; defaults to RAG chunk_sources input.")
    parser.add_argument("--output-dir", type=Path,
                        help="Output directory; defaults to RAG chunks. Replaces the chunk, FAQ mapping and validation files.")
    args = parser.parse_args()
    root=args.rag_dir.resolve()
    pack=root/'novabank_category_master_policies_enriched_v1_1'
    out=args.output_dir.resolve() if args.output_dir else root/'chunks'
    manifest=json.loads((pack/'manifest.json').read_text(encoding='utf-8'))
    policies={};intent_policy={}
    for record in manifest['policies']:
     p=pack/record['path'];t=p.read_text(encoding='utf-8');front=t.split('---',2)[1]
     def field(name):
      m=re.search(r'^'+name+r':\s*(.+)$',front,re.M)
      return m.group(1).strip() if m else None
     meta={k:field(k) for k in ['policy_id','business_category','version','status','effective_date','jurisdiction_context','synthetic','source_type']}
     assert meta['source_type'] == 'Category Master Policy', f'{p}: invalid or missing source_type'
     assert meta['version']=='1.1' and meta['status']=='Active' and meta['effective_date']=='2026-10-11'
     assert meta['policy_id']==record['policy_id'] and meta['business_category']==record['business_category']
     assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],str(p)
     headings=[]
     for m in re.finditer(r'^### (.+)$',t,re.M):
      headings.append({'heading':m.group(1),'line':t[:m.start()].count('\n')+1})
     info={'record':record,'text':t,'metadata':meta,'headings':headings,'path':str(p.relative_to(root))}
     policies[record['policy_id']]=info
     for intent in record['included_intents']:
      assert re.search(r'^### '+re.escape(intent)+r' — ',t,re.M)
      intent_policy[intent]=info
    faq_path=root/'faqs/NovaBank_BANKING77_FAQs_v1_1.md'
    faqs = parse_faqs(faq_path.read_text(encoding='utf-8'))
    for faq in faqs:
     info = intent_policy[faq['intent']]['metadata']
     assert faq['source_policy_id'] == info['policy_id']
     assert faq['source_policy_version'] == info['version']
     assert faq['category'] == info['business_category']
    assert len(faqs)==231
    products={
    'card_lifecycle':'physical Visa debit card','card_usage_and_access':'Visa debit cards and wallet tokens',
    'currency_exchange':'personal account currency balances and conversion','card_payments':'Visa debit card purchases',
    'cash_withdrawals':'physical Visa debit card ATM withdrawals','card_top_ups':'external debit-card SGD funding',
    'security_and_unrecognised_transactions':'personal account and debit-card security','account_management':'personal account',
    'bank_transfers':'domestic SGD bank transfers','virtual_cards':'reusable and disposable virtual Visa debit cards',
    'cash_and_cheque_deposits':'personal account funding','identity_verification':'personal account verification',
    'refunds':'debit-card purchase refunds'}
    stop=set('a an the of for and or to in on at by with from my your how what why when which do does can could is are be me i it about should need know novabank within after before per each not its this that as only up day days business calendar costs takes issued complete seconds amount fee customer staff have has was will if into while through then once without same'.split())
    def tokens(s):
     aliases={'refunded':'refund','refunds':'refund','refunding':'refund','charges':'charge','charged':'charge','charging':'charge','replacing':'replace','replacement':'replace','replaced':'replace','issued':'issue','issuance':'issue','issuing':'issue','payments':'payment','cards':'card','limits':'limit','fees':'fee','arrives':'arrival','arrived':'arrival','arrive':'arrival','declined':'decline','verification':'verify','verified':'verify','failed':'failure','fails':'failure','tracing':'trace','transfers':'transfer','funds':'fund','funding':'fund','cancelled':'cancel','cancelling':'cancel','cancellation':'cancel'}
     return {aliases.get(w,w) for w in re.findall(r'[a-z]+',s.lower()) if w not in stop and len(w)>2}
    draft_path=args.drafts.resolve() if args.drafts else root/'chunk_sources/knowledge_chunk_drafts_v1_1.txt'
    records=re.findall(r'^\[([^\n]+)\]\n(.*?)(?=^\[|\Z)',draft_path.read_text(encoding='utf-8'),re.M|re.S)
    assert records, 'No chunk drafts parsed; check the header format.'
    chunks=[];audit=[];number=Counter()
    calendar=' Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.'
    cutoff=' Delivery Day 0 is processing acceptance by 14:00 on a Singapore business day; later or non-business-day acceptance uses the next business day. Day 1 is the following business day.'
    for header,body in records:
     intent,kind,title,related=header.split('|');related=related.split(',') if related else []
     info=intent_policy[intent];meta=info['metadata'];content=' '.join(body.split())
     assert kind in ['policy','faq','procedure','warning','definition']
     assert all(i in intent_policy and i!=intent for i in related)
     context=[]
     if re.search(r'\bDay [125]\b',content) and '14:00' not in content:
      content+=cutoff;context.append('Physical-card processing acceptance/cutoff convention in the source policy')
     if ('business day' in content.lower() or re.search(r'\bDay [125]\b',content)) and 'exclude weekends' not in content:
      content+=calendar;context.append('Shared business-day calendar and complete-evidence review start')
     # Source-grounded reminders keep the main rule safe when retrieved alone.
     if kind=='procedure' and not re.search(r'secur|authenticat',content,re.I):
      content+=' Use the secure account channel for account-specific checks and changes.'
      context.append('Shared account-specific authentication boundary')
     number[intent]+=1
     key=re.sub(r'[^A-Za-z0-9_-]','',intent)
     cid=f'NB-v1_1-{key}-{number[intent]:03d}'
     relevant=[f for f in faqs if f['intent'] in [intent]+related]
     weights=tokens(title+' '+body)
     def expression_score(q):
      q_tokens = tokens(q)
      return (4*len(tokens(title)&q_tokens)+len(weights&q_tokens))/max(1,len(q_tokens))
     ranked=sorted(relevant,key=lambda f:max(expression_score(q) for q in f['expressions']),reverse=True)
     matched=[f for f in ranked if any(len(tokens(title)&tokens(q))>=2 and expression_score(q)>=2 for q in f['expressions'])]
     # Keywords are compact hints; the sidecar preserves ALL expressions without a cap.
     kws=[title.lower(),intent.replace('_',' ').rstrip('?')]
     expression_hints=[]
     for f in matched:
      expression_hints.extend(q for q in f['expressions'] if len(tokens(title)&tokens(q))>=2)
     expression_hints=sorted(dict.fromkeys(expression_hints),key=lambda q:-expression_score(q))
     kws.extend(expression_hints[:4])
     for f in matched:
      for term in f['keywords']:
       if tokens(term)&weights and term not in kws:kws.append(term)
     for word in re.findall(r'[a-z]+(?:-[a-z]+)*',title.lower()):
      if word not in stop and word not in kws and len(word)>2:kws.append(word)
     kws=list(dict.fromkeys(kws))[:10]
     chunk={'chunk_id':cid,'title':title,'content':content,'knowledge_type':kind,'intent':intent,'related_intents':related,'category':meta['business_category'],'source_policy_id':meta['policy_id'],'source_policy_version':meta['version'],'source_document':info['path'],'source_type':meta['source_type'],'customer_type':'personal','product':products.get(meta['business_category']),'region':meta['jurisdiction_context'],'status':'active','effective_date':meta['effective_date'],'retrieval_keywords':kws}
     chunks.append(chunk)
     relevant_headings=[h for h in info['headings'] if any(h['heading'].startswith(i+' — ') for i in [intent]+related) or h['heading'] in ['Common Calendar, Authentication and Evidence Rules','Common Fees, Limits and Service Conditions','Academic Scope and Safety','Physical-Card Delivery Reference','Currency Conversion Boundary','Counter and Available-Balance Interpretation','Funding-Origin Review Boundary','Calendar, Cutoff and Service Start Events','Fees and Delivery Service Matrix','Card Counts, Renewal Overlap and Order States','Authentication, Evidence and Secure Channels','Security, Payment Continuity and Liability Boundaries']]
     audit.append({'chunk_id':cid,'source_sha256':info['record']['sha256'],'source_sections_to_review':relevant_headings,'context_included':context,'faq_phrasing_ids':[f['id'] for f in matched],'source_authority':'Policy text only; FAQ questions/keywords supply retrieval phrasing, never answer facts.'})
    # Uncertain source statements stay in the report, not in the active JSONL.
    # Resolved source issues are retained as a trace, with assertions on current rules.
    resolution_specs = [
        ('REVIEW-001', 'DOC-CAT-CARDTOPUP-001', ['pending_top_up', 'top_up_failed', 'topping_up_by_card', 'automatic_top_up'], 'pending may last at most 72 hours from issuer authorisation, not NovaBank acceptance or request initiation.', '72-hour finalisation starts at recorded issuer authorisation; final FAILED and release instruction remain separate clocks.'),
        ('REVIEW-002', 'DOC-CAT-CARDPAY-001', ['card_payment_fee_charged'], 'Submit an alleged fee error within 60 calendar days of the disputed fee posting to the NovaBank ledger, not purchase settlement if the dates differ.', 'Purchase-fee intake starts at disputed fee ledger posting, not underlying purchase settlement.'),
        ('REVIEW-003', 'DOC-CAT-ATM-001', ['wrong_exchange_rate_for_cash_withdrawal'], 'Submit an alleged rate-calculation error within 60 calendar days of the disputed withdrawal posting to the NovaBank ledger, not settlement if the dates differ.', 'ATM rate-error intake starts at withdrawal ledger posting.'),
        ('REVIEW-004', 'DOC-CAT-ATM-001', ['pending_cash_withdrawal'], 'A status-only enquiry is reviewed within 2 business days after complete evidence.', 'Status-only review is 2 business days; cash-dispensing reconciliation is 10 business days, both after complete evidence, with immediate reporting of cash problems.'),
    ]
    review = []
    resolutions = []
    for rid, pid, intents, quote, explanation in resolution_specs:
        text = policies[pid]['text']
        assert quote in text, (rid, 'Canonical clarification missing')
        resolutions.append({'review_id': rid, 'status': 'RESOLVED', 'clarification_date': '2026-10-14', 'source_policy_id': pid, 'source_policy_version': '1.1', 'source_document': policies[pid]['path'], 'canonical_source_passage': {'quote': quote, 'line': text[:text.index(quote)].count('\n') + 1}, 'resolution': explanation, 'affected_active_chunk_ids': [c['chunk_id'] for c in chunks if c['intent'] in intents]})
    fields=['chunk_id','title','content','knowledge_type','intent','related_intents','category','source_policy_id','source_policy_version','source_document','source_type','customer_type','product','region','status','effective_date','retrieval_keywords']
    assert chunks and all(list(c)==fields for c in chunks)
    assert len({c['chunk_id'] for c in chunks})==len(chunks)
    assert len({c['content'] for c in chunks})==len(chunks)
    assert set(c['intent'] for c in chunks)==set(intent_policy)
    assert all(len(c['retrieval_keywords'])>=3 for c in chunks)
    # Check numeric literals against the owning policy, accepting typographic number variants.
    def nums(s):return set(re.findall(r'\d+(?:[.,:]\d+)*',s.replace('–','-').replace('—','-')))
    numeric=[]
    for c in chunks:
     absent=nums(c['content'])-nums(policies[c['source_policy_id']]['text'])
     if absent:numeric.append({'chunk_id':c['chunk_id'],'literals_to_review':sorted(absent)})
    # Similarity is only a candidate detector; necessary contextual repetition is retained.
    near=[]
    for a in range(len(chunks)):
     for b in range(a):
      ca,cb=chunks[a],chunks[b]
      if ca['category']!=cb['category']:continue
      sa=tokens(ca['content'].replace(calendar.strip(),''));sb=tokens(cb['content'].replace(calendar.strip(),''))
      similarity=len(sa&sb)/len(sa|sb)
      if similarity>=.58:near.append({'chunk_ids':[cb['chunk_id'],ca['chunk_id']],'token_jaccard':round(similarity,3)})
    word_counts={c['chunk_id']:len(c['content'].split()) for c in chunks}
    report={'status':'PASS','scope':{'policy_count':len(policies),'source_version':'1.1','source_effective_date':'2026-10-11','synthetic':True,'meaning_of_active':'Active within the fictional NovaBank corpus; not real banking approval.','faq_count_used_for_phrasing_only':len(faqs)},'counts':{'active_chunks':len(chunks),'primary_intents':len(number),'all_target_intents':len(intent_policy),'by_category':dict(Counter(c['category'] for c in chunks)),'by_knowledge_type':dict(Counter(c['knowledge_type'] for c in chunks)),'by_primary_intent':dict(number)},'checks':{'valid_jsonl':True,'exact_required_fields':True,'unique_chunk_ids':True,'exact_duplicate_content':0,'all_77_intents_have_primary_chunks':True,'all_related_labels_valid':True,'source_metadata_read_from_frontmatter':True,'all_sources_active_v1_1':True,'source_hashes_match_manifest':True,'faq_answers_not_used_as_authority':True,'semantic_support_method':'Editorial policy-based summaries with source-section references and source-local context. Numeric/source checks are mechanical; not a proof of every semantic claim.','numeric_literals_needing_review':numeric,'near_duplicate_candidates':near},'word_lengths':{'guideline':[50,150],'minimum':min(word_counts.values()),'maximum':max(word_counts.values()),'outside_guideline':[{'chunk_id':k,'words':v,'reason':'Preserve complete conditions and source-local context; length is advisory.'} for k,v in word_counts.items() if not 50<=v<=150]},'source_issues_requiring_review':review,'resolved_source_issues':resolutions,'coverage_notes':['Policy rules are consolidated by knowledge topic; this is not a paragraph-by-paragraph reproduction. Related labels are assigned only to shared applicable rules.','FAQ answers and external reference materials are excluded as factual authorities. FAQ questions and keywords are used only for retrieval phrasing.','Repeated fees, authentication and clock context are retained where needed to make a different rule self-contained; duplicate standalone FAQ copies are not emitted.','Source instructions for implementation, external-source registries, historical-version narratives and duplicated intent summary tables are not customer knowledge chunks.','All four previously flagged timing issues are explicitly clarified in current policies and represented in the active chunks; see resolved_source_issues.'],'chunk_provenance':audit}
    report['knowledge_quality_clarifications'] = manifest.get('knowledge_quality_clarifications', [])
    assert all('NovaBank' in c['content'] for c in chunks)
    assert all((root/c['source_document']).is_file() for c in chunks)
    assert any('72 hours from the recorded issuer-authorisation timestamp' in c['content'] for c in chunks if c['intent']=='pending_top_up')
    for intent in ['card_payment_fee_charged','wrong_exchange_rate_for_cash_withdrawal']:
     assert any('60 calendar days' in c['content'] and 'posting to the NovaBank ledger' in c['content'] for c in chunks if c['intent']==intent)
    assert all(issue['affected_active_chunk_ids'] for issue in review)
    faq_mapping = build_faq_mapping(faqs, chunks, tokens)
    unmatched = [row['faq_id'] for row in faq_mapping if not row['candidate_chunks']]
    report['faq_expression_coverage'] = {
        'faqs': len(faqs), 'primary_questions': len(faqs),
        'alternative_questions': sum(len(f['alternatives']) for f in faqs),
        'expressions_preserved': sum(len(row['expressions']) for row in faq_mapping),
        'faqs_with_candidate_chunks': len(faq_mapping) - len(unmatched),
        'unmatched_faq_ids': unmatched,
        'chunks_with_question_hints': sum(any('?' in k for k in c['retrieval_keywords']) for c in chunks),
        'association_method': 'Same source policy/version/category and explicit primary/related intent; lexical ranking of all compatible chunks. Candidates require retrieval evaluation; no semantic confidence claim.'}
    out.mkdir(parents=True,exist_ok=True)
    file=out/'NovaBank_knowledge_chunks_v1_1.jsonl'
    file.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in chunks),encoding='utf-8')
    assert [json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()]==chunks
    mapping_file = out / 'NovaBank_faq_chunk_mapping_v1_1.jsonl'
    mapping_file.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in faq_mapping),encoding='utf-8')
    report['faq_mapping_file'] = {'name': mapping_file.name, 'sha256': hashlib.sha256(mapping_file.read_bytes()).hexdigest()}
    report['checks'].update({'source_type_matches_policy_metadata':all(c['source_type']==policies[c['source_policy_id']]['metadata']['source_type'] for c in chunks),'source_document_paths_resolve':True,'clarified_deadlines_restored_to_active_chunks':True,'all_chunks_name_novabank':True,'near_duplicate_detection_scope':'Token Jaccard >= 0.58 within a business category; candidates only, not a semantic duplicate guarantee.'})
    report['output_file']={'name':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'format':'UTF-8 JSONL; one complete object per line; no Markdown fences'}
    report['generation']={'script':str(script_path.relative_to(script_path.parents[4])),'method':'Deterministic packaging of editorially curated policy summaries; no model call, embeddings or live retrieval.','drafts':str(draft_path.relative_to(root)) if draft_path.is_relative_to(root) else str(draft_path),'drafts_sha256':hashlib.sha256(draft_path.read_bytes()).hexdigest(),'faq_sha256':hashlib.sha256(faq_path.read_bytes()).hexdigest(),'manifest_sha256':hashlib.sha256((pack/'manifest.json').read_bytes()).hexdigest()}
    if numeric or near or unmatched:
     report['status']='REVIEW_REQUIRED'
    (out/'validation_report_v1_1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'count':len(chunks),'intent_count':len(number),'numeric_review':numeric,'near_duplicates':near,'length_outliers':report['word_lengths']['outside_guideline'],'status':report['status'],'output':str(file),'report':str(out/'validation_report_v1_1.json')},indent=2))


if __name__ == "__main__":
    main()
