---
policy_id: DOC-CAT-CARDUSE-001
business_category: card_usage_and_access
included_intents:
  - card_linking
  - card_not_working
  - pin_blocked
  - contactless_not_working
  - card_acceptance
  - visa_or_mastercard
  - change_pin
  - apple_pay_or_google_pay
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
  - REF-01
  - REF-02
  - REF-03
  - REF-18
---

## NovaBank Physical Card Usage, PIN and Wallet Access Master Policy

### Purpose and Category Scope

Association, use and authentication of existing NovaBank Visa debit cards. Card issuance and activation are governed by card_lifecycle; reusable and disposable virtual issuance are governed by virtual_cards.

### Common Fees, Limits and Service Conditions

Purchases have a maximum of SGD-equivalent 5,000 per transaction and 10,000 per Singapore calendar day, shared by all cards and wallet tokens on the account. Physical contactless purchases are limited to SGD-equivalent 100 per transaction and 300 cumulative since the last successful chip-and-PIN purchase. Device-authenticated wallet tokens do not automatically inherit these physical-tap thresholds.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Physical-Card Delivery Reference

Physical-card standard delivery is SGD 0, dispatch by Day 2 and arrival by Day 5; express delivery adds SGD 10, dispatch by Day 1 and arrival by Day 2. Day 0 is the acceptance date for orders accepted by 14:00 on a business day; later/non-business-day orders use the next business day. Replacement requires secure verification and a verified Singapore address. Only 1 unfulfilled dispatch order is allowed; the retired predecessor does not count against the 2-card limit.

### Counter and Available-Balance Interpretation

Purchase, ATM, card-top-up and outgoing bank-transfer limits are separate channel counters and apply at account level, not separately to each physical card, virtual card, wallet device or funding card. Available balance excludes authorisation holds and funds under an applicable review restriction. Principal counts toward transaction value limits; available balance must additionally cover disclosed fees. An approved attempt is assigned to its acceptance date for daily/monthly counting; a release can restore reserved capacity only in the still-current counting period. A refund or reversal of a completed transaction does not reset historical used limits or create new capacity in the earlier period. Where a product-specific limit is lower, the stricter limit applies.

### Card Credentials and Token States

An app account, physical-card record and device wallet token are different objects. A linked card can remain inactive; a usable chip card can have disabled taps; a wallet token can be revoked while the physical card remains valid. Staff must identify the affected object before changing it. A temporary customer freeze is reversible only if no security restriction applies; permanent retirement is not. Card retirement suspends associated tokens within 5 minutes, but cannot cancel previous authorisations or merchant contracts. Unknown transaction outcomes require status lookup rather than a second attempt.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### card_linking — Associate an existing NovaBank physical debit card with its own verified NovaBank app account

**Intent definition:** Associate an existing NovaBank physical debit card with its own verified NovaBank app account.

**Processing, conditions, fees and limits:**

- A physical card must belong to the same verified account holder. Enter its last four digits and expiry month/year in Cards > Link existing card, then approve the request in the authenticated app; linking completes within 60 seconds and costs SGD 0.
- An account supports at most 2 active physical cards: one primary card and one spare. Linking is not activation, and an unactivated linked card still cannot make payments.
- After 3 unsuccessful ownership checks within 24 hours, linking is locked for 24 hours. Staff review a matching-ownership issue within 2 business days after receiving an order reference and masked screenshot.
- Customer-support chat must not collect full card numbers, PINs, CVVs or authentication codes. Full credentials, where needed for an unrelated card top-up, belong only in the secure payment form.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Linking another person's card, linking an external bank card as a NovaBank-issued card, and merging different customers' accounts are rejected. Wallet-token enrolment belongs to apple_pay_or_google_pay.

**Operational exceptions and status checks:**

- Link only the customer-owned card selected in the authenticated account. If the last four digits match more than one historical card, also match expiry and issuance reference; do not reveal another account holder or merge card records. A cancelled, retired or expired card remains historical and cannot become usable through linking.
- An accepted request has one linking reference. If the card is still absent after 60 seconds, refresh once and inspect that reference before resubmitting; a matching-record issue is reviewed within 2 business days at SGD 0. Linking does not reset the activation deadline or create an additional physical-card entitlement.

### card_not_working — Troubleshoot a general physical debit-card failure when no single transaction outcome is identified

**Intent definition:** Troubleshoot a general physical debit-card failure when no single transaction outcome is identified.

**Processing, conditions, fees and limits:**

- Check card activation, expiry, app freeze status, available balance and enabled payment controls. A newly delivered card requires activation and one successful chip-and-PIN purchase before contactless use.
- An authenticated unfreeze completes within 60 seconds at SGD 0, except where a security team has blocked the card. A damaged card replacement costs SGD 15 and follows the standard delivery deadline of Day 5.
- Physical-card purchase limits are SGD-equivalent 5,000 per transaction and 10,000 per Singapore calendar day, shared with virtual cards and wallet-token purchases on the account.
- If general failures persist after these checks, staff acknowledge the diagnostic case within 1 business day and issue a technical decision within 2 business days. Suspected compromise bypasses routine troubleshooting and is escalated immediately.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** A security block cannot be bypassed by support chat. A single recorded decline uses declined_card_payment; tap-only failure uses contactless_not_working; virtual-card failure uses virtual_card_not_working.

**Operational exceptions and status checks:**

- Record whether chip-and-PIN, physical tap, online purchase or wallet use failed. One recorded payment refusal routes to declined_card_payment; two-terminal tap-only failure routes to contactless_not_working. Do not diagnose damage from one merchant refusal.
- Temporary customer freeze may be removed within 60 seconds after secure verification at SGD 0; permanent retirement and security-team restrictions require their separate route. A replacement retires the damaged predecessor before order acceptance and costs SGD 15 plus selected delivery: standard SGD 0, arrival Day 5; express SGD 10, arrival Day 2.

### pin_blocked — Unblock a physical-card PIN after consecutive incorrect card-PIN attempts

**Intent definition:** Unblock a physical-card PIN after consecutive incorrect card-PIN attempts.

**Processing, conditions, fees and limits:**

- The card PIN is blocked after 3 consecutive incorrect attempts. This card-PIN block is distinct from the app's 6-digit passcode lock.
- After secure app authentication, select Cards > PIN > Unblock. An eligible unblock costs SGD 0 and completes within 5 minutes; the next transaction must be chip-and-PIN.
- At most 1 self-service PIN unblock is permitted in 24 hours. If the card remains blocked after 5 minutes, urgent security staff review ownership; a technical decision is issued within 1 business day.
- A fraud-team block or cancelled card is not eligible for self-service unblocking. Staff never request the actual 4-digit PIN in chat, telephone notes or uploaded screenshots.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Overriding a security block, recovering a PIN by disclosing it to an agent, and unblocking someone else's card are prohibited. change_pin changes a known PIN; passcode_forgotten concerns app access.

**Operational exceptions and status checks:**

- Stop further PIN attempts after the third consecutive wrong entry. Wallet biometric success does not prove the physical-card PIN is unblocked. The SGD 0 self-service unblock takes up to 5 minutes and is limited to one in a rolling 24 hours, not one per midnight reset.
- After an eligible unblock, make the next purchase by chip-and-PIN. If the customer has forgotten the PIN, use the secure PIN-change flow after removing an eligible PIN block; chat cannot disclose the previous PIN. Do not repeat an unblock to bypass a security restriction.

### contactless_not_working — Troubleshoot tap-to-pay failure on an otherwise usable physical debit card

**Intent definition:** Troubleshoot tap-to-pay failure on an otherwise usable physical debit card.

**Processing, conditions, fees and limits:**

- Activate a new physical card and complete one chip-and-PIN purchase before its first contactless transaction. Ensure contactless is enabled in Cards > Controls.
- NovaBank's physical-card contactless threshold is SGD-equivalent 100 per transaction and SGD-equivalent 300 cumulative since the last successful chip-and-PIN transaction; exceeding either requires chip-and-PIN.
- Changing the contactless setting takes effect within 60 seconds and costs SGD 0. A merchant or terminal may require PIN sooner; NovaBank cannot force that terminal to accept a tap.
- If taps fail at 2 different compatible terminals while chip-and-PIN succeeds, submit terminal dates and masked references. Staff review within 2 business days; a confirmed damaged-card replacement costs SGD 15 and arrives by Day 5 under the physical-card Day 0 acceptance/cutoff convention.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Contactless payment above the threshold without required authentication is unsupported. General failures use card_not_working; wallet-token enrolment and wallet-specific failure use apple_pay_or_google_pay.

**Operational exceptions and status checks:**

- A purchase of exactly SGD-equivalent 100 is within the single-tap ceiling only if it does not take cumulative tap principal above 300. A successful chip-and-PIN purchase resets that cumulative counter; app toggles, wallet purchases and calendar midnight do not.
- A terminal may demand chip-and-PIN below NovaBank ceilings. Use one card at a time and remove competing cards from the tap area; do not promise a terminal override. The contactless control changes within 60 seconds at SGD 0. After failures at two compatible terminals with successful chip use, submit dates and masked references for the 2-business-day review.

### card_acceptance — Explain where an active NovaBank-issued debit card may be used

**Intent definition:** Explain where an active NovaBank-issued debit card may be used.

**Processing, conditions, fees and limits:**

- NovaBank issues Visa debit cards. Active physical cards may be used at Visa debit merchants; reusable virtual cards are for online purchases or eligible wallet use. Acceptance depends on merchant/terminal support and risk controls.
- Purchase limits are SGD-equivalent 5,000 per transaction and 10,000 per account per calendar day. A purchase requires sufficient available balance and successful authentication where prompted.
- Transactions are permitted only in SGD, USD, EUR, GBP or AUD. NovaBank rejects other transaction currencies before approval; merchant-selected conversion to a supported currency is separately priced by the merchant.
- NovaBank charges SGD 0 for ordinary purchases. If it converts from SGD, a 0.50% fee with SGD 0.50 minimum applies. A merchant-acceptance query is reviewed within 2 business days with merchant name and masked transaction reference.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Acceptance at every merchant, prohibited purchases, offline transactions without authorisation and purchases in unsupported currencies are not guaranteed or supported. An actual decline uses declined_card_payment; network selection uses visa_or_mastercard.

**Operational exceptions and status checks:**

- Visa acceptance signage does not guarantee a particular debit card, online transaction or deposit is accepted. A merchant may require the physical cardholder, local billing details or a deposit; disposable cards reject deposit and recurring workflows even at otherwise compatible merchants.
- For a public acceptance question, collect no customer documents and answer immediately at SGD 0. For a specific refusal, securely check merchant, country, charged currency and reference, then use declined_card_payment. Supported foreign-currency spending does not create a foreign local account or international-transfer service.

### visa_or_mastercard — Explain the network of NovaBank-issued cards and distinguish eligible external funding networks

**Intent definition:** Explain the network of NovaBank-issued cards and distinguish eligible external funding networks.

**Processing, conditions, fees and limits:**

- All NovaBank-issued physical, reusable virtual and disposable virtual debit cards use Visa. Customers cannot select Mastercard for a NovaBank-issued card.
- Visa network selection costs SGD 0 because it is fixed. Physical first-card issuance costs SGD 0, standard shipping takes 5 business days, and reusable virtual issuance costs SGD 0 and takes up to 60 seconds.
- For external SGD top-ups only, NovaBank accepts eligible Singapore-issued Visa or Mastercard debit cards owned by the verified customer. External Mastercard eligibility does not mean NovaBank issues Mastercard cards.
- Check merchant support for Visa debit; ordinary account purchase limits are SGD-equivalent 5,000 per transaction and 10,000 daily. Staff clarify a network query within 2 business days.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Choosing or switching a NovaBank card to Mastercard, American Express or another network is unsupported. card_acceptance covers merchant use; supported_cards_and_currencies covers external funding-card eligibility.

**Operational exceptions and status checks:**

- NovaBank issues Visa debit credentials only: physical, reusable virtual and disposable. Network-selection enquiries cost SGD 0 and can be answered immediately without authentication. An external Mastercard may qualify for card funding but is not a NovaBank-issued Mastercard.
- A merchant that accepts only Mastercard is not made eligible by ordering another NovaBank card. Do not submit a replacement, alter account settings or promise a future network migration in response to a network preference.

### change_pin — Change the 4-digit PIN of an eligible physical NovaBank debit card

**Intent definition:** Change the 4-digit PIN of an eligible physical NovaBank debit card.

**Processing, conditions, fees and limits:**

- Authenticate in the app and use Cards > PIN > Change PIN. The new PIN must contain exactly 4 digits; the change costs SGD 0 and completes within 5 minutes.
- At most 2 PIN changes are allowed in a rolling 24-hour period. Follow the app's instruction to complete the next transaction as chip-and-PIN so the physical-card state is refreshed.
- A blocked PIN must first pass the pin_blocked process, which permits 1 self-service unblock per 24 hours. A cancelled or fraud-blocked card is not eligible for a PIN change.
- Support never asks for the current or new PIN. If a successful change is not usable after 5 minutes, submit the masked card identifier and change reference; staff review within 1 business day.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Changing the app's 6-digit passcode, selecting a PIN on someone else's card and overriding security restrictions are unsupported. passcode_forgotten concerns login recovery rather than card PIN management.

**Operational exceptions and status checks:**

- Enter and confirm the four-digit new PIN only in the secure PIN screen. Reject four repeated digits or ascending/descending sequences; never ask the customer to state the proposed PIN in chat. No unchanged customer identity document is required.
- An approved change costs SGD 0, applies within 5 minutes and allows two changes per rolling 24 hours. Test through a chip-and-PIN purchase; an app-passcode change neither changes nor unblocks this PIN. A cancelled card is ineligible, and a PIN block must follow pin_blocked first.

### apple_pay_or_google_pay — Enrol a supported NovaBank debit card in Apple Pay or Google Pay and troubleshoot wallet-specific use

**Intent definition:** Enrol a supported NovaBank debit card in Apple Pay or Google Pay and troubleshoot wallet-specific use.

**Processing, conditions, fees and limits:**

- Active physical and reusable virtual NovaBank Visa debit cards may be enrolled through the authenticated app and the device's supported wallet. Disposable cards cannot be enrolled.
- Enrolment requires a wallet-compatible device, device screen lock and secure ownership confirmation. Successful token provisioning takes up to 5 minutes and costs SGD 0; maximum is 3 active wallet-device tokens per account.
- Wallet purchases share account limits of SGD-equivalent 5,000 per transaction and 10,000 daily. Device-authenticated wallet purchases follow merchant authentication rules; the physical-card SGD 100/300 contactless thresholds do not automatically apply to authenticated wallet tokens.
- If enrolment remains incomplete after 5 minutes, staff diagnose within 2 business days. A lost-device report requires security escalation; verified device-session/token suspension completes within 5 minutes.

**Verification and required evidence:** For a card-specific action, authenticate securely and identify the card by its last 4 digits. For troubleshooting, provide a masked reference, timestamp, merchant or terminal and error message; for linking, provide the card expiry and order reference if needed. Do not disclose the PIN. An unchanged verified identity needs no fresh document.

**Fee and limit reference:** Routine linking, PIN administration, wallet enrolment, diagnosis and acceptance enquiries cost SGD 0. Applicable numeric limits are specified above and in the intent rules. A damaged physical replacement is SGD 15 plus the selected delivery fee; routine support cannot waive transaction or authentication limits.

**Intent boundary and unsupported requests:** Disposable-card enrolment, ATM withdrawals via wallet, unsupported devices and guaranteed acceptance at every terminal are unsupported. card_linking concerns app association; contactless_not_working concerns physical-card taps.

**Operational exceptions and status checks:**

- Each enrolled device token counts towards the account maximum of three active wallet tokens. A replacement handset requires fresh secure provisioning; device ownership does not establish account ownership. Provisioning is SGD 0 within 5 minutes, and all wallet purchases share the account purchase counters.
- Reusable virtual credentials may be enrolled; disposable credentials and wallet ATM cash withdrawal are unsupported. Card retirement suspends associated tokens within 5 minutes. Unfreezing a card does not recreate a revoked token; re-provision securely. Merchant subscriptions and existing authorisations are not cancelled merely by removing a wallet token.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Associate an existing NovaBank physical debit card with its own verified NovaBank app account. | `card_linking` |
| Troubleshoot a general physical debit-card failure when no single transaction outcome is identified. | `card_not_working` |
| Unblock a physical-card PIN after consecutive incorrect card-PIN attempts. | `pin_blocked` |
| Troubleshoot tap-to-pay failure on an otherwise usable physical debit card. | `contactless_not_working` |
| Explain where an active NovaBank-issued debit card may be used. | `card_acceptance` |
| Explain the network of NovaBank-issued cards and distinguish eligible external funding networks. | `visa_or_mastercard` |
| Change the 4-digit PIN of an eligible physical NovaBank debit card. | `change_pin` |
| Enrol a supported NovaBank debit card in Apple Pay or Google Pay and troubleshoot wallet-specific use. | `apple_pay_or_google_pay` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| card_linking / apple_pay_or_google_pay | Linking associates an owned physical card with the NovaBank app; wallet enrolment provisions a device payment token. |
| card_not_working / contactless_not_working | General chip/card failures use card_not_working; physical tap-only failure while chip-and-PIN works uses contactless_not_working. |
| pin_blocked / change_pin | Three wrong physical PIN attempts require unblocking first; choosing a new PIN is a separate change action. |
| card_acceptance / visa_or_mastercard | Where a card may be used is acceptance; which network NovaBank issues is network selection. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not offer Mastercard issuance, ATM withdrawals through wallet tokens, third-party card linking, use of unsupported currencies, bypass of a fraud block, or contactless purchases above the physical thresholds without required authentication. Physical issuance, replacement orders, merchant refunds and ATM reconciliation are separate workflows.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
