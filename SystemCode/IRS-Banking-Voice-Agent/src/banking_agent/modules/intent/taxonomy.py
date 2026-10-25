"""Controlled vocabulary for the Intent / Risk / Entity module (Part A).

Everything this module emits is defined here once:

* the operational intent names that C, D, and E switch on;
* the risk vocabulary and the phrase/baseline rules behind it;
* the entity-type vocabulary and its gazetteers.

``docs/scenario_table.md`` and ``docs/module_api_contract.md`` are the
acceptance sources for these names, so they are frozen here and must not be
re-spelled anywhere else in the codebase.

``UNKNOWN_INTENT`` and ``RiskLevel.UNKNOWN`` are deliberately distinct: the
first means "no supported intent matched", the second means "risk could not be
assessed". ``RiskLevel.UNKNOWN`` is *not* ``RiskLevel.LOW``.
"""

from __future__ import annotations

from banking_agent.schemas.enums import RiskLevel

UNKNOWN_INTENT = "UNKNOWN"
"""Intent value used when no operational intent is supported by the text."""

# --------------------------------------------------------------------------- #
# Operational intents (docs/scenario_table.md, core scenarios S01-S08)
# --------------------------------------------------------------------------- #

INTENT_CARD_FEE_ENQUIRY = "card_fee_enquiry"
INTENT_FEE_COMPLAINT = "fee_complaint"
INTENT_UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
INTENT_FRAUD_SUSPICION = "fraud_suspicion"
INTENT_PRODUCT_RECOMMENDATION = "product_recommendation"
INTENT_POLICY_ENQUIRY = "policy_enquiry"

OPERATIONAL_INTENTS = frozenset(
    {
        INTENT_CARD_FEE_ENQUIRY,
        INTENT_FEE_COMPLAINT,
        INTENT_UNAUTHORIZED_TRANSACTION,
        INTENT_FRAUD_SUSPICION,
        INTENT_PRODUCT_RECOMMENDATION,
        INTENT_POLICY_ENQUIRY,
    }
)

# Ordered highest-priority first; the order also breaks equal-score ties.
INTENT_PRIORITY = (
    INTENT_FRAUD_SUSPICION,
    INTENT_UNAUTHORIZED_TRANSACTION,
    INTENT_FEE_COMPLAINT,
    INTENT_PRODUCT_RECOMMENDATION,
    INTENT_CARD_FEE_ENQUIRY,
    INTENT_POLICY_ENQUIRY,
)

INTENT_PATTERNS: dict[str, tuple[tuple[str, float], ...]] = {
    INTENT_FRAUD_SUSPICION: (
        (r"\bscam\b", 3.0),
        (r"\bfraud\w*\b", 3.0),
        (r"\bphishing\b", 3.0),
        (r"\bsuspicious\b", 2.0),
    ),
    INTENT_UNAUTHORIZED_TRANSACTION: (
        (r"\bwithout my (?:permission|consent|authori[sz]ation|knowledge)\b", 3.0),
        (r"\bunauthori[sz]ed\b", 3.0),
        (r"\bunrecogni[sz]ed\b", 3.0),
        (r"\bsomeone (?:used|has used|took|has taken|paid|has paid|withdrew)\b", 3.0),
        (
            r"\b(?:did ?n[o']?t|never|do not|don'?t)\s+(?:make|authori[sz]e|approve)\b",
            3.0,
        ),
        (r"\bnot me\b", 2.0),
        (r"\bnot mine\b", 2.0),
    ),
    INTENT_FEE_COMPLAINT: (
        (r"\bcharged (?:a|an|the)? ?fee\b", 3.0),
        (r"\bcharged twice\b", 3.0),
        (r"\bovercharg\w+\b", 3.0),
        (r"\bfee\b.{0,30}\b(?:i do ?n[o']?t|do not|don'?t|unclear|why)\b", 2.0),
        (r"\bcomplain\w*\b", 2.0),
        (r"\bdispute\b", 2.0),
        (r"\bextra charge\b", 2.0),
        (r"\bwrong (?:amount|fee|charge)\b", 2.0),
    ),
    INTENT_PRODUCT_RECOMMENDATION: (
        (r"\brecommend\w*\b", 3.0),
        (r"\bsuggest\b.{0,40}\b(?:product|account|card|plan)\b", 3.0),
        (r"\bsuitable\b.{0,40}\b(?:product|account|plan)\b", 2.0),
        (r"\bwhich (?:product|account|plan)\b", 2.0),
        (r"\bnext best action\b", 3.0),
    ),
    INTENT_CARD_FEE_ENQUIRY: (
        (r"\breplacement fee\b", 3.0),
        (r"\bwhat (?:is|are) the\b.{0,25}\bfee\b", 2.0),
        (r"\bhow much\b.{0,25}\b(?:fee|charge)\b", 2.0),
        (r"\bfee\b", 2.0),
        (r"\bcharge[sd]?\b", 1.0),
    ),
    INTENT_POLICY_ENQUIRY: (
        (r"\bpolic(?:y|ies)\b", 3.0),
        (r"\bterms and conditions\b", 3.0),
        (r"\b(?:procedure|guideline|regulation)s?\b", 2.0),
        (r"\bwhat (?:is|are) the rule\b", 2.0),
    ),
}

# --------------------------------------------------------------------------- #
# Risk signals
# --------------------------------------------------------------------------- #

HIGH_RISK_PATTERNS = (
    r"\bwithout my (?:permission|consent|authori[sz]ation|knowledge)\b",
    r"\bunauthori[sz]ed\b",
    r"\bunrecogni[sz]ed\b",
    r"\bnot recogni[sz]ed\b",
    r"\bnot me\b",
    r"\bnot mine\b",
    r"\b(?:did ?n[o']?t|never)\s+(?:make|authori[sz]e|approve)\b",
    r"\bsomeone (?:used|has used|took|has taken|paid|has paid|withdrew)\b",
    r"\bscam\b",
    r"\bfraud\w*\b",
    r"\bphishing\b",
    r"\bsuspicious\b",
    r"\bstolen\b",
    r"\b(?:compromised|hacked)\b",
    r"\b(?:otp|one[- ]time password)\b",
    # Social-engineering reports are high risk only when coupled to a money
    # movement. This avoids treating a generic use of "trick" as fraud.
    r"\b(?:trick(?:ed|ing)?|deceiv(?:e|ed|ing)|coerc(?:e|ed|ing)|pressur(?:e|ed|ing))\b.{0,80}\b(?:transfer(?:ring)?|send(?:ing)?(?:\s+money)?|pay(?:ing)?|mak(?:e|ing)\s+(?:a\s+)?payment)\b",
)

MEDIUM_RISK_PATTERNS = (
    r"\bcharged twice\b",
    r"\bdouble[- ]charged\b",
    r"\bovercharg\w+\b",
    r"\bextra charge\b",
    r"\bwrong (?:amount|fee|charge)\b",
    r"\bdispute\b",
    r"\brefund\b",
    r"\bdeclined\b",
    r"\bfailed\b",
    r"\bpending\b",
)

RISK_ORDER: dict[RiskLevel, int] = {
    RiskLevel.UNKNOWN: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
}

RISK_BASELINE_BY_INTENT: dict[str, RiskLevel] = {
    INTENT_FRAUD_SUSPICION: RiskLevel.HIGH,
    INTENT_UNAUTHORIZED_TRANSACTION: RiskLevel.HIGH,
    INTENT_FEE_COMPLAINT: RiskLevel.MEDIUM,
    INTENT_CARD_FEE_ENQUIRY: RiskLevel.LOW,
    INTENT_POLICY_ENQUIRY: RiskLevel.LOW,
    INTENT_PRODUCT_RECOMMENDATION: RiskLevel.LOW,
}

# --------------------------------------------------------------------------- #
# Entity vocabulary
# --------------------------------------------------------------------------- #

ENTITY_PAYMENT_METHOD = "payment_method"
ENTITY_AMOUNT = "amount"
ENTITY_CURRENCY = "currency"
ENTITY_DATE = "date"
ENTITY_RELATIVE_TIME = "relative_time"
ENTITY_ACCOUNT_TYPE = "account_type"
ENTITY_PRODUCT = "product"
ENTITY_CHANNEL = "channel"
ENTITY_TRANSACTION_REFERENCE = "transaction_reference"

ENTITY_TYPES = frozenset(
    {
        ENTITY_PAYMENT_METHOD,
        ENTITY_AMOUNT,
        ENTITY_CURRENCY,
        ENTITY_DATE,
        ENTITY_RELATIVE_TIME,
        ENTITY_ACCOUNT_TYPE,
        ENTITY_PRODUCT,
        ENTITY_CHANNEL,
        ENTITY_TRANSACTION_REFERENCE,
    }
)

ENTITY_GAZETTEER_CONFIDENCE = 0.90
ENTITY_PATTERN_CONFIDENCE = 0.85

# type -> ((phrase, canonical value), ...). Matched longest-phrase-first so that
# "credit card" is not also reported as "card".
ENTITY_GAZETTEER: dict[str, tuple[tuple[str, str], ...]] = {
    ENTITY_PAYMENT_METHOD: (
        ("apple pay", "apple pay"),
        ("google pay", "google pay"),
        ("contactless", "contactless"),
        ("credit card", "credit card"),
        ("debit card", "debit card"),
        ("virtual card", "virtual card"),
        ("atm card", "atm card"),
        ("direct debit", "direct debit"),
        ("bank transfer", "bank transfer"),
        ("paynow", "paynow"),
        ("paylah", "paylah"),
        ("giro", "giro"),
        ("cheque", "cheque"),
        ("transfer", "transfer"),
        ("cash", "cash"),
        ("atm", "atm"),
        ("card", "card"),
    ),
    ENTITY_ACCOUNT_TYPE: (
        ("savings account", "savings account"),
        ("current account", "current account"),
        ("deposit account", "deposit account"),
        ("joint account", "joint account"),
        ("fixed deposit", "fixed deposit"),
        ("time deposit", "time deposit"),
    ),
    ENTITY_PRODUCT: (
        ("savings product", "savings product"),
        ("savings plan", "savings plan"),
        ("credit card", "credit card"),
        ("debit card", "debit card"),
        ("virtual card", "virtual card"),
        ("physical card", "physical card"),
        ("disposable card", "disposable card"),
        ("personal loan", "personal loan"),
        ("home loan", "home loan"),
        ("investment plan", "investment plan"),
        ("unit trust", "unit trust"),
        ("mortgage", "mortgage"),
        ("insurance", "insurance"),
    ),
    ENTITY_CHANNEL: (
        ("mobile app", "mobile app"),
        ("online banking", "online banking"),
        ("internet banking", "internet banking"),
        ("mobile banking", "mobile banking"),
        ("phone banking", "phone banking"),
        ("website", "website"),
        ("branch", "branch"),
        ("app", "app"),
    ),
    ENTITY_RELATIVE_TIME: (
        ("last night", "last night"),
        ("this morning", "this morning"),
        ("last week", "last week"),
        ("this week", "this week"),
        ("last month", "last month"),
        ("last year", "last year"),
        ("just now", "just now"),
        ("yesterday", "yesterday"),
        ("tonight", "tonight"),
        ("today", "today"),
        ("recently", "recently"),
        ("earlier", "earlier"),
    ),
}

_MONTHS = (
    "january|february|march|april|may|june|"
    "july|august|september|october|november|december"
)
_MONTH = r"(?:" + _MONTHS + r")"

# type -> ((regex, value group), ...)
ENTITY_PATTERNS: dict[str, tuple[tuple[str, int], ...]] = {
    ENTITY_AMOUNT: (
        (r"(?:s\$|sgd|\$|usd)\s?\d[\d,]*(?:\.\d{1,2})?", 0),
        (r"\b\d[\d,]*(?:\.\d{1,2})?\s?(?:dollars?|cents?|sgd|usd)\b", 0),
    ),
    ENTITY_CURRENCY: (
        (r"\b(?:sgd|usd|eur|gbp|jpy|myr|hkd|aud|cny|rmb)\b", 0),
        (r"\bsingapore dollars?\b", 0),
        (r"\bus dollars?\b", 0),
    ),
    ENTITY_DATE: (
        (r"\b\d{4}-\d{2}-\d{2}\b", 0),
        (r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", 0),
        # A month name is a date only with a day, a year, or a date
        # preposition. This keeps "may" and "march" from matching as verbs.
        (
            r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?"
            + _MONTH
            + r"(?:\s+\d{4})?)\b",
            1,
        ),
        (r"\b(" + _MONTH + r"\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)\b", 1),
        (r"\b(" + _MONTH + r"\s+\d{4})\b", 1),
        (
            r"\b(?:in|on|during|since|until|before|after)\s+("
            + _MONTH
            + r")\b(?!\s+\d)",
            1,
        ),
        (r"\b(?:on\s+the|the)\s+(\d{1,2}(?:st|nd|rd|th))\b", 1),
    ),
    ENTITY_RELATIVE_TIME: (
        (r"\ba (?:few|couple of) (?:days?|weeks?|months?)\b", 0),
        (r"\b\d+\s+(?:days?|weeks?|months?|hours?|minutes?)\s+ago\b", 0),
    ),
    ENTITY_TRANSACTION_REFERENCE: (
        (
            r"\b(?:txn|ref|reference)\s*(?:id|no|number)?\s*[:#-]\s*([a-z0-9][a-z0-9-]{3,})\b",
            1,
        ),
        (
            r"\btransaction\s+(?:id|number|ref|reference)\s*[:#-]?\s*([a-z0-9][a-z0-9-]{3,})\b",
            1,
        ),
    ),
}
