"""Tests for the Intent / Risk / Entity module (Part A).

The expected values come from ``docs/scenario_table.md`` (core scenarios
S01-S08) and ``docs/module_api_contract.md`` (section A), not from the
implementation.
"""

import sys
import unittest

from banking_agent.modules.intent import (
    IntentModuleAdapter,
    TrainedIntentClassifier,
    analyze,
    classify,
    classify_by_rules,
    extract_entities,
)
from banking_agent.modules.intent import calibrate_project_route
from banking_agent.modules.intent.banking77 import (
    BANKING77_LABELS,
    BANKING77_TO_OPERATIONAL_INTENT,
    DEFAULT_OPERATIONAL_INTENT,
    operational_intent_for,
    unmapped_labels,
    unresolved_intents,
)
from banking_agent.modules.intent.taxonomy import (
    ENTITY_TYPES,
    OPERATIONAL_INTENTS,
    UNKNOWN_INTENT,
)
from banking_agent.schemas import IntentResult, RiskLevel
from banking_agent.schemas.state import Entity, UnderstandingResult

# (scenario id, user text, intent, confidence, risk_level)
SCENARIOS = (
    (
        "S01",
        "What is the replacement fee for my card?",
        "card_fee_enquiry",
        0.94,
        RiskLevel.LOW,
    ),
    (
        "S02",
        "I was charged a fee I do not understand.",
        "fee_complaint",
        0.92,
        RiskLevel.MEDIUM,
    ),
    (
        "S03",
        "Someone used my card without my permission.",
        "unauthorized_transaction",
        0.97,
        RiskLevel.HIGH,
    ),
    (
        "S04",
        "I think this transfer may be a scam.",
        "fraud_suspicion",
        0.95,
        RiskLevel.HIGH,
    ),
    (
        "S05",
        "Can you recommend a savings product while my fee complaint is still open?",
        "product_recommendation",
        0.91,
        RiskLevel.LOW,
    ),
    (
        "S06",
        "My complaint is resolved. Can you recommend a suitable savings product?",
        "product_recommendation",
        0.93,
        RiskLevel.LOW,
    ),
    (
        "S07",
        "I need help with that thing from before.",
        "UNKNOWN",
        0.31,
        RiskLevel.UNKNOWN,
    ),
    (
        "S08",
        "What is the bank policy for crypto wallet recovery?",
        "policy_enquiry",
        0.88,
        RiskLevel.LOW,
    ),
)


class ScenarioContractTests(unittest.TestCase):
    def test_pinned_values_match_the_scenario_table(self) -> None:
        for scenario_id, text, intent, confidence, risk in SCENARIOS:
            with self.subTest(scenario=scenario_id):
                result = classify(text)
                self.assertEqual(result.intent, intent)
                self.assertAlmostEqual(result.confidence or 0.0, confidence, places=2)
                self.assertEqual(result.risk_level, risk)

    def test_rule_layer_reproduces_scenario_intent_and_risk(self) -> None:
        for scenario_id, text, intent, _confidence, risk in SCENARIOS:
            with self.subTest(scenario=scenario_id):
                result = classify_by_rules(text)
                self.assertEqual(result.intent, intent)
                self.assertEqual(result.risk_level, risk)

    def test_result_uses_the_shared_schema_model(self) -> None:
        self.assertIsInstance(classify("Hello there."), UnderstandingResult)

    def test_vocabulary_is_shared_with_the_contract(self) -> None:
        for scenario_id, text, *_rest in SCENARIOS:
            with self.subTest(scenario=scenario_id):
                result = classify(text)
                self.assertIn(result.intent, OPERATIONAL_INTENTS | {UNKNOWN_INTENT})
                self.assertIsInstance(result.risk_level, RiskLevel)
                self.assertGreaterEqual(result.confidence or 0.0, 0.0)
                self.assertLessEqual(result.confidence or 0.0, 1.0)

    def test_classification_is_deterministic(self) -> None:
        text = "Someone used my card without my permission."
        self.assertEqual(classify(text).model_dump(), classify(text).model_dump())


class RiskSignalTests(unittest.TestCase):
    def test_high_risk_phrase_is_not_downgraded_by_unknown_intent(self) -> None:
        result = classify_by_rules(
            "Hmm, I am not sure but I think someone hacked my account."
        )
        self.assertEqual(result.intent, UNKNOWN_INTENT)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)

    def test_high_risk_survives_low_confidence(self) -> None:
        result = classify_by_rules("Not sure about this, but my card was stolen.")
        self.assertLess(result.confidence or 1.0, 0.9)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)

    def test_social_engineering_transfer_report_is_high_risk(self) -> None:
        result = classify_by_rules(
            "I think someone is trying to trick me into making this transfer."
        )
        self.assertEqual(result.risk_level, RiskLevel.HIGH)

    def test_fee_complaint_baseline_is_medium(self) -> None:
        result = classify_by_rules("I was charged a fee I do not understand.")
        self.assertEqual(result.risk_level, RiskLevel.MEDIUM)

    def test_unknown_risk_is_not_low(self) -> None:
        result = classify("I need help with that thing from before.")
        self.assertEqual(result.risk_level, RiskLevel.UNKNOWN)
        self.assertNotEqual(result.risk_level, RiskLevel.LOW)


class EntityExtractionTests(unittest.TestCase):
    def test_scenario_example_extracts_payment_method(self) -> None:
        entities = extract_entities("Someone used my card without my permission.")
        self.assertIn(("payment_method", "card"), {(e.type, e.value) for e in entities})

    def test_amount_currency_and_time_are_extracted(self) -> None:
        entities = extract_entities("I was charged SGD 120 yesterday by mistake.")
        found = {(e.type, e.value) for e in entities}
        self.assertIn(("amount", "sgd 120"), found)
        self.assertIn(("currency", "sgd"), found)
        self.assertIn(("relative_time", "yesterday"), found)

    def test_month_names_need_date_context(self) -> None:
        modal = {
            (entity.type, entity.value)
            for entity in extract_entities("I think this transfer may be a scam.")
        }
        self.assertNotIn(("date", "may"), modal)
        verb = {
            (entity.type, entity.value)
            for entity in extract_entities("I will march to the branch.")
        }
        self.assertNotIn(("date", "march"), verb)

    def test_month_names_in_date_context_are_extracted(self) -> None:
        cases = {
            "My card was charged on 12 May.": "12 may",
            "In May I lost my card.": "may",
            "The charge happened in March 2025.": "march 2025",
            "It happened on May 12, 2025.": "may 12, 2025",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                dates = {
                    entity.value
                    for entity in extract_entities(text)
                    if entity.type == "date"
                }
                self.assertIn(expected, dates)

    def test_bare_ordinals_are_not_dates(self) -> None:
        self.assertNotIn(
            "1st",
            {e.value for e in extract_entities("This is my 1st card.")},
        )
        self.assertIn(
            "1st",
            {
                e.value
                for e in extract_entities("It happened on the 1st day of the month.")
            },
        )

    def test_longest_phrase_wins_over_its_substring(self) -> None:
        entities = extract_entities("Please block my credit card.")
        values = {e.value for e in entities if e.type == "payment_method"}
        self.assertIn("credit card", values)
        self.assertNotIn("card", values)

    def test_no_entities_for_plain_text(self) -> None:
        self.assertEqual(
            extract_entities("I need help with that thing from before."), []
        )

    def test_entities_are_unique_schema_models(self) -> None:
        entities = extract_entities(
            "My credit card and my card were both charged SGD 5."
        )
        self.assertTrue(all(isinstance(entity, Entity) for entity in entities))
        keys = [(entity.type, entity.value) for entity in entities]
        self.assertEqual(len(keys), len(set(keys)))
        for entity in entities:
            self.assertGreaterEqual(entity.confidence or 0.0, 0.0)
            self.assertLessEqual(entity.confidence or 1.0, 1.0)

    def test_entity_types_are_frozen(self) -> None:
        self.assertEqual(len(ENTITY_TYPES), 9)


class ContractAdapterTests(unittest.TestCase):
    def test_envelope_matches_the_api_contract(self) -> None:
        response = analyze(
            {
                "session_id": "session-001",
                "user_text": "Someone used my card without my permission.",
            }
        )
        self.assertEqual(response["status"], "ok")
        data = response["data"]
        self.assertEqual(set(data), {"intent", "confidence", "risk_level", "entities"})
        self.assertEqual(data["intent"], "unauthorized_transaction")
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertEqual(
            data["entities"][0],
            {"type": "payment_method", "value": "card", "confidence": 0.9},
        )

    def test_module_never_returns_decision_fields(self) -> None:
        response = analyze(
            {"session_id": "session-001", "user_text": "I think this is a scam."}
        )
        for forbidden in ("action", "reason_code", "next_state", "final_response"):
            self.assertNotIn(forbidden, response["data"])

    def test_blank_or_missing_text_is_a_technical_error(self) -> None:
        self.assertEqual(
            analyze({"session_id": "s", "user_text": "   "})["status"], "error"
        )
        self.assertEqual(analyze({"session_id": "s"})["status"], "error")


class ProjectRouteCalibrationTests(unittest.TestCase):
    def _model_result(self, intent: str = "policy_enquiry") -> UnderstandingResult:
        return UnderstandingResult(
            intent=intent, confidence=0.91, risk_level=RiskLevel.LOW
        )

    def test_unambiguous_project_routes_override_adjacent_banking77_route(self) -> None:
        cases = (
            ("Why was I charged this fee?", "fee_complaint", RiskLevel.MEDIUM),
            ("There is a card fee on my account that I do not recognise.", "fee_complaint", RiskLevel.MEDIUM),
            ("Which savings product should I choose?", "product_recommendation", RiskLevel.LOW),
            ("My fee dispute is still open. Which savings product should I choose?", "product_recommendation", RiskLevel.MEDIUM),
            ("I do not recognise a purchase on my card.", "unauthorized_transaction", RiskLevel.HIGH),
            ("Is this payment a scam?", "fraud_suspicion", RiskLevel.HIGH),
            ("Could you tell me the fee for replacing my bank card?", "card_fee_enquiry", RiskLevel.LOW),
            ("Can you help with that bank thing?", "UNKNOWN", RiskLevel.UNKNOWN),
            ("What happens if I lose access to a crypto wallet?", "policy_enquiry", RiskLevel.LOW),
        )
        for text, intent, risk in cases:
            with self.subTest(text=text):
                result = calibrate_project_route(text, self._model_result())
                self.assertEqual(result.intent, intent)
                self.assertEqual(result.risk_level, risk)

    def test_calibration_keeps_entities_from_the_model_result(self) -> None:
        original = UnderstandingResult(
            intent="policy_enquiry",
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            entities=[Entity(type="payment_method", value="card", confidence=0.9)],
        )
        calibrated = calibrate_project_route("Why was I charged this fee?", original)
        self.assertEqual(calibrated.entities, original.entities)


class Banking77MappingTests(unittest.TestCase):
    def test_label_space_is_the_published_set(self) -> None:
        self.assertEqual(len(BANKING77_LABELS), 77)
        self.assertEqual(len(set(BANKING77_LABELS)), 77)

    def test_label_ids_match_the_published_order(self) -> None:
        self.assertEqual(BANKING77_LABELS[0], "activate_my_card")
        self.assertEqual(BANKING77_LABELS[15], "card_payment_fee_charged")
        self.assertEqual(BANKING77_LABELS[22], "compromised_card")
        self.assertEqual(BANKING77_LABELS[51], "Refund_not_showing_up")
        self.assertEqual(
            BANKING77_LABELS[76], "wrong_exchange_rate_for_cash_withdrawal"
        )

    def test_every_label_resolves_to_an_operational_route(self) -> None:
        for label in BANKING77_LABELS:
            with self.subTest(label=label):
                self.assertIn(operational_intent_for(label), OPERATIONAL_INTENTS)

    def test_labels_without_an_explicit_route_use_the_enquiry_bucket(self) -> None:
        defaulted = unmapped_labels()
        self.assertEqual(
            len(defaulted) + len(BANKING77_TO_OPERATIONAL_INTENT),
            len(BANKING77_LABELS),
        )
        for label in defaulted:
            with self.subTest(label=label):
                self.assertEqual(
                    operational_intent_for(label), DEFAULT_OPERATIONAL_INTENT
                )

    def test_mapping_invents_no_labels(self) -> None:
        self.assertEqual(unresolved_intents(), ())

    def test_routes_are_operational_intents(self) -> None:
        self.assertIn(DEFAULT_OPERATIONAL_INTENT, OPERATIONAL_INTENTS)
        for label, intent in BANKING77_TO_OPERATIONAL_INTENT.items():
            with self.subTest(label=label):
                self.assertIn(intent, OPERATIONAL_INTENTS)
                self.assertEqual(operational_intent_for(label), intent)

    def test_unknown_labels_fall_back_to_the_enquiry_route(self) -> None:
        self.assertEqual(
            operational_intent_for("not_a_banking77_label"), DEFAULT_OPERATIONAL_INTENT
        )

    def test_risk_sensitive_labels_are_routed_to_risk_paths(self) -> None:
        for label in (
            "compromised_card",
            "lost_or_stolen_card",
            "lost_or_stolen_phone",
        ):
            with self.subTest(label=label):
                self.assertEqual(operational_intent_for(label), "fraud_suspicion")
        for label in (
            "card_payment_not_recognised",
            "cash_withdrawal_not_recognised",
            "direct_debit_payment_not_recognised",
        ):
            with self.subTest(label=label):
                self.assertEqual(
                    operational_intent_for(label), "unauthorized_transaction"
                )


class _StubPipeline:
    """Duck-typed stand-in for a fitted scikit-learn pipeline."""

    def __init__(
        self,
        label: str,
        proba: list[float] | None = None,
        scores: list[float] | None = None,
        classes: list[str] | None = None,
    ) -> None:
        self._label = label
        self._proba = proba
        self._scores = scores
        self.classes_ = classes

    def predict(self, texts):
        return [self._label for _ in texts]

    def predict_proba(self, texts):
        return [self._proba for _ in texts]

    def decision_function(self, texts):
        return [self._scores for _ in texts]


class _DecisionOnlyPipeline(_StubPipeline):
    predict_proba = None


class TrainedClassifierTests(unittest.TestCase):
    def test_fine_grained_label_is_routed_to_an_operational_intent(self) -> None:
        classifier = TrainedIntentClassifier(
            _StubPipeline("compromised_card", proba=[0.1, 0.9])
        )
        result = classifier.classify("Someone used my card without my permission.")
        self.assertEqual(result.intent, "fraud_suspicion")
        self.assertEqual(result.risk_level, RiskLevel.HIGH)
        self.assertAlmostEqual(result.confidence or 0.0, 0.9, places=6)
        self.assertIn(
            ("payment_method", "card"), {(e.type, e.value) for e in result.entities}
        )

    def test_confidence_falls_back_to_the_decision_margin(self) -> None:
        classifier = TrainedIntentClassifier(
            _DecisionOnlyPipeline("exchange_charge", scores=[8.0, 0.0, -8.0])
        )
        result = classifier.classify("What is the exchange charge?")
        self.assertEqual(result.intent, "card_fee_enquiry")
        self.assertGreater(result.confidence or 0.0, 0.99)

    def test_confidence_aggregates_probability_over_the_mapped_route(self) -> None:
        pipeline = _StubPipeline(
            "card_payment_fee_charged",
            proba=[0.30, 0.25, 0.45],
            classes=[
                "card_payment_fee_charged",
                "transfer_fee_charged",
                "card_arrival",
            ],
        )
        result = TrainedIntentClassifier(pipeline).classify("fee?")
        self.assertEqual(result.intent, "card_fee_enquiry")
        self.assertAlmostEqual(result.confidence or 0.0, 0.55, places=6)

    def test_confidence_uses_the_predicted_route_not_the_largest_route(self) -> None:
        pipeline = _StubPipeline(
            "card_payment_fee_charged",
            proba=[0.20, 0.15, 0.65],
            classes=[
                "card_payment_fee_charged",
                "transfer_fee_charged",
                "card_arrival",
            ],
        )
        result = TrainedIntentClassifier(pipeline).classify("fee?")
        self.assertEqual(result.intent, "card_fee_enquiry")
        self.assertAlmostEqual(result.confidence or 0.0, 0.35, places=6)

    def test_predict_labels_exposes_the_diagnostic_label(self) -> None:
        classifier = TrainedIntentClassifier(_StubPipeline("card_arrival", proba=[1.0]))
        self.assertEqual(
            classifier.predict_labels(["a", "b"]), ["card_arrival", "card_arrival"]
        )

    def test_batch_classification_matches_single_classification(self) -> None:
        classifier = TrainedIntentClassifier(
            _StubPipeline("card_payment_not_recognised", proba=[0.2, 0.7])
        )
        texts = ["I do not recognise this payment", "There is a charge I did not make"]
        batched = classifier.classify_many(texts)
        self.assertEqual(
            [result.model_dump() for result in batched],
            [classifier.classify(text).model_dump() for text in texts],
        )

    def test_module_stays_free_of_heavy_optional_dependencies(self) -> None:
        self.assertNotIn("sklearn", sys.modules)
        self.assertNotIn("torch", sys.modules)


class AsyncAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_adapter_satisfies_the_shared_intent_envelope(self) -> None:
        raw = await IntentModuleAdapter().analyze(
            "session-001", "Someone used my card without my permission."
        )
        result = IntentResult.model_validate(raw)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data.intent, "unauthorized_transaction")
        self.assertEqual(result.data.confidence, 0.97)
        self.assertEqual(result.data.risk_level, RiskLevel.HIGH)

    async def test_adapter_error_envelope_matches_the_shared_schema(self) -> None:
        raw = await IntentModuleAdapter().analyze("session-001", "   ")
        result = IntentResult.model_validate(raw)
        self.assertEqual(result.status, "error")
        self.assertIsNone(result.data)

    async def test_adapter_accepts_an_injected_classifier(self) -> None:
        def stub(text: str) -> UnderstandingResult:
            return UnderstandingResult(
                intent="fee_complaint",
                confidence=0.5,
                risk_level=RiskLevel.MEDIUM,
            )

        raw = await IntentModuleAdapter(classifier=stub).analyze("session", "text")
        result = IntentResult.model_validate(raw)
        self.assertEqual(result.data.intent, "fee_complaint")
        self.assertEqual(result.data.entities, [])


if __name__ == "__main__":
    unittest.main()
