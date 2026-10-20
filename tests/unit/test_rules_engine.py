"""Module C decisions against the shared Scenario Table and canonical schema."""

import unittest

from banking_agent.modules.rules import EvidenceArbitrator, RuleEngine
from banking_agent.schemas.enums import (
    Action, ComplaintStatus, ConsentStatus, HandoffStatus, RiskLevel,
)
from banking_agent.schemas.state import AgentState, RetrievedDocument, UnderstandingResult
from banking_agent.schemas.state import Decision


def make_state(
    intent: str,
    confidence: float,
    risk: RiskLevel,
    *,
    complaint: ComplaintStatus = ComplaintStatus.NONE,
    handoff: HandoffStatus = HandoffStatus.NOT_REQUIRED,
    consent: ConsentStatus = ConsentStatus.UNKNOWN,
    text: str = "Synthetic customer request",
    docs: list[RetrievedDocument] | None = None,
) -> AgentState:
    return AgentState(
        session_id="synthetic-session",
        user_text=text,
        understanding=UnderstandingResult(
            intent=intent, confidence=confidence, risk_level=risk
        ),
        complaint_status=complaint,
        handoff_status=handoff,
        consent=consent,
        retrieved_docs=docs or [],
    )


POLICY_DOC = RetrievedDocument(
    document_id="policy-card-fees-v1",
    title="Synthetic Card Fees Policy",
    source="NovaBank synthetic policy",
    score=0.89,
    excerpt="The synthetic replacement card fee is SGD 10.",
)


class ScenarioTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = RuleEngine()

    def test_s01_grounded_policy_enquiry(self) -> None:
        state = make_state(
            "card_fee_enquiry", 0.94, RiskLevel.LOW,
            text="What is the replacement fee for my card?",
        )
        precheck = self.rules.evaluate(state)
        self.assertEqual(precheck.status, "ok")
        self.assertEqual(precheck.data.action, Action.ANSWER)
        self.assertEqual(precheck.data.reason_code, "POLICY_RETRIEVAL_PERMITTED")

        state.retrieved_docs = [POLICY_DOC]
        postcheck = self.rules.evaluate(state, rag_status="ok")
        self.assertEqual(postcheck.data.action, Action.ANSWER)
        self.assertEqual(postcheck.data.reason_code, "POLICY_EVIDENCE_FOUND")

    def test_s02_fee_complaint_opens_case(self) -> None:
        state = make_state("fee_complaint", 0.92, RiskLevel.MEDIUM)
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.HANDLE_COMPLAINT)
        self.assertEqual(decision.reason_code, "FEE_COMPLAINT")
        self.assertEqual(decision.next_state.complaint_status, ComplaintStatus.OPEN)
        self.assertIsNone(decision.next_state.handoff_status)

    def test_s03_unauthorized_transaction_escalates(self) -> None:
        state = make_state("unauthorized_transaction", 0.97, RiskLevel.HIGH)
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.ESCALATE)
        self.assertEqual(decision.reason_code, "HIGH_RISK_TRANSACTION")
        self.assertEqual(decision.next_state.complaint_status, ComplaintStatus.OPEN)
        self.assertEqual(decision.next_state.handoff_status, HandoffStatus.ESCALATED)

    def test_s04_fraud_suspicion_escalates(self) -> None:
        state = make_state("fraud_suspicion", 0.95, RiskLevel.HIGH)
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.ESCALATE)
        self.assertEqual(decision.reason_code, "FRAUD_SUSPICION")
        self.assertEqual(decision.next_state.complaint_status, ComplaintStatus.OPEN)
        self.assertEqual(decision.next_state.handoff_status, HandoffStatus.ESCALATED)

    def test_s05_open_complaint_blocks_recommendation(self) -> None:
        state = make_state(
            "product_recommendation", 0.91, RiskLevel.LOW,
            complaint=ComplaintStatus.OPEN, consent=ConsentStatus.GRANTED,
        )
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.BLOCK)
        self.assertEqual(decision.reason_code, "UNRESOLVED_COMPLAINT")

    def test_s06_resolved_and_consented_recommendation(self) -> None:
        state = make_state(
            "product_recommendation", 0.93, RiskLevel.LOW,
            complaint=ComplaintStatus.RESOLVED, consent=ConsentStatus.GRANTED,
        )
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.RECOMMEND)
        self.assertEqual(decision.reason_code, "RECOMMENDATION_PERMITTED")
        self.assertIsNone(decision.next_state.complaint_status)

    def test_s07_low_confidence_clarifies(self) -> None:
        state = make_state("UNKNOWN", 0.31, RiskLevel.UNKNOWN)
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.CLARIFY)
        self.assertEqual(decision.reason_code, "LOW_INTENT_CONFIDENCE")

    def test_s08_no_reliable_evidence_abstains(self) -> None:
        state = make_state("policy_enquiry", 0.88, RiskLevel.LOW)
        self.assertEqual(self.rules.evaluate(state).data.action, Action.ANSWER)
        decision = self.rules.evaluate(state, rag_status="empty").data
        self.assertEqual(decision.action, Action.ABSTAIN)
        self.assertEqual(decision.reason_code, "INSUFFICIENT_EVIDENCE")


class RuleBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = RuleEngine()

    def test_high_risk_precedes_low_confidence(self) -> None:
        state = make_state("fraud_suspicion", 0.20, RiskLevel.HIGH)
        self.assertEqual(self.rules.evaluate(state).data.action, Action.ESCALATE)

    def test_urgent_customer_report_survives_wrong_classifier_label(self) -> None:
        state = make_state(
            "policy_enquiry", 0.24, RiskLevel.LOW,
            text="I think this transfer may be a scam.",
        )
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.ESCALATE)
        self.assertEqual(decision.reason_code, "FRAUD_SUSPICION")

    def test_lost_card_intent_escalates_even_when_risk_signal_is_low(self) -> None:
        state = make_state("lost_card", 0.90, RiskLevel.LOW)
        self.assertEqual(
            self.rules.evaluate(state).data.reason_code, "CARD_SECURITY_RISK"
        )

    def test_misclassified_lost_card_text_escalates(self) -> None:
        for text in ("I lost my card.", "My card is missing."):
            with self.subTest(text=text):
                state = make_state("policy_enquiry", 0.20, RiskLevel.LOW, text=text)
                decision = self.rules.evaluate(state).data
                self.assertEqual(decision.action, Action.ESCALATE)
                self.assertEqual(decision.reason_code, "CARD_SECURITY_RISK")

    def test_misclassified_account_and_credential_reports_keep_correct_reason(self) -> None:
        for text, reason in (
            ("My account was hacked.", "ACCOUNT_SECURITY_RISK"),
            ("My credentials were leaked.", "CREDENTIAL_SECURITY_RISK"),
        ):
            with self.subTest(text=text):
                state = make_state("policy_enquiry", 0.20, RiskLevel.LOW, text=text)
                decision = self.rules.evaluate(state).data
                self.assertEqual(decision.action, Action.ESCALATE)
                self.assertEqual(decision.reason_code, reason)
                self.assertEqual(decision.next_state.complaint_status, ComplaintStatus.OPEN)
                self.assertEqual(decision.next_state.handoff_status, HandoffStatus.ESCALATED)

    def test_open_complaint_precedes_low_confidence(self) -> None:
        state = make_state(
            "product_recommendation", 0.20, RiskLevel.LOW,
            complaint=ComplaintStatus.OPEN, consent=ConsentStatus.GRANTED,
        )
        result = self.rules.evaluate(state)
        self.assertEqual(result.data.reason_code, "UNRESOLVED_COMPLAINT")

    def test_customer_claim_of_resolution_does_not_change_state(self) -> None:
        state = make_state(
            "product_recommendation", 0.93, RiskLevel.LOW,
            complaint=ComplaintStatus.OPEN, consent=ConsentStatus.GRANTED,
            text="My complaint is resolved. Recommend a savings account.",
        )
        self.assertEqual(self.rules.evaluate(state).data.action, Action.BLOCK)

    def test_missing_consent_blocks_recommendation(self) -> None:
        state = make_state(
            "product_recommendation", 0.93, RiskLevel.LOW,
            complaint=ComplaintStatus.RESOLVED, consent=ConsentStatus.UNKNOWN,
        )
        self.assertEqual(self.rules.evaluate(state).data.reason_code, "CONSENT_REQUIRED")

    def test_misclassified_recommendation_cannot_bypass_complaint_gate(self) -> None:
        state = make_state(
            "policy_enquiry", 0.93, RiskLevel.LOW,
            complaint=ComplaintStatus.OPEN, consent=ConsentStatus.GRANTED,
            text="Can you recommend a savings product?",
        )
        self.assertEqual(
            self.rules.evaluate(state).data.reason_code, "UNRESOLVED_COMPLAINT"
        )

    def test_handoff_blocks_recommendation(self) -> None:
        state = make_state(
            "product_recommendation", 0.93, RiskLevel.LOW,
            complaint=ComplaintStatus.RESOLVED,
            handoff=HandoffStatus.PENDING,
            consent=ConsentStatus.GRANTED,
        )
        self.assertEqual(self.rules.evaluate(state).data.reason_code, "HANDOFF_ACTIVE")

    def test_risk_must_be_low_for_recommendation(self) -> None:
        state = make_state(
            "product_recommendation", 0.93, RiskLevel.MEDIUM,
            complaint=ComplaintStatus.RESOLVED, consent=ConsentStatus.GRANTED,
        )
        self.assertEqual(self.rules.evaluate(state).data.reason_code, "RISK_NOT_CLEARED")

    def test_account_specific_read_is_blocked_without_auth_state(self) -> None:
        state = make_state("check_balance", 0.95, RiskLevel.LOW)
        self.assertEqual(
            self.rules.evaluate(state).data.reason_code, "AUTHENTICATION_REQUIRED"
        )

    def test_misclassified_account_read_is_still_blocked(self) -> None:
        state = make_state(
            "policy_enquiry", 0.95, RiskLevel.LOW,
            text="What is my account balance?",
        )
        self.assertEqual(
            self.rules.evaluate(state).data.reason_code, "AUTHENTICATION_REQUIRED"
        )

    def test_transaction_execution_is_outside_synthetic_text_path(self) -> None:
        state = make_state("make_transfer", 0.95, RiskLevel.LOW)
        self.assertEqual(
            self.rules.evaluate(state).data.reason_code, "OPERATION_NOT_SUPPORTED"
        )

    def test_misclassified_transfer_request_is_still_blocked(self) -> None:
        state = make_state(
            "policy_enquiry", 0.95, RiskLevel.LOW,
            text="Please transfer money from my account.",
        )
        self.assertEqual(
            self.rules.evaluate(state).data.reason_code, "OPERATION_NOT_SUPPORTED"
        )

    def test_retrieval_error_and_mismatched_ok_status_fail_closed(self) -> None:
        state = make_state("policy_enquiry", 0.88, RiskLevel.LOW)
        self.assertEqual(
            self.rules.evaluate(state, rag_status="error").data.action,
            Action.ABSTAIN,
        )
        self.assertEqual(
            self.rules.evaluate(state, rag_status="ok").data.reason_code,
            "INSUFFICIENT_EVIDENCE",
        )

    def test_existing_open_case_is_not_reopened_during_high_risk_route(self) -> None:
        state = make_state(
            "fraud_suspicion", 0.95, RiskLevel.HIGH,
            complaint=ComplaintStatus.OPEN,
        )
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.ESCALATE)
        self.assertIsNone(decision.next_state.complaint_status)
        self.assertEqual(decision.next_state.handoff_status, HandoffStatus.ESCALATED)

    def test_repeat_complaint_does_not_create_another_case(self) -> None:
        state = make_state(
            "fee_complaint", 0.91, RiskLevel.MEDIUM,
            complaint=ComplaintStatus.OPEN,
        )
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.action, Action.HANDLE_COMPLAINT)
        self.assertEqual(decision.reason_code, "COMPLAINT_ALREADY_OPEN")
        self.assertIsNone(decision.next_state.complaint_status)

    def test_reviewing_complaint_stays_unresolved(self) -> None:
        state = make_state(
            "fee_complaint", 0.91, RiskLevel.MEDIUM,
            complaint=ComplaintStatus.UNDER_REVIEW,
        )
        decision = self.rules.evaluate(state).data
        self.assertEqual(decision.reason_code, "COMPLAINT_UNDER_REVIEW")
        self.assertIsNone(decision.next_state.complaint_status)

    def test_output_uses_contract_envelope_and_strings(self) -> None:
        state = make_state("fraud_suspicion", 0.95, RiskLevel.HIGH)
        payload = self.rules.evaluate(state).model_dump(mode="json")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"]["action"], "ESCALATE")
        self.assertEqual(payload["data"]["reason_code"], "FRAUD_SUSPICION")
        self.assertEqual(payload["data"]["next_state"]["handoff_status"], "ESCALATED")


class OrchestratorAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_calls_follow_e_orchestrator_contract(self) -> None:
        rules = RuleEngine()
        state = make_state(
            "card_fee_enquiry", 0.94, RiskLevel.LOW,
            text="What is the replacement fee for my card?",
        )

        first = await rules.decide(state)
        self.assertIsInstance(first, dict)
        self.assertEqual(first["data"]["action"], "ANSWER")
        self.assertEqual(first["data"]["reason_code"], "POLICY_RETRIEVAL_PERMITTED")

        state.decision = Decision.model_validate(first["data"])
        state.retrieved_docs = [POLICY_DOC]
        second = await rules.decide(state)
        self.assertEqual(second["data"]["action"], "ANSWER")
        self.assertEqual(second["data"]["reason_code"], "POLICY_EVIDENCE_FOUND")

    async def test_empty_retrieval_abstains_on_second_call(self) -> None:
        rules = RuleEngine()
        state = make_state("policy_enquiry", 0.88, RiskLevel.LOW)
        first = await rules.decide(state)
        state.decision = Decision.model_validate(first["data"])

        second = await rules.decide(state)
        self.assertEqual(second["data"]["action"], "ABSTAIN")
        self.assertEqual(second["data"]["reason_code"], "INSUFFICIENT_EVIDENCE")


class EvidenceArbitrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = EvidenceArbitrator()

    def test_relevant_policy_excerpt_passes_without_score_threshold(self) -> None:
        self.assertTrue(
            self.gate.assess(
                "What is the replacement fee for my card?", [POLICY_DOC]
            ).sufficient
        )
        low_score = POLICY_DOC.model_copy(update={"score": -4.2})
        self.assertTrue(
            self.gate.assess(
                "What is the replacement fee for my card?", [low_score]
            ).sufficient
        )

    def test_high_score_does_not_launder_wrong_topic(self) -> None:
        wrong = POLICY_DOC.model_copy(update={"score": 100.0})
        result = self.gate.assess(
            "What is the bank policy for crypto wallet recovery?", [wrong]
        )
        self.assertFalse(result.sufficient)
        self.assertEqual(result.reason_code, "EVIDENCE_SCOPE_MISMATCH")

    def test_missing_specific_detail_abstains_despite_related_card_excerpt(self) -> None:
        result = self.gate.assess(
            "What exact font family is printed on a replacement card?", [POLICY_DOC]
        )
        self.assertFalse(result.sufficient)

    def test_broad_card_overlap_does_not_support_a_different_attribute(self) -> None:
        result = self.gate.assess(
            "What is the exact colour of the replacement card?", [POLICY_DOC]
        )
        self.assertFalse(result.sufficient)
        self.assertEqual(result.reason_code, "EVIDENCE_SCOPE_MISMATCH")

    def test_fee_question_requires_a_value(self) -> None:
        vague = POLICY_DOC.model_copy(update={
            "excerpt": "The replacement card fee is listed in the policy."
        })
        result = self.gate.assess(
            "What is the replacement fee for my card?", [vague]
        )
        self.assertEqual(result.reason_code, "MISSING_REQUESTED_VALUE")

    def test_delivery_time_cannot_answer_a_fee_question(self) -> None:
        time_only = POLICY_DOC.model_copy(update={
            "excerpt": "The replacement card fee is pending. Delivery takes 5 days."
        })
        result = self.gate.assess(
            "What is the replacement fee for my card?", [time_only]
        )
        self.assertEqual(result.reason_code, "MISSING_REQUESTED_VALUE")

    def test_shipping_price_cannot_substitute_for_replacement_fee(self) -> None:
        shipping_only = POLICY_DOC.model_copy(update={
            "excerpt": "The replacement card fee is listed separately; express shipping costs SGD 10."
        })
        result = self.gate.assess(
            "What is the replacement fee for my card?", [shipping_only]
        )
        self.assertEqual(result.reason_code, "MISSING_REQUESTED_VALUE")

    def test_joined_shipping_price_cannot_substitute_for_replacement_fee(self) -> None:
        for joiner in (",", " and", " —"):
            with self.subTest(joiner=joiner):
                shipping_only = POLICY_DOC.model_copy(update={
                    "excerpt": (
                        "The replacement card fee is pending"
                        f"{joiner} express shipping costs SGD 10."
                    )
                })
                result = self.gate.assess(
                    "What is the replacement fee for my card?", [shipping_only]
                )
                self.assertEqual(result.reason_code, "MISSING_REQUESTED_VALUE")

    def test_one_unrelated_rendered_doc_blocks_whole_answer(self) -> None:
        other = RetrievedDocument(
            document_id="unrelated-doc", title="Savings product",
            source="Synthetic policy", score=0.9,
            excerpt="The savings account has a fictional eligibility rule.",
        )
        self.assertFalse(
            self.gate.assess(
                "What is the replacement fee for my card?", [POLICY_DOC, other]
            ).sufficient
        )

    def test_reason_specific_replacement_price_requires_clarification(self) -> None:
        loss_policy = POLICY_DOC.model_copy(update={
            "excerpt": "Loss replacement costs SGD 15; express shipping costs SGD 10."
        })
        state = make_state(
            "card_fee_enquiry", 0.94, RiskLevel.LOW,
            text="What is the replacement fee for my card?", docs=[loss_policy],
        )
        decision = RuleEngine().evaluate(state, rag_status="ok").data
        self.assertEqual(decision.action, Action.CLARIFY)
        self.assertEqual(decision.reason_code, "REPLACEMENT_REASON_REQUIRED")

        specific = self.gate.assess(
            "How much does replacing a lost card cost?", [loss_policy]
        )
        self.assertTrue(specific.sufficient)

    def test_condition_wording_still_requires_replacement_reason(self) -> None:
        loss_policy = POLICY_DOC.model_copy(update={
            "document_id": "lost-card-price",
            "title": "Lost card replacement",
            "excerpt": "For a lost card, replacement is SGD 15.",
        })
        generic = self.gate.assess(
            "What is the replacement fee for my card?", [loss_policy]
        )
        self.assertEqual(generic.reason_code, "REPLACEMENT_REASON_REQUIRED")
        specific = self.gate.assess(
            "How much does replacing a lost card cost?", [loss_policy]
        )
        self.assertTrue(specific.sufficient)

    def test_specific_replacement_fee_does_not_use_shipping_price(self) -> None:
        shipping_only = POLICY_DOC.model_copy(update={
            "title": "Lost card replacement",
            "excerpt": "For a lost card, express shipping costs SGD 10; replacement fee is pending.",
        })
        result = self.gate.assess(
            "How much does replacing a lost card cost?", [shipping_only]
        )
        self.assertEqual(result.reason_code, "MISSING_REQUESTED_VALUE")


if __name__ == "__main__":
    unittest.main()
