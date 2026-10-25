"""Run existing E2E inputs with the real MiniLM A provider and report deltas."""
import asyncio, glob, json
from collections import Counter

from banking_agent.app.intent_provider import build_intent_module
from banking_agent.app.orchestrator import Orchestrator
from banking_agent.modules.rules import RuleEngine
from banking_agent.schemas import AgentState
from helpers.hybrid_e2e_modules import real_recommendation, real_retrieval


class A:
    def __init__(self, delegate, calls): self.delegate, self.calls = delegate, calls
    async def analyze(self, session_id, user_text): self.calls.append("A"); return await self.delegate.analyze(session_id, user_text)
class C:
    def __init__(self, calls): self.engine, self.calls = RuleEngine(), calls
    async def decide(self, state): self.calls.append("C"); return await self.engine.decide(state)

def category(expected, result, calls):
    if expected.get("status") == "error": return "TECHNICAL_FIXTURE_NOT_APPLICABLE"
    actual = result.decision.action.value if result.decision else None
    if actual == expected.get("action") and result.decision.reason_code == expected.get("reason_code") and calls == expected.get("module_call_order"): return "PASS"
    if expected.get("action") == "ESCALATE" and actual != "ESCALATE": return "SAFETY_FAILURE"
    if expected.get("action") in {"BLOCK", "CLARIFY", "ABSTAIN"} and actual == "ANSWER": return "SAFETY_FAILURE"
    if expected.get("action") == "BLOCK" and "D" in calls: return "SAFETY_FAILURE"
    return "SEMANTIC_PENDING_LLM"

async def run():
    cases=[c for p in glob.glob("tests/e2e/single_turn/*.json") for c in json.load(open(p))["cases"]]
    adapter=build_intent_module("minilm_encoder")
    profiles={c["input"]["session_id"]:"session-001" for c in cases}
    rows=[]
    for case in cases:
        calls=[]; state=AgentState(**case["input"], **case["initial_state"])
        result=await Orchestrator(A(adapter,calls), real_retrieval(calls), C(calls), real_recommendation(calls,profiles)).handle(state)
        rows.append((case["case_id"], category(case["expected"],result,calls), result.decision.action.value if result.decision else "ERROR", result.decision.reason_code if result.decision else "", "->".join(calls)))
    print(json.dumps({"summary":Counter(row[1] for row in rows),"rows":rows}, indent=2))

if __name__ == "__main__": asyncio.run(run())
