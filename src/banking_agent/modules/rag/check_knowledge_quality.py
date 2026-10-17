#!/usr/bin/env python3
"""Reproduce the 2026-10-14 NovaBank knowledge-quality review.

Standard-library cross-category TF-IDF candidate detection and metadata/source
checks, with the original editorial findings and candidate dispositions retained.
This is a snapshot review replay: it is NOT an automated semantic fact checker.
Input hashes prevent old human judgements being silently reused after edits.
No policies, FAQ, drafts or chunks are changed. Only the two review reports are
written to --output-dir (default: the RAG quality_reports directory).
"""
import argparse
import collections
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

EXPECTED_CHUNK_SHA256 = '98ce975e9e54f8678177571db20e8cb31fd960f5eaf9dfa6455fd36fa40156d9'
EXPECTED_POLICY_HASHES = {'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md': '872ac45ce52f172a82b8f541061bac1b80a631341bf8d4a9e026ece1de82d36c', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_usage_and_access_master_policy.md': 'b5c6e80a610b60a388854a37bacc820ee6820af7b3755bf5436c9f5bb5213cc1', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_currency_exchange_master_policy.md': 'cad0372a82ac5bdd07b4fc5191ef234517053ee90abdf5524fe9927189cb370c', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_payments_master_policy.md': '98a6e7d63f60821ad1283153a8ff90a3a65422ea6fac0bed605a4df958f5292c', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_cash_withdrawals_master_policy.md': '5f95986bf80f45a6174a33e354472251dc7ceb20831c636606176e0f74315f8f', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_top_ups_master_policy.md': 'aa42082c76c0c313a2af044363e17eb976bfa795426cd3897956706ed0a09f99', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_security_and_unrecognised_transactions_master_policy.md': 'fd371dd57bdfc561e5305932b6ec528080e3c940b02cf29b7bd4358137bcccaf', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_account_management_master_policy.md': 'b30cf94ec91fbc0eba8c15b865fb3583c7621526c995bbe79f2f3eb9f2f4b14f', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md': '8e3b7bbd1bbceb95039fd4cb8a72e8fdafd7b6bdfa77546bab2082f9eba56141', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_virtual_cards_master_policy.md': '51c89700e36219b8b901b8d690b8ff2d57274565fd0f2a7b4c193bbec9e6f299', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_cash_and_cheque_deposits_master_policy.md': '65c78186ac6808ee13a43bf2550604252792a4ec251c73cd32fed3d11527a33b', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_identity_verification_master_policy.md': 'ea5ecdf81736136f879eebc55190919464ce4509419b607b286a91f9b080cc4e', 'novabank_category_master_policies_enriched_v1_1/policies/NovaBank_refunds_master_policy.md': '80661b06522d19e7b919225005d179d3d0d4b7e867e9c2decbdaf561dca05ec2'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rag-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output-dir', type=Path, help='Destination for reports only.')
    args = parser.parse_args()
    if not __debug__:
        raise RuntimeError('Do not use -O; validation assertions must remain enabled.')
    r = args.rag_dir.resolve()
    p=r/'chunks/NovaBank_knowledge_chunks_v1_1.jsonl';original=p.read_bytes();cs=[json.loads(l) for l in original.decode().splitlines()];byid={c['chunk_id']:c for c in cs}
    # This replays a human-reviewed snapshot, rather than asserting new semantic facts.
    if hashlib.sha256(original).hexdigest() != EXPECTED_CHUNK_SHA256:
        raise ValueError('Chunk corpus changed. Review facts and candidate dispositions before updating the saved snapshot.')
    for source_document, expected_hash in EXPECTED_POLICY_HASHES.items():
        if hashlib.sha256((r / source_document).read_bytes()).hexdigest() != expected_hash:
            raise ValueError('Policy changed: ' + source_document + '. Refresh the editorial review before replaying it.')

    pack=r/'novabank_category_master_policies_enriched_v1_1'
    manifest=json.loads((pack/'manifest.json').read_text());sources={d['policy_id']:(pack/d['path']) for d in manifest['policies']}
    def evidence(pid,quote):
     path=sources[pid];s=path.read_text();assert quote in s,(pid,quote)
     return {'source_document':str(path.relative_to(r)),'source_policy_id':pid,'line':s[:s.index(quote)].count('\n')+1,'quote':quote}
    cutoffs=[c['chunk_id'] for c in cs if 'Delivery Day 0 is processing acceptance by 14:00' in c['content'] and 'non-business' not in c['content']]
    issues=[
     {'finding_id':'KQ-001','priority':'P1','kind':'SOURCE_CONFLICT_PROPAGATED','affected_chunk_ids':['NB-v1_1-request_refund-004'],'title':'Aggregate refund cap and remaining refundable principal are conflated','chunk_quote':'Total NovaBank refund recovery cannot exceed the original settled principal less prior credited refunds.','evidence':[evidence('DOC-CAT-REFUND-001','Total credited refunds must not exceed its original settled principal;'),evidence('DOC-CAT-REFUND-001','A refund cannot exceed original settled principal less earlier refunds.'),evidence('DOC-CAT-REFUND-001','Aggregate principal recovery cannot exceed the original settled principal less prior credits.')],'impact':'The chunk follows one ambiguous source statement but conflicts with the separately explicit total-refund cap. For synthetic principal SGD 100 and prior credit SGD 40, remaining refundable principal is SGD 60, while aggregate recovery must be capped at SGD 100; the ambiguous wording could incorrectly cap aggregate recovery at SGD 60. These amounts are test examples, not new policy limits.','recommendation':'Clarify the source first: additional recovery <= original principal minus prior credits; aggregate credited refunds <= original settled principal. Synchronise FAQ/draft/chunk. Hold this chunk from use for refund-cap calculations until clarified.'},
     {'finding_id':'KQ-002','priority':'P2','kind':'CONDITION_OMISSION','affected_chunk_ids':cutoffs,'title':'Generated delivery cutoff omits the non-business-day branch','chunk_quote':'Delivery Day 0 is processing acceptance by 14:00 on a Singapore business day; later acceptance uses the next business day.','evidence':[evidence('DOC-CAT-CARDLIFE-001','later or non-business-day orders use the next business day.'),evidence('DOC-CAT-CARDUSE-001','later/non-business-day orders use the next business day.'),evidence('DOC-CAT-ATM-001','later/non-business-day orders use the next business day.'),evidence('DOC-CAT-SECURITY-001','later/non-business-day orders use the next business day.')],'impact':'The repeated context does not explicitly handle a weekend/public-holiday request before 14:00. In isolation it is incomplete; the canonical delivery-clock chunk does preserve this branch.','recommendation':'Amend the builder context sentence to explicitly include later OR non-business-day acceptance, then regenerate all seven affected chunks. Do not delete the cutoff context to reduce similarity.'},
     {'finding_id':'KQ-003','priority':'P2','kind':'SOURCE_START_EVENT_UNSPECIFIED','affected_chunk_ids':['NB-v1_1-unable_to_verify_identity-002'],'title':'Identity-decision reconsideration intake lacks an explicit 30-day start event','chunk_quote':'A NovaBank customer disputing a documented final identity-verification decision may request one staff reconsideration within 30 calendar days.','evidence':[evidence('DOC-CAT-IDVERIFY-001','A customer disputing a final decision may request one staff review within 30 calendar days;'),evidence('DOC-CAT-IDVERIFY-001','A documented final decision may receive one staff reconsideration requested within 30 calendar days, targeted within 5 business days.')],'impact':'The source and chunk do not explicitly identify whether the 30-calendar-day clock starts when the final decision is recorded, issued or notified. The 5-business-day decision target after complete evidence is explicit.','recommendation':'Ask the policy owner to specify the start event in the source, then synchronise the intake wording. Do not infer a start date from the current wording.'}
    ]
    noise=['Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.','Delivery Day 0 is processing acceptance by 14:00 on a Singapore business day; later acceptance uses the next business day. Day 1 is the following business day.','Use the secure account channel for account-specific checks and changes.']
    stop=set('a an the of for and or to in on at by with from my your how what why when which do does can could is are be me i it about should need know novabank within after before per each not its this that as only up day days business calendar costs takes issued complete seconds amount fee customer staff have has was will if into while through then once without same'.split())
    def text(c):
     t=c['content']
     for n in noise:t=t.replace(n,'')
     return t

    def words(t):
     aliases={'refunded':'refund','refunds':'refund','replacement':'replace','replaced':'replace','payments':'payment','cards':'card','fees':'fee','limits':'limit','transfers':'transfer','credited':'credit','crediting':'credit','verification':'verify','verified':'verify','declined':'decline'}
     return [aliases.get(w,w) for w in re.findall(r'[a-z]+|\d+(?:[.,:]\d+)*',t.lower()) if w not in stop]
    corpus=[words(text(c)) for c in cs];df=collections.Counter(w for ws in corpus for w in set(ws));vec=[]
    for ws in corpus:
     v={w:(1+math.log(n))*math.log((len(cs)+1)/(df[w]+1)) for w,n in collections.Counter(ws).items()};norm=math.sqrt(sum(x*x for x in v.values()));vec.append({k:v/norm for k,v in v.items()})
    pairs=[]
    for a,b in itertools.combinations(range(len(cs)),2):
     if cs[a]['category']==cs[b]['category']:continue
     va,vb=vec[a],vec[b];cos=sum(x*vb.get(w,0) for w,x in va.items());sa,sb=set(corpus[a]),set(corpus[b]);j=len(sa&sb)/len(sa|sb);contain=len(sa&sb)/min(len(sa),len(sb))
     if cos>=.32 and len(sa&sb)>=8:
      pairs.append({'a':cs[a]['chunk_id'],'b':cs[b]['chunk_id'],'cosine':round(cos,4),'jaccard':round(j,4),'containment':round(contain,4),'shared_terms':sorted(sa&sb)})
    pairs.sort(key=lambda p:p['cosine'],reverse=True)


    notes=[
     ('PARTIAL_SHARED_RULE','Both contain identity-backed access recovery and manual review; phone theft additionally requires session/token protection and number-change controls. Extract a recovery core only; retain both incident routes.'),
     ('KEEP_DISTINCT','FX fee-error and purchase-fee investigations share an SLA, but charged products and evidence differ. Equal numbers do not establish identical knowledge.'),
     ('PARTIAL_SHARED_RULE','Both state NovaBank FX fee/DCC exception. A canonical fee rule can be shared, while the ATM chunk must retain SGD funding, withdrawal fee and operator-charge conditions.'),
     ('KEEP_DISTINCT','Updating an existing verified record differs from onboarding; onboarding requires a live selfie and age/residency eligibility. Do not merge procedures.'),
     ('KEEP_DISTINCT','Phone change and stolen-phone recovery share a 24-hour restriction, but recovery/protection and contact update have different triggers.'),
     ('PARTIAL_SHARED_RULE','The incoming-funding chunk repeats the funding-origin trigger. Canonicalise the trigger under identity verification; retain incoming-cap and funding-counter context in bank transfers.'),
     ('KEEP_DISTINCT','Purchase-fee error and ATM rate error have different transaction scopes and evidence; do not collapse them merely because intake and review numbers match.'),
     ('PARTIAL_SHARED_RULE','The card-address amendment core overlaps strongly. Extract verified pre-dispatch amendment/confirmation/Day 0 reset; preserve the account-update eligibility review and each policy provenance.'),
     ('KEEP_DISTINCT','Final failed card funding releases via an external issuer with a separate five-business-day clock; failed domestic transfers release reservations or returned principal via bank-transfer clocks.'),
     ('KEEP_DISTINCT','Physical PIN blocking (three attempts, rolling unblock limit) differs from app passcode lock (five attempts, thirty-minute lock). Merge would damage safety boundaries.'),
     ('KEEP_DISTINCT','Card rate-error intake remains settlement-based while ATM rate-error intake is ledger-posting-based. The differing start events must remain explicit.'),
     ('KEEP_DISTINCT','Card top-up fee review and outgoing-transfer fee review concern different funding/payment channels and references, despite equal review/correction SLAs.'),
     ('PARTIAL_SHARED_RULE','Both contain the no-FX-fee condition and NovaBank conversion fee. Extract only the fee core; retain purchase-fee classification and original-fee refund exception.'),
     ('PARTIAL_SHARED_RULE','ATM-retained and lost-card replacement share issuance/delivery/token rules. A shared replacement core is possible, but ATM retrieval/cash reconciliation and theft investigation must remain.'),
     ('KEEP_DISTINCT','Merchant Visa debit acceptance differs from Visa/PLUS ATM withdrawal eligibility; virtual/wallet support and ATM physical-card restrictions differ.'),
     ('KEEP_DISTINCT','Contactless prerequisites/cumulative reset explain tap behaviour; recorded issuer decline diagnoses one refused purchase. Threshold repetition is necessary context.'),
     ('KEEP_DISTINCT','Cash-dispensing/status enquiry differs from an unauthorised ATM security case. Immediate fraud escalation and late-report assessment must not be removed.'),
     ('PARTIAL_SHARED_RULE','Both repeat purchase same-currency/FX-fee conditions. Keep a canonical purchase-funding rule, with fee-classification and original-fee treatment retained separately.'),
     ('KEEP_DISTINCT','Purchase funding/settlement conversion defines pricing; rate-error review defines evidence and dispute procedure. They answer different questions.'),
     ('KEEP_DISTINCT','Failed card funding diagnosis differs from failed transfer release and retry. Shared failure vocabulary is not duplicate knowledge.')
    ]
    assert len(pairs)==len(notes)==20
    for i,(pair,(decision,note)) in enumerate(zip(pairs,notes),1):
     pair.update({'candidate_id':f'DQ-{i:03d}','categories':[byid[pair['a']]['category'],byid[pair['b']]['category']],'titles':[byid[pair['a']]['title'],byid[pair['b']]['title']],'disposition':decision,'editorial_reason':note,'action':'No automatic deletion. Extract shared subrules only if provenance and intent applicability remain intact.' if decision=='PARTIAL_SHARED_RULE' else 'Retain both chunks; deduplicate common wording only if conditions stay self-contained.'})
    # Per-chunk checks and representative source evidence; lexical matches are evidence pointers, not proof.
    stop=set('a an the and or to in on at by with from is are be for of novabank within after before per day days business calendar customer staff same'.split())
    def tokens(t):return set(w for w in re.findall(r'[a-z]+|\d+(?:[.,:]\d+)*',t.lower()) if w not in stop)
    def numeric(t):return set(re.findall(r'\d+(?:[.,:]\d+)*',t))
    expected=set(json.loads((pack/'banking77_mapping.json').read_text()))
    metadata=[];num_issues=[];chunk_reviews=[]
    for c in cs:
     src=sources[c['source_policy_id']];t=src.read_text();front=t.split('---',2)[1]
     checks={}
     for output,source in [('source_policy_id','policy_id'),('source_policy_version','version'),('category','business_category'),('effective_date','effective_date'),('region','jurisdiction_context')]:
      v=re.search(r'^'+source+r':\s*(.+)$',front,re.M).group(1).strip();checks[output]=c[output]==v
     checks['status']=c['status']=='active' and 'status: Active' in front
     checks['source_document']=(r/c['source_document']).resolve()==src.resolve()
     checks['intent']=c['intent'] in expected
     checks['related_intents']=all(x in expected and x!=c['intent'] for x in c['related_intents'])
     if not all(checks.values()):metadata.append({'chunk_id':c['chunk_id'],'checks':checks})
     absent=numeric(c['content'])-numeric(t)
     if absent:num_issues.append({'chunk_id':c['chunk_id'],'literals':sorted(absent)})
     terms=tokens(c['content']);suggestions=[]
     for line_no,line in enumerate(t.splitlines(),1):
      if line.startswith(('#','---')) or not line.strip() or ':' in line and line_no<25:continue
      st=tokens(line)
      if len(st)<6:continue
      score=len(st&terms)/len(st|terms)
      suggestions.append((score,line_no,line))
     suggestions.sort(reverse=True)
     affected=[i['finding_id'] for i in issues if c['chunk_id'] in i['affected_chunk_ids']]
     chunk_reviews.append({'chunk_id':c['chunk_id'],'source_policy_id':c['source_policy_id'],'source_document':c['source_document'],'metadata_checks':checks,'numeric_literals_missing_from_source':sorted(absent),'review_result':'REQUIRES_CORRECTION_OR_SOURCE_CLARIFICATION' if affected else 'NO_ADDITIONAL_ISSUE_DETECTED','finding_ids':affected,'representative_source_evidence':[{'line':n,'quote':line,'lexical_score':round(score,4),'use':'Source lookup pointer, not automatic semantic entailment.'} for score,n,line in suggestions[:3]]})
    hashes={str(src.relative_to(r)):hashlib.sha256(src.read_bytes()).hexdigest() for src in sources.values()}
    manifest_mismatch=[d['policy_id'] for d in manifest['policies'] if hashes[str((pack/d['path']).relative_to(r))]!=d['sha256']]
    assert not metadata and not num_issues and not manifest_mismatch
    assert len(cs)==151 and len(chunk_reviews)==151
    assert len({c['content'] for c in cs})==151
    assert {c['intent'] for c in cs}==expected
    assert p.read_bytes()==original
    out = args.output_dir.resolve() if args.output_dir else r / 'quality_reports'
    out.mkdir(parents=True, exist_ok=True)
    report={'status':'REQUIRES_CORRECTION_OR_SOURCE_CLARIFICATION','review_date':'2026-10-14','scope':{'chunk_count':151,'policy_count':13,'primary_intent_count':77,'source_version':'1.1','input_chunk_sha256':hashlib.sha256(original).hexdigest(),'policy_sha256':hashes,'knowledge_files_modified':False},'summary':{'fact_findings':len(issues),'affected_chunks':len({cid for issue in issues for cid in issue['affected_chunk_ids']}),'chunks_without_additional_detected_issue':sum(not x['finding_ids'] for x in chunk_reviews),'metadata_mismatches':len(metadata),'numeric_literals_missing_from_source':len(num_issues),'exact_duplicate_chunks':0,'cross_category_pairs_evaluated':10321,'cross_category_candidates':len(pairs),'candidate_dispositions':dict(Counter(x['disposition'] for x in pairs)),'full_chunk_merges_or_deletions_recommended':0},'methods':{'factual_review':'Editorial inspection of all 151 chunk texts, policy-source metadata and representative supporting passages, with focused review of fees, limits, timing start events, exceptions, security and refund logic. Numbers found somewhere in a policy are not treated as sufficient semantic support.','deduplication':'All cross-category pairs; remove common calendar/cutoff/channel boilerplate; word TF-IDF cosine >= 0.32 and at least 8 shared terms for candidates. Candidates manually classified.','limitations':['This is a bounded knowledge-quality review, not a legal-compliance certification or a retrieval benchmark. No embeddings or model-based entailment checker was run.','Representative source matches are navigation aids, not exhaustive claim-level entailment proofs. NO_ADDITIONAL_ISSUE_DETECTED does not certify that every possible omission has been excluded.','Lexical candidate thresholds can miss semantic paraphrases. Candidate overlap is not itself a reason to merge different business processes.','Source conflicts require correction of Policy before FAQ/draft/chunk synchronisation. Only reports were written; no original chunk or policy was changed.']},'fact_findings':issues,'cross_category_dedup_candidates':pairs,'per_chunk_review':chunk_reviews}
    (out/'knowledge_quality_review_v1_1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    md=['# NovaBank 知识质量检测 — 2026-10-14','', '**结论：发现 3 项需要修正或澄清的问题，建议处理后复检。** 本次检查 151 个块、13 份 v1.1 政策和 77 个意图，只新增报告，未改动知识材料。','', '## 检测结果','', '- 151 个块完成内容检查与来源对照；142 个块未发现新增问题，9 个块涉及 3 项问题。','- 元数据不匹配 0 项；来源政策哈希不匹配 0 项；无来源数字 0 项；完全相同内容重复 0 项。','- 检查 10,321 对跨类别组合，发现 20 对候选：7 对可抽取共享子规则，13 对应保留业务区分。','- 没有建议整块删除或整块合并的候选。词法候选检测不保证发现所有语义重复。','', '## 事实与条件问题','']
    for issue in issues:
     md += [f"### {issue['finding_id']} / {issue['priority']}：{issue['title']}",'',issue['impact'],'', '**涉及块：** '+', '.join(issue['affected_chunk_ids']),'', '**建议：** '+issue['recommendation'],'','**政策依据：**']
     for e in issue['evidence']:md.append(f"- `{e['source_document']}:{e['line']}` — {e['quote']}")
     md.append('')
    md += ['## 跨类别候选去重','', '只移除公共日历、配送截止与安全渠道补充句后计算词 TF-IDF 余弦相似度；阈值 0.32，至少 8 个共享词。以下分数是候选排序值，不是重复概率。','', '| 候选 | 块 A | 块 B | 余弦 | 判定 |','| --- | --- | --- | ---: | --- |']
    for pair in pairs:md.append(f"| {pair['candidate_id']} | {pair['a']} | {pair['b']} | {pair['cosine']} | {'可抽取共享子规则' if pair['disposition']=='PARTIAL_SHARED_RULE' else '保留业务区分'} |")
    md += ['', '**优先考虑的共享核心：** 资金来源审查触发条件（DQ-006）、配送地址修改（DQ-008）、通用 FX/DCC 费用（DQ-003/DQ-013/DQ-018）。需保留每个政策来源及业务例外，不能直接删除完整块。','', '**必须保持独立：** 卡 PIN 与登录 passcode；卡充值失败与银行转账失败；卡汇率争议的结算日起算与 ATM 汇率争议的入账日起算；现金差额查询与未授权 ATM 交易。','', '## 使用说明','', '详细 JSON 报告提供全部 151 个块的检测结果、来源定位以及每个候选的人工判定理由。原构建校验报告的 PASS 表示结构检查通过，与此次更深入的知识质量结论并不等价。本报告未运行检索评测，也未自动修改或删除任何知识块。','']
    (out/'knowledge_quality_review_v1_1.md').write_text('\n'.join(md))
    print(json.dumps(report['summary'],indent=2));print('Input chunk SHA256 unchanged:',hashlib.sha256(p.read_bytes()).hexdigest())

if __name__ == '__main__':
    main()
