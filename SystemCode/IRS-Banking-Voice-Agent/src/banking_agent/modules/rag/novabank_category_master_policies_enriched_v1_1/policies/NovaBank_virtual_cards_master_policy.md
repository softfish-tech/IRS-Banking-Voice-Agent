---
policy_id: DOC-CAT-VIRTUAL-001
business_category: virtual_cards
included_intents:
  - getting_virtual_card
  - disposable_card_limits
  - virtual_card_not_working
  - get_disposable_virtual_card
version: 1.1
status: Active
effective_date: 2026-10-11
source_type: Category Master Policy
bank_name: NovaBank
currency: SGD
jurisdiction_context: Singapore
language: en
synthetic: true
supersedes_version: 1.0
reference_review_date: 2026-10-11
reference_role: Operational topics only; all NovaBank terms are synthetic
reference_ids:
  - REF-18
  - REF-19
---

## NovaBank Reusable and Disposable Virtual Debit Cards Master Policy

### Purpose and Category Scope

Issuance and use of NovaBank reusable and one-use virtual Visa debit credentials within an existing verified personal account. Virtual-card counts are separate from physical-card entitlements.

### Common Fees, Limits and Service Conditions

One active reusable virtual card and one unused disposable virtual card are permitted per account. Issuance fee is SGD 0 and generation takes up to 60 seconds. Maximum disposable generations are 5 per Singapore calendar day; an unused disposable expires after 24 hours and supports one approved purchase of at most SGD-equivalent 500. Shared purchase limits are 5,000 per transaction and 10,000 daily; the stricter disposable limit prevails.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Counter and Available-Balance Interpretation

Purchase, ATM, card-top-up and outgoing bank-transfer limits are separate channel counters and apply at account level, not separately to each physical card, virtual card, wallet device or funding card. Available balance excludes authorisation holds and funds under an applicable review restriction. Principal counts toward transaction value limits; available balance must additionally cover disclosed fees. An approved attempt is assigned to its acceptance date for daily/monthly counting; a release can restore reserved capacity only in the still-current counting period. A refund or reversal of a completed transaction does not reset historical used limits or create new capacity in the earlier period. Where a product-specific limit is lower, the stricter limit applies.

### Credential Retirement and Merchant Compatibility

Reusable and disposable cards share account purchase limits but have different lifecycle entitlements. A disposable allows exactly one approved online purchase, not one merchant relationship. Its failed authorisation does not consume it, but an approved purchase does even before settlement. Original-transaction settlement/reversal/refund matching survives credential retirement. Zero-value tests, deposit security and multiple independent authorisations are not disposable-supported workflows. A replacement reusable credential does not automatically update subscriptions or wallet provisioning. Display credentials only in a freshly authenticated secure app screen.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### getting_virtual_card — Create a reusable virtual debit card for an eligible verified NovaBank customer

**Intent definition:** Create a reusable virtual debit card for an eligible verified NovaBank customer.

**Processing, conditions, fees and limits:**

- A verified adult personal account may hold 1 active reusable virtual Visa debit card. Create it in Cards > Add virtual card; issuance takes up to 60 seconds and costs SGD 0.
- The reusable virtual card supports online purchases and eligible wallet enrolment. It shares account purchase limits of SGD-equivalent 5,000 per transaction and 10,000 per calendar day with physical and disposable cards.
- Reveal card credentials only after secure app re-authentication. The virtual card has its own credentials; it is not a digital copy of a physical card and need not wait for physical delivery.
- If issuance remains incomplete after 5 minutes, submit the issuance reference; staff review within 2 business days. Freezing this virtual card takes effect within 60 seconds.

**Verification and required evidence:** Authenticate and re-authenticate in the app before revealing virtual credentials. Verify account ownership, verified adult status, card state and existing-card counters. Technical cases require a masked virtual-card identifier or generation reference and timestamp; purchases also require the merchant and decline reference. No fresh ID is needed for unchanged verified records.

**Fee and limit reference:** Issuance, freezing, unfreezing and technical review cost SGD 0. Maximum active reusable count is 1, unused disposable count is 1, and disposable generations are at most 5 daily. Disposable principal is at most 500 equivalent for 1 approved purchase; all spending shares the 10,000-equivalent daily account cap.

**Intent boundary and unsupported requests:** ATM cash withdrawal, physical chip-and-PIN use and a second active reusable virtual card are unsupported. A one-use online card belongs to get_disposable_virtual_card.

**Operational exceptions and status checks:**

- Generation requires an active verified personal account and secure authentication, costs SGD 0 and takes up to 60 seconds. Only one reusable virtual card may be active; replacing it retires old credentials first and does not create a second simultaneous entitlement.
- Reveal full credentials only in the secure card-details screen after fresh authentication, never in support chat. A replacement number is not automatically migrated to merchant subscriptions or all wallet tokens; the customer must update permitted recurring arrangements securely. Purchase caps remain account-shared SGD-equivalent 5,000 each/10,000 daily, and ATM/PIN-terminal use is unsupported.

### disposable_card_limits — State usage limits of NovaBank's single-use disposable virtual debit card

**Intent definition:** State usage limits of NovaBank's single-use disposable virtual debit card.

**Processing, conditions, fees and limits:**

- An account may have 1 unused disposable card at a time, generated at SGD 0 within 60 seconds, with at most 5 generations per Singapore calendar day.
- Each disposable card supports 1 approved online purchase with a maximum SGD-equivalent 500 value and expires 24 hours after generation if unused. Failed authorisations do not consume the one-use allowance.
- After one approved authorisation, credentials retire for new purchases. Related settlement, reversal and refund processing for that original transaction remain possible after retirement.
- Disposable spending also consumes the shared account purchase limits of SGD-equivalent 5,000 per transaction and 10,000 daily; the stricter disposable maximum of 500 still applies. A generation-limit query is reviewed within 2 business days.

**Verification and required evidence:** Authenticate and re-authenticate in the app before revealing virtual credentials. Verify account ownership, verified adult status, card state and existing-card counters. Technical cases require a masked virtual-card identifier or generation reference and timestamp; purchases also require the merchant and decline reference. No fresh ID is needed for unchanged verified records.

**Fee and limit reference:** Issuance, freezing, unfreezing and technical review cost SGD 0. Maximum active reusable count is 1, unused disposable count is 1, and disposable generations are at most 5 daily. Disposable principal is at most 500 equivalent for 1 approved purchase; all spending shares the 10,000-equivalent daily account cap.

**Intent boundary and unsupported requests:** Subscriptions, recurring payments, deposits, preauthorisations, wallet enrolment, ATM use and multiple independent purchases on one disposable card are unsupported. Card-funding limits under top_up_limits are unrelated.

**Operational exceptions and status checks:**

- Exactly one unused disposable credential may exist, with at most five successful generations per Singapore calendar day, one approved online purchase and SGD-equivalent 500 principal per purchase. Generations count even if later deleted or expired; a rejected generation request does not count as successful creation.
- Unused credentials expire after 24 hours. An approved purchase consumes the card even before settlement; a failed authorisation does not. A merchant workflow involving multiple independent authorisations, recurring billing, zero-value verification or deposit security is unsupported rather than exempt from the one-purchase rule. Public limit guidance is immediate and SGD 0.

### virtual_card_not_working — Troubleshoot a reusable virtual debit-card purchase or wallet-use failure

**Intent definition:** Troubleshoot a reusable virtual debit-card purchase or wallet-use failure.

**Processing, conditions, fees and limits:**

- Confirm the reusable virtual card is active, not frozen, correctly entered in the secure merchant form, and used for an accepted online purchase or eligible wallet payment.
- A reusable virtual card cannot be used at an ATM or as a physical chip-and-PIN card. It shares the SGD-equivalent 5,000 per-purchase and 10,000 daily account purchase limits.
- Authenticated unfreeze takes effect within 60 seconds at SGD 0. If credentials were exposed, escalate under compromised_card; replacement reusable virtual issuance costs SGD 0 and takes up to 60 seconds once approved.
- For persistent non-security failure, submit the masked virtual-card identifier, merchant, timestamp and decline reference; staff acknowledge within 1 business day and diagnose within 2 business days.

**Verification and required evidence:** Authenticate and re-authenticate in the app before revealing virtual credentials. Verify account ownership, verified adult status, card state and existing-card counters. Technical cases require a masked virtual-card identifier or generation reference and timestamp; purchases also require the merchant and decline reference. No fresh ID is needed for unchanged verified records.

**Fee and limit reference:** Issuance, freezing, unfreezing and technical review cost SGD 0. Maximum active reusable count is 1, unused disposable count is 1, and disposable generations are at most 5 daily. Disposable principal is at most 500 equivalent for 1 approved purchase; all spending shares the 10,000-equivalent daily account cap.

**Intent boundary and unsupported requests:** Physical-card troubleshooting, ATM use, forcing declined payments and reusing retired disposable credentials are unsupported within this policy. Disposable constraints use disposable_card_limits.

**Operational exceptions and status checks:**

- First identify reusable versus disposable, expiry/retirement, available balance, shared limits, merchant authentication and whether the merchant requires card-present PIN, repeat collection or a saved credential. Reusable-card troubleshooting stays here; disposable incompatibility retrieves disposable_card_limits. Virtual credentials cannot be used at ATMs; disposable cards additionally reject wallet enrolment and subscriptions/deposits.
- A retired disposable card may still receive a matched original-transaction refund; it cannot make a second purchase. Troubleshooting is SGD 0 with a 2-business-day technical review after masked references. A single recorded payment DECLINED routes to declined_card_payment; generating another card must not bypass a merchant incompatibility or security restriction.

### get_disposable_virtual_card — Generate one-use virtual Visa debit credentials for a single eligible online purchase

**Intent definition:** Generate one-use virtual Visa debit credentials for a single eligible online purchase.

**Processing, conditions, fees and limits:**

- A verified adult customer can generate 1 unused disposable card in Cards > Disposable card within 60 seconds at SGD 0. Maximum generation is 5 cards per Singapore calendar day.
- Each generated card expires after 24 hours if unused and permits 1 approved online purchase of at most SGD-equivalent 500. A failed authorisation does not consume that one-use allowance.
- After approved authorisation, credentials retire for new purchases, but settlement, reversal and refund matching remain supported for the original purchase. Shared account purchase limits still apply.
- A generation that has not completed after 5 minutes is reviewed by staff within 2 business days using the generation reference. Reveal disposable credentials only in the authenticated app.

**Verification and required evidence:** Authenticate and re-authenticate in the app before revealing virtual credentials. Verify account ownership, verified adult status, card state and existing-card counters. Technical cases require a masked virtual-card identifier or generation reference and timestamp; purchases also require the merchant and decline reference. No fresh ID is needed for unchanged verified records.

**Fee and limit reference:** Issuance, freezing, unfreezing and technical review cost SGD 0. Maximum active reusable count is 1, unused disposable count is 1, and disposable generations are at most 5 daily. Disposable principal is at most 500 equivalent for 1 approved purchase; all spending shares the 10,000-equivalent daily account cap.

**Intent boundary and unsupported requests:** Recurring payments, subscriptions, deposits, preauthorisations, wallet enrolment and ATM use are unsupported. getting_virtual_card creates a reusable card; disposable_card_limits explains one-use restrictions.

**Operational exceptions and status checks:**

- Before SGD 0 generation within 60 seconds, confirm the one-unused-card slot, the five-generation daily cap and eligibility of the intended one-time online purchase. If an unused card exists, reuse or securely retire it before generating another; retirement does not restore a used generation.
- State the SGD-equivalent 500 purchase cap and 24-hour unused expiry before showing details securely. Merchants that need test charges, independent split authorisations, deposits or repeat billing are incompatible. Retirement preserves the mapping for original settlement, network reversals and refunds, with the refunds policy's five-business-day clock from merchant issuance.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Create a reusable virtual debit card for an eligible verified NovaBank customer. | `getting_virtual_card` |
| State usage limits of NovaBank's single-use disposable virtual debit card. | `disposable_card_limits` |
| Troubleshoot a reusable virtual debit-card purchase or wallet-use failure. | `virtual_card_not_working` |
| Generate one-use virtual Visa debit credentials for a single eligible online purchase. | `get_disposable_virtual_card` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| getting_virtual_card / get_disposable_virtual_card | Reusable credentials support multiple purchases and eligible wallets; disposable credentials allow one approved online purchase. |
| get_disposable_virtual_card / disposable_card_limits | Generation is an action request; questions about one-use, 24-hour expiry, value and generation caps are limits. |
| virtual_card_not_working / disposable_card_limits | Reusable virtual technical failures use virtual_card_not_working; a retired/expired/over-limit disposable is a disposable restriction, not reusable-card malfunction. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not offer virtual ATM withdrawals, physical chip-and-PIN use, a second active reusable virtual card, multiple independent purchases on a disposable card, or disposable subscriptions, deposits, preauthorisations or wallet enrolment. Retired disposable credentials remain matchable for original-transaction settlement, reversals and refunds.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
