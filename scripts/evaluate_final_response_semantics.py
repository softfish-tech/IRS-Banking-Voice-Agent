"""Independently judge recorded ANSWER/CLARIFY text without rerunning the agent.

The source reports must contain only synthetic evaluation conversations.  This
script preserves their raw attempts and writes a separate, hash-linked judge
artifact.  BLOCK/ESCALATE/ABSTAIN/HANDLE_COMPLAINT are recorded as structural
safety rows only; they are not included in answer-quality headline rates.
"""
from __future__ import annotations

import argparse, asyncio, hashlib, json, os, sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path: sys.path.insert(0, str(ROOT / "src"))

from banking_agent.app.local_env import load_local_env
from banking_agent.app.providers import LLMSettings, create_llm_client
from scripts.evaluate_real_llm_e2e import (
    FORBIDDEN_PATTERN_RUBRICS, RESPONSE_FACT_RUBRICS, SemanticResponseEvaluator,
)
from scripts import evaluate_real_llm_e2e as core
from scripts import run_single_turn_fuse_freeze as complex_freeze

EXPANDED = ROOT / "tests/fixtures/evaluation/multi_turn_semantic/v1/expanded_e2e_annotations.json"
SUPPLEMENTS = ROOT / "tests/fixtures/evaluation/semantic/v1/response_supplements_v1.json"


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _load(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))

def _verdict_key(row: dict) -> tuple:
    return (row["population"], row.get("sequence_id"), row.get("case_id"), row.get("repeat"))

def _retryable_unavailable(row: dict) -> bool:
    return (
        row.get("scope") == "answer_or_clarify"
        and not row.get("scored")
        and row.get("judge", {}).get("status") == "unavailable"
    )

def _missing_judge_rubrics(response_gold: dict) -> list[str]:
    missing = [f"fact:{group.get('id')}" for group in response_gold.get("required_fact_groups", []) if group.get("id") not in RESPONSE_FACT_RUBRICS]
    missing.extend(f"forbidden:{pattern}" for pattern in response_gold.get("forbidden_patterns", []) if pattern not in FORBIDDEN_PATTERN_RUBRICS)
    return missing


def _rubrics() -> tuple[dict, dict, dict, dict]:
    core_gold = {x["source_case_id"]: x.get("response", {}) for x in core._load_semantic_scorecard() .values()}
    complex_gold = {x["case_id"]: x["semantic_gold"].get("response", {}) for x in complex_freeze._load_cases()}
    annotations = {x["sequence_id"]: x["turn_oracles"] for x in _load(EXPANDED)["sequences"]}
    expanded_gold = {(seq, item["turn_id"]): item.get("response", {}) for seq, items in annotations.items() for item in items}
    supplements = _load(SUPPLEMENTS)
    if supplements.get("schema_version") != "response-supplements-v1":
        raise ValueError("unsupported_response_supplements_schema")
    complex_gold.update(supplements.get("complex", {}))
    for key, response_gold in supplements.get("expanded", {}).items():
        sequence_id, turn_id = key.rsplit(":", 1)
        expanded_gold[(sequence_id, int(turn_id))] = response_gold
    legacy_gold = {}
    for key, response_gold in supplements.get("legacy", {}).items():
        sequence_id, turn_id = key.rsplit(":", 1)
        legacy_gold[(sequence_id, int(turn_id))] = response_gold
    return core_gold, complex_gold, expanded_gold, legacy_gold


def _candidate_rows(unified: dict, legacy: dict) -> list[dict]:
    core_gold, complex_gold, expanded_gold, legacy_gold = _rubrics()
    result = []
    core_questions={x["case_id"]:x["input"]["user_text"] if isinstance(x.get("input"),dict) else x.get("input") for x in core._load_cases()}
    complex_questions={x["case_id"]:x["input"] for x in complex_freeze._load_cases()}
    expanded_questions={(sequence["id"], index): turn["text"] for sequence, _ in core._load_expanded_multi_turn() for index, turn in enumerate(sequence["turns"], start=1)}
    legacy_questions = {
        (sequence["sequence_id"], turn_id): turn["user_text"]
        for path in sorted(core.MULTI_TURN_ROOT.glob("**/*.json"))
        for sequence in [json.loads(path.read_text(encoding="utf-8"))]
        for turn_id, turn in enumerate(sequence["turns"], start=1)
    }
    def add(population, row, answer, action, question, gold, *, text_quality_eligible=True):
        result.append({"population": population, "source": row, "answer": answer, "action": action, "question": question, "response_gold": gold or {}, "text_quality_eligible": text_quality_eligible})
    for row in unified["core_attempts"]:
        seq = row.get("sequence_id") or ""
        action = row["actual"].get("action")
        if seq.startswith("MTX-"):
            add("expanded_multi_turn", row, row["response_text"], action, expanded_questions.get((seq, row["case_id"]), ""), expanded_gold.get((seq, row["case_id"])))
        elif not seq:
            add("core_single_turn", row, row["response_text"], action, core_questions.get(row["case_id"], ""), core_gold.get(row["case_id"]))
    for row in unified["complex_attempts"]:
        add("complex_single_turn", row, row.get("final_response_text"), row["actual"].get("action"), complex_questions.get(row["case_id"], ""), complex_gold.get(row["case_id"]))
    # Reconciliation replaces, rather than adds to, raw-v1 legacy attempts.
    for row in legacy["rows"]:
        sequence_id, turn_id = row["sequence_id"], row["case_id"]
        add(
            "legacy_multi_turn_reconciliation", row, row["response_text"], row["actual"].get("action"),
            legacy_questions.get((sequence_id, turn_id), ""),
            legacy_gold.get((sequence_id, turn_id)),
            text_quality_eligible=(sequence_id, turn_id) in legacy_gold,
        )
    return result


async def evaluate(
    unified_path: Path, legacy_path: Path, *, dry_run: bool, resume_path: Path | None = None,
    legacy_only: bool = False,
) -> dict:
    unified, legacy = _load(unified_path), _load(legacy_path)
    rows = _candidate_rows(unified, legacy)
    if legacy_only:
        rows = [row for row in rows if row["population"] == "legacy_multi_turn_reconciliation"]
    resume = _load(resume_path) if resume_path else None
    previous_by_key = {}
    if resume:
        sources = resume.get("sources", {})
        if sources.get("unified_sha256") != _sha(unified_path) or sources.get("legacy_sha256") != _sha(legacy_path):
            raise ValueError("resume_report_source_hash_mismatch")
        previous_by_key = {_verdict_key(row): row for row in resume.get("verdicts", [])}
    evaluator = None
    if not dry_run:
        load_local_env()
        model = os.environ.get("BANKING_AGENT_LLM_MODEL", "").strip()
        if not model: raise RuntimeError("BANKING_AGENT_LLM_MODEL_required_for_response_judging")
        settings = LLMSettings.from_environment()
        evaluator = SemanticResponseEvaluator(create_llm_client(settings), model=model, settings=settings)
    verdicts=[]
    retried_unavailable_candidates = 0
    for item in rows:
        action=item["action"]
        base={"population":item["population"], "sequence_id":item["source"].get("sequence_id"), "case_id":item["source"].get("case_id"), "repeat":item["source"].get("repeat"), "action":action}
        previous = previous_by_key.get(_verdict_key(base))
        if previous and not _retryable_unavailable(previous):
            verdicts.append(previous)
            continue
        if previous:
            retried_unavailable_candidates += 1
        if not item["text_quality_eligible"]:
            verdicts.append({**base,"scope":"non_answer_structural_safety_only","scored":False,"reason":"outside_reviewed_text_population"}); continue
        if action not in {"ANSWER","CLARIFY"}:
            verdicts.append({**base,"scope":"non_answer_structural_safety_only","scored":False,"reason":"outside_text_quality_scope"}); continue
        if not item["response_gold"]:
            verdicts.append({**base,"scope":"answer_or_clarify","scored":False,"reason":"missing_reviewed_response_rubric"}); continue
        missing = _missing_judge_rubrics(item["response_gold"])
        if missing:
            verdicts.append({**base,"scope":"answer_or_clarify","scored":False,"reason":"missing_judge_rubric","missing_judge_rubrics":missing}); continue
        if dry_run:
            verdicts.append({**base,"scope":"answer_or_clarify","scored":False,"reason":"dry_run"}); continue
        assessment, metadata = await evaluator.assess(
            question=item["question"], answer=item["answer"], response_gold=item["response_gold"],
            request_id=f"final-semantic-{item['population']}-{base['repeat']}-{base['sequence_id'] or 'single'}-{base['case_id']}",
        )
        verdicts.append({**base,"scope":"answer_or_clarify","scored":assessment is not None,"response_passed":None if assessment is None else all(assessment.required_facts.values()) and assessment.safety_passed is not False,"required_fact_results":None if assessment is None else assessment.required_facts,"safety_passed":None if assessment is None else assessment.safety_passed,"judge":metadata})
    grouped=defaultdict(list)
    for row in verdicts: grouped[row["population"]].append(row)
    summary={}
    for name, items in grouped.items():
        in_scope=[x for x in items if x["scope"]=="answer_or_clarify"]
        scored=[x for x in in_scope if x["scored"]]
        summary[name]={"all_recorded_responses":len(items),"answer_or_clarify_candidates":len(in_scope),"scored":len(scored),"response_passed":sum(x.get("response_passed") is True for x in scored),"unscored":len(in_scope)-len(scored),"non_answer_structural_safety_only":sum(x["scope"]=="non_answer_structural_safety_only" for x in items)}
    return {"evaluation":"final_response_semantic_v1","generated_at":datetime.now(UTC).isoformat(),"method":"llm_semantic_v1_minimum_acceptability","sources":{"unified_report":str(unified_path),"unified_sha256":_sha(unified_path),"legacy_reconciliation":str(legacy_path),"legacy_sha256":_sha(legacy_path)},"scope":{"judge_actions":["ANSWER","CLARIFY"],"non_answer":"structural safety only; no text-quality headline","temperature":0,"dry_run":dry_run,"legacy_only":legacy_only},"resume":None if resume is None else {"source_report":str(resume_path),"source_sha256":_sha(resume_path),"reused_verdicts":len(verdicts)-retried_unavailable_candidates,"retried_unavailable_candidates":retried_unavailable_candidates},"summary":summary,"verdicts":verdicts}


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--unified-report",type=Path,default=ROOT/"artifacts/evaluation/unified_freeze_20261023_182527/report.json")
    p.add_argument("--legacy-report",type=Path,default=ROOT/"artifacts/evaluation/legacy_reconciliation_v2_20261023/report.json")
    p.add_argument("--output",type=Path,default=ROOT/"artifacts/evaluation/final_response_semantic_v1/report.json")
    p.add_argument("--resume-report",type=Path,help="Reuse all prior verdicts and retry only judge-unavailable rows.")
    p.add_argument("--legacy-only",action="store_true",help="Judge only the legacy reconciliation population.")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args(); report=asyncio.run(evaluate(a.unified_report,a.legacy_report,dry_run=a.dry_run,resume_path=a.resume_report,legacy_only=a.legacy_only)); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"report_json":str(a.output),"summary":report["summary"]},ensure_ascii=False))

if __name__=="__main__": main()
