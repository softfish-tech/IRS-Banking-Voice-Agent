"""Scenario-scripted test doubles, not production domain implementations."""
from copy import deepcopy

class ScriptedModules:
    def __init__(self, outputs):
        self.outputs = deepcopy(outputs)
        self.calls = []
        self.rule_inputs = []
        self.rule_index = 0

    async def analyze(self, session_id, user_text):
        self.calls.append("A")
        return deepcopy(self.outputs["A"])

    async def retrieve(self, query, top_k):
        self.calls.append("B")
        return deepcopy(self.outputs["B"])

    async def decide(self, state):
        self.calls.append("C")
        self.rule_inputs.append(state.model_copy(deep=True))
        result = self.outputs["C"][self.rule_index]
        self.rule_index += 1
        return deepcopy(result)

    async def recommend(self, session_id, complaint_status, handoff_status, consent):
        self.calls.append("D")
        return deepcopy(self.outputs["D"])
