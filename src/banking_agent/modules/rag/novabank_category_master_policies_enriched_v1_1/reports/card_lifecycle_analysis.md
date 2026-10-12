## Part 1: Analysis and Expansion Report

### Scope and Reference Method

The submitted prompt retained input placeholders. This review therefore uses the previously created card_lifecycle version 1.0 as its draft and official public banking FAQs retrieved on 2026-10-11 as reference material. The output is a new standalone version 1.1, effective 2026-10-11. No original 13-policy package or Desktop file was edited.

Public sources identify operational topics; all NovaBank-specific numbers, exceptions, liability boundaries and wording remain synthetic design decisions. No reference-bank product name, phone number or contractual liability outcome is adopted as a NovaBank fact.

### Missing Rules Added

- Address/name validation before production, clear order-acceptance prerequisites, and separate handling of verification review and production cutoff. The operational topics are informed by [DBS card replacement guidance](https://www.dbs.com.sg/personal/support/card-issues-card-replacement.html). NovaBank's 20-character production name limit and unchanged delivery tiers are its own specifications.
- Distinction between temporary freeze and irreversible cancellation, treatment of a subsequently found cancelled card, and an assisted path when a card cannot be selected in the app. These topics are informed by [OCBC card services](https://www.ocbc.com/personal-banking/help-and-support/cards/card-services). NovaBank uses its existing protection times and does not copy another bank's wallet-lock exception.
- Replacement activation, merchant credential updates, retired-card disposal and a pre-travel renewal option. These topics are informed by [UOB debit-card FAQs](https://www.uob.com.sg/personal/customer-service/debit-card.page). The 90-day early-renewal eligibility window, review time and wallet-token treatment are NovaBank design choices, not extracted UOB limits.
- NovaBank-specific exception workflows: unsafe packaging, wrong-recipient cards, duplicate order requests, insufficient replacement-fee balance, address-amendment/dispatch races, renewal queues and explicit nonrenewal notices.
- Retained first-card/spare/renewal prices, standard Day 5 and express Day 2 deadlines, SGD 10 express surcharge and existing activation limits; clarified paid-express service recovery rather than importing a reference tariff.
- Explicit boundaries for loss abroad: urgent protection remains available 24/7, but NovaBank still does not ship abroad, offer overseas emergency cash or introduce joint/supplementary cards. Protection does not wait for a police report.
- Liability remains case-based under the existing security/dispute category. No automatic 48-hour forfeiture, conclusive OTP/PIN-authorisation inference or blanket reimbursement promise is introduced. Reference-bank reporting terms are not transplanted into NovaBank.

### Category Recommendation

Retain the current 13 categories. The enrichment deepens existing lifecycle intents rather than adding official BANKING77 labels. Credential migration relates to card_usage_and_access and card_payments; refunds stay in refunds; loss, compromise and liability assessment stay in security_and_unrecognised_transactions; ATM retention stays in cash_withdrawals; residence and identity changes stay in account_management/identity_verification.

Do not create fraud_investigation merely to duplicate the existing security category. If the project later actually supports credit lines, overdrafts or instalment finance, introduce a separate credit_and_overdraft category with its own product decisions, data and C/E contracts. Public FAQ navigation mentioning those products is not a reason to expand the current fictional service scope. Family/joint products would similarly require explicit scope approval and new account/card entitlement contracts; they remain unsupported here.

### Integration and Version Notes

The enriched policy is saved as NovaBank_card_lifecycle_enriched_v1.1.md. It preserves the same policy_id and seven intents, with a new version and effective date. Keep version 1.0 for historical events. Before substituting version 1.1 in an active index, update the document registry/manifest, file hash and version selection; do not load both as interchangeable current evidence. The existing package's original manifest continues to describe its original files accurately.

Candidate operational records such as order state, request ID and delivery timestamp belong to the future E-owned fulfilment layer. They are not implemented schema changes. Initial/spare/replacement activation uses a dispatch-based clock; renewal activation uses predecessor expiry. Cross-category baseline prices and limits are preserved. Novel exceptions should be reflected in C/E acceptance fixtures when the team adopts them.

### Reference Registry

| ID | Official source | Topics reviewed | Access date |
| --- | --- | --- | --- |
| REF-CARDLIFE-001 | [DBS: Replace Credit/Debit/ATM Card](https://www.dbs.com.sg/personal/support/card-issues-card-replacement.html) | Address confirmation, production name, replacement and PIN/renewal considerations | 2026-10-11 |
| REF-CARDLIFE-002 | [OCBC: Card Services](https://www.ocbc.com/personal-banking/help-and-support/cards/card-services) | Lock versus loss cancellation, replacement reasons, activation, unavailable app records and ownership boundaries | 2026-10-11 |
| REF-CARDLIFE-003 | [UOB: Debit Card Help and Support](https://www.uob.com.sg/personal/customer-service/debit-card.page) | Replacement activation, credential updates, expiry, early travel renewal, disposal and immediate security reporting | 2026-10-11 |

No scraped full text is redistributed. The references are research provenance, not an active NovaBank answer corpus. Structural checks verify intent coverage and Markdown/metadata format; they are not certification of legal compliance or proof of all semantic interactions.
