"""BANKING77 fine-grained label space and its mapping to operational intents.

BANKING77 (Casanueva et al., 2020) is the training and evaluation source for
the intent classifier: 13,083 English banking queries over 77 intents, with a
10,003 / 3,080 train / test split.

The 77 labels are *not* the intents the agent emits. They are the evaluation
space for the Part A Macro-F1 experiment; :data:`BANKING77_TO_OPERATIONAL_INTENT`
is the bridge to the coarser routes that C and E switch on. The mapping is a
first proposal for C/E review and lives here so that it can be validated
offline, without downloading the dataset.
"""

from __future__ import annotations

from .taxonomy import (
    INTENT_CARD_FEE_ENQUIRY,
    INTENT_FEE_COMPLAINT,
    INTENT_FRAUD_SUSPICION,
    INTENT_POLICY_ENQUIRY,
    INTENT_UNAUTHORIZED_TRANSACTION,
)

BANKING77_LABELS: tuple[str, ...] = (
    "activate_my_card",
    "age_limit",
    "apple_pay_or_google_pay",
    "atm_support",
    "automatic_top_up",
    "balance_not_updated_after_bank_transfer",
    "balance_not_updated_after_cheque_or_cash_deposit",
    "beneficiary_not_allowed",
    "cancel_transfer",
    "card_about_to_expire",
    "card_acceptance",
    "card_arrival",
    "card_delivery_estimate",
    "card_linking",
    "card_not_working",
    "card_payment_fee_charged",
    "card_payment_not_recognised",
    "card_payment_wrong_exchange_rate",
    "card_swallowed",
    "cash_withdrawal_charge",
    "cash_withdrawal_not_recognised",
    "change_pin",
    "compromised_card",
    "contactless_not_working",
    "country_support",
    "declined_card_payment",
    "declined_cash_withdrawal",
    "declined_transfer",
    "direct_debit_payment_not_recognised",
    "disposable_card_limits",
    "edit_personal_details",
    "exchange_charge",
    "exchange_rate",
    "exchange_via_app",
    "extra_charge_on_statement",
    "failed_transfer",
    "fiat_currency_support",
    "get_disposable_virtual_card",
    "get_physical_card",
    "getting_spare_card",
    "getting_virtual_card",
    "lost_or_stolen_card",
    "lost_or_stolen_phone",
    "order_physical_card",
    "passcode_forgotten",
    "pending_card_payment",
    "pending_cash_withdrawal",
    "pending_top_up",
    "pending_transfer",
    "pin_blocked",
    "receiving_money",
    "Refund_not_showing_up",
    "request_refund",
    "reverted_card_payment?",
    "supported_cards_and_currencies",
    "terminate_account",
    "top_up_by_bank_transfer_charge",
    "top_up_by_card_charge",
    "top_up_by_cash_or_cheque",
    "top_up_failed",
    "top_up_limits",
    "top_up_reverted",
    "topping_up_by_card",
    "transaction_charged_twice",
    "transfer_fee_charged",
    "transfer_into_account",
    "transfer_not_received_by_recipient",
    "transfer_timing",
    "unable_to_verify_identity",
    "verify_my_identity",
    "verify_source_of_funds",
    "verify_top_up",
    "virtual_card_not_working",
    "visa_or_mastercard",
    "why_verify_identity",
    "wrong_amount_of_cash_received",
    "wrong_exchange_rate_for_cash_withdrawal",
)
"""The 77 BANKING77 intents in published label-id order (index == label id)."""

DEFAULT_OPERATIONAL_INTENT = INTENT_POLICY_ENQUIRY
"""Enquiry bucket used for every fine-grained label without a stronger route."""

_OPERATIONAL_GROUPS: dict[str, tuple[str, ...]] = {
    INTENT_CARD_FEE_ENQUIRY: (
        "card_payment_fee_charged",
        "cash_withdrawal_charge",
        "exchange_charge",
        "top_up_by_bank_transfer_charge",
        "top_up_by_card_charge",
        "transfer_fee_charged",
    ),
    INTENT_FEE_COMPLAINT: (
        "extra_charge_on_statement",
        "transaction_charged_twice",
        "wrong_amount_of_cash_received",
        "card_payment_wrong_exchange_rate",
        "wrong_exchange_rate_for_cash_withdrawal",
        "Refund_not_showing_up",
        "request_refund",
    ),
    INTENT_UNAUTHORIZED_TRANSACTION: (
        "card_payment_not_recognised",
        "cash_withdrawal_not_recognised",
        "direct_debit_payment_not_recognised",
    ),
    INTENT_FRAUD_SUSPICION: (
        "compromised_card",
        "lost_or_stolen_card",
        "lost_or_stolen_phone",
    ),
}

BANKING77_TO_OPERATIONAL_INTENT: dict[str, str] = {
    label: intent for intent, labels in _OPERATIONAL_GROUPS.items() for label in labels
}


def operational_intent_for(label: str) -> str:
    """Map a fine-grained BANKING77 label to its operational route."""
    return BANKING77_TO_OPERATIONAL_INTENT.get(label, DEFAULT_OPERATIONAL_INTENT)


def unmapped_labels() -> tuple[str, ...]:
    """Labels with no explicit route; they take ``DEFAULT_OPERATIONAL_INTENT``.

    Informational rather than an error: the enquiry bucket is the intended
    default for the long tail of BANKING77 service questions.
    """
    claimed = set(BANKING77_TO_OPERATIONAL_INTENT)
    return tuple(label for label in BANKING77_LABELS if label not in claimed)


def unresolved_intents() -> tuple[str, ...]:
    """Group entries that do not exist in the published label space."""
    known = set(BANKING77_LABELS)
    return tuple(
        label for label in BANKING77_TO_OPERATIONAL_INTENT if label not in known
    )
