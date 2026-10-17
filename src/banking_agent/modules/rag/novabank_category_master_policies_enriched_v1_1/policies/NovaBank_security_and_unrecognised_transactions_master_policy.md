---
policy_id: DOC-CAT-SECURITY-001
business_category: security_and_unrecognised_transactions
included_intents:
  - lost_or_stolen_card
  - card_payment_not_recognised
  - compromised_card
  - direct_debit_payment_not_recognised
  - lost_or_stolen_phone
  - cash_withdrawal_not_recognised
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
  - REF-12
  - REF-13
  - REF-03
  - REF-08
  - REF-06
---

## NovaBank Card, Device and Unrecognised Debit Security Master Policy

### Purpose and Category Scope

Loss, theft, credential exposure and alleged unauthorised transactions. Protective escalation takes priority over ordinary intent uncertainty or troubleshooting. Direct-debit mandates are not a NovaBank product, but alleged unauthorised deductions must still be assessed.

### Common Fees, Limits and Service Conditions

Security intake and protective freeze cost SGD 0. Authenticated card freeze takes up to 60 seconds; verified device-session and wallet-token suspension takes up to 5 minutes. Urgent security staff are available 24/7. Physical loss/security replacement costs SGD 15 plus SGD 0 standard delivery by Day 5 or SGD 10 express delivery by Day 2. No automatic provisional reimbursement is promised.

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

### Protection, Investigation and Liability Decisions

Urgent intake can begin without full receipts or a police report; account-state changes require verified authority. After secure verification, protective freeze targets 60 seconds and relevant session/token revocation targets 5 minutes. Protection cannot erase past authorisations. Whether a payment was unknown, knowingly approved under deception or made after credential exposure must be recorded; none alone determines reimbursement. There is no automatic 48-hour forfeiture rule or unconditional reimbursement promise. Where BANKING77 lacks an exact unauthorised-transfer label, preserve urgent staff escalation instead of forcing an incorrect low-risk label.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### lost_or_stolen_card — Immediately protect a physical debit card reported lost or stolen

**Intent definition:** Immediately protect a physical debit card reported lost or stolen.

**Processing, conditions, fees and limits:**

- Freeze the card in Cards > Freeze as soon as loss is suspected; an authenticated freeze takes effect within 60 seconds at SGD 0. Urgent security staff are available 24 hours a day, 7 days a week.
- Verify through the secure account channel. If the customer cannot access the app, urgent staff begin assisted verification before changing account data; chatbot messages never collect PINs, CVVs or one-time codes.
- Once permanently cancelled, the lost card cannot be reactivated. Customer-loss replacement costs SGD 15 and delivery takes 5 business days from the processing acceptance date.
- Record the last four digits, loss time and any unrecognised transaction references. Creating or escalating a case leaves the complaint OPEN until an authorised resolution event; marketing recommendations remain blocked.

**Verification and required evidence:** Escalate immediately. Before protective account changes, authenticate through the secure app or assisted recovery using a valid government-issued photo ID, live identity check and matching account records. Record the affected masked card/device and event or transaction reference. No fresh ID is needed when secure app verification succeeds; never collect secret credentials in chat.

**Fee and limit reference:** Report, freeze, device suspension and investigation fees are SGD 0. Open one coordinated security case per incident, linking affected transaction references rather than duplicate claims. Physical security replacement is SGD 15 plus delivery; reusable virtual replacement is SGD 0. No automatic reimbursement entitlement or daily-limit increase arises from an incident.

**Intent boundary and unsupported requests:** Promises that freezing reverses already authorised payments, guarantees recovery of stolen funds, or proves the complaint resolved are prohibited. Known unauthorised card payments also require card_payment_not_recognised review.

**Operational exceptions and status checks:**

- Report immediately from any location. Securely freeze within 60 seconds at SGD 0; if loss/theft is confirmed, permanent retirement cannot be undone even if the card is later found. Linked wallet tokens are suspended within 5 minutes, but previous approved purchases may still settle.
- No police report or complete transaction receipt is a prerequisite for urgent intake. Loss replacement is SGD 15 plus standard SGD 0 shipping by Day 5 or express SGD 10 by Day 2, only to a verified Singapore address. A disputed debit gets a linked investigation, and neither replacement nor late reporting alone determines reimbursement.

### card_payment_not_recognised — Protect and investigate an unrecognised debit-card purchase

**Intent definition:** Protect and investigate an unrecognised debit-card purchase.

**Processing, conditions, fees and limits:**

- Treat an unrecognised card purchase as a high-risk report and route immediately to urgent security staff available 24/7. Authenticate through the secure channel and freeze the affected card within 60 seconds after an authenticated instruction.
- Record the transaction reference, merchant descriptor, amount, settlement status and time the customer noticed it. A merchant descriptor check must not delay protection when the customer alleges unauthorised use.
- Report promptly; the standard card-dispute intake window is 60 calendar days from settlement. Late reports are still escalated for assessment, without promising acceptance or reimbursement.
- Staff acknowledge the security case within 1 business day and target a dispute decision within 30 calendar days after complete evidence. Approved refunds are credited within 2 business days after approval. No provisional refund or liability outcome is guaranteed.
- Freeze and investigation are SGD 0. Purchase caps remain 5,000 equivalent each and 10,000 daily, but being within a limit does not prove authorisation. One case per incident may link multiple disputed purchases. Do not promise compensation merely because a transaction fits these caps.

**Verification and required evidence:** Escalate immediately. Before protective account changes, authenticate through the secure app or assisted recovery using a valid government-issued photo ID, live identity check and matching account records. Record the affected masked card/device and event or transaction reference. No fresh ID is needed when secure app verification succeeds; never collect secret credentials in chat.

**Fee and limit reference:** Report, freeze, device suspension and investigation fees are SGD 0. Open one coordinated security case per incident, linking affected transaction references rather than duplicate claims. Physical security replacement is SGD 15 plus delivery; reusable virtual replacement is SGD 0. No automatic reimbursement entitlement or daily-limit increase arises from an incident.

**Intent boundary and unsupported requests:** A chatbot cannot declare the transaction authorised, guarantee reimbursement, close the complaint on intake, or recommend products during the unresolved case. Known duplicate purchases use transaction_charged_twice; unknown ATM debits use cash_withdrawal_not_recognised.

**Operational exceptions and status checks:**

- Record recognition status without forcing the customer to contact a suspected merchant first. A different trading name may explain a descriptor, but a customer denying approval routes immediately to urgent security even when the line is pending. Secure card freeze is SGD 0 within 60 seconds.
- Collect masked reference, amount/currency, date, card last four digits and known device access for the formal case. Standard intake is within 60 calendar days of settlement; late cases require staff assessment rather than automatic rejection. Acknowledge within 1 business day, target decision within 30 calendar days after complete evidence and credit approved reimbursement within 2 business days. OTP/PIN use is not conclusive proof of consent.

### compromised_card — Respond to suspected exposure of debit-card credentials whether or not a fraudulent charge exists

**Intent definition:** Respond to suspected exposure of debit-card credentials whether or not a fraudulent charge exists.

**Processing, conditions, fees and limits:**

- Suspected credential exposure, phishing or a shared CVV is a high-risk report. Freeze the affected card immediately using secure authentication; the app action takes effect within 60 seconds at SGD 0, with urgent staff available 24/7.
- Record last four digits, exposure time, how exposure occurred and any transaction references, without collecting the exposed full credentials. Do not ask the customer to send a PIN, CVV or one-time code.
- After verified cancellation, a physical security replacement costs SGD 15 and takes 5 business days; replacement of a reusable virtual card costs SGD 0 and takes up to 60 seconds once staff permit reissuance.
- If unauthorised purchases are identified, open the separate card dispute: report promptly, standard intake within 60 calendar days of settlement, acknowledgement within 1 business day and target decision within 30 calendar days after complete evidence.

**Verification and required evidence:** Escalate immediately. Before protective account changes, authenticate through the secure app or assisted recovery using a valid government-issued photo ID, live identity check and matching account records. Record the affected masked card/device and event or transaction reference. No fresh ID is needed when secure app verification succeeds; never collect secret credentials in chat.

**Fee and limit reference:** Report, freeze, device suspension and investigation fees are SGD 0. Open one coordinated security case per incident, linking affected transaction references rather than duplicate claims. Physical security replacement is SGD 15 plus delivery; reusable virtual replacement is SGD 0. No automatic reimbursement entitlement or daily-limit increase arises from an incident.

**Intent boundary and unsupported requests:** Reactivating a permanently cancelled compromised card, guaranteeing prevention of all previously authorised settlements, and claiming compromise is resolved merely by opening a case are prohibited.

**Operational exceptions and status checks:**

- Credentials exposed on a fraudulent website or to a caller count as compromise even with zero observed loss. Stop entering credentials, securely freeze within 60 seconds at SGD 0 and escalate urgently. Staff determine permanent retirement and replacement; a freeze cannot erase previous authorisations.
- If the customer deliberately approved a scam payment, record that fact without calling it automatically unauthorised or denying investigation. Protection remains immediate, and staff apply the transaction's correct dispute route. Security replacement is SGD 15 plus standard SGD 0/Day 5 or express SGD 10/Day 2 delivery; reimbursement is not guaranteed.

### direct_debit_payment_not_recognised — Respond to an alleged unrecognised direct debit when NovaBank does not offer direct-debit mandates

**Intent definition:** Respond to an alleged unrecognised direct debit when NovaBank does not offer direct-debit mandates.

**Processing, conditions, fees and limits:**

- NovaBank supports no direct-debit mandate or collection service. The number of allowed direct-debit mandates is 0; no direct-debit fee, collection limit or mandate-creation window applies.
- An entry described by the customer as a direct debit must be identified from its transaction reference and payment type. Card subscriptions are card transactions, and scheduled payments shown by another bank are not NovaBank direct debits.
- Any alleged unauthorised deduction is immediately escalated to urgent security staff available 24/7. Securely verify the account and record the reference, descriptor, amount and date without requesting PINs or codes.
- Staff acknowledge within 1 business day and classify the ledger entry within 2 business days. If it is an unrecognised card payment, apply the 60-calendar-day standard card intake and 30-calendar-day dispute-decision target after complete evidence.
- Allowed mandates: 0; supported direct-debit principal limit: SGD 0. Unsupported mandate submission is rejected immediately, and no mandate fee is collected (SGD 0). A security allegation is classified within 2 business days, not processed as an invented direct-debit refund.

**Verification and required evidence:** Escalate immediately. Before protective account changes, authenticate through the secure app or assisted recovery using a valid government-issued photo ID, live identity check and matching account records. Record the affected masked card/device and event or transaction reference. No fresh ID is needed when secure app verification succeeds; never collect secret credentials in chat.

**Fee and limit reference:** Report, freeze, device suspension and investigation fees are SGD 0. Open one coordinated security case per incident, linking affected transaction references rather than duplicate claims. Physical security replacement is SGD 15 plus delivery; reusable virtual replacement is SGD 0. No automatic reimbursement entitlement or daily-limit increase arises from an incident.

**Intent boundary and unsupported requests:** Creating, cancelling or refunding a NovaBank direct-debit mandate is unsupported. The unsupported payment type must not cause an unauthorised-debit allegation to be dismissed or marked resolved.

**Operational exceptions and status checks:**

- NovaBank supports zero direct-debit mandates. A reported direct debit may be a recurring card purchase, a transfer, a misleading descriptor or a fraudulent demand. Classify actual ledger references within 2 business days at SGD 0, while treating suspected account compromise immediately.
- Do not create, cancel or claim a refund under a non-existent mandate scheme. An actual unrecognised card debit follows the 60-calendar-day standard intake and 30-calendar-day investigation; an actual transfer needs urgent staff-led assessment because BANKING77 has no exact unauthorised-transfer label. Unsupported terminology is not grounds to dismiss a debit complaint.

### lost_or_stolen_phone — Secure NovaBank access and wallet tokens after a phone is lost or stolen

**Intent definition:** Secure NovaBank access and wallet tokens after a phone is lost or stolen.

**Processing, conditions, fees and limits:**

- Contact urgent security staff immediately through the independently verified support channel; the security service is available 24/7. Assisted secure verification is required before changing account access.
- After verified instruction, revoke the device's app session and suspend associated wallet tokens within 5 minutes at SGD 0. Freeze any also-compromised debit card within 60 seconds of its authenticated freeze instruction.
- Phone loss alone does not automatically cancel a physical card, reverse existing payments or close a complaint. Review recent transactions and separately escalate unrecognised debits.
- A new registered-phone request requires secure identity evidence and review within 2 business days after complete submission. After approval, adding beneficiaries and card top-ups are restricted for 24 hours.
- Assisted recovery requires valid government-issued photo ID, live identity check and matching account records. A replacement registered phone must be controlled by the verified customer. There are at most 3 active wallet-device tokens per account; suspension can cover all tokens on the lost device and does not require the customer to know token secrets.

**Verification and required evidence:** Escalate immediately. Before protective account changes, authenticate through the secure app or assisted recovery using a valid government-issued photo ID, live identity check and matching account records. Record the affected masked card/device and event or transaction reference. No fresh ID is needed when secure app verification succeeds; never collect secret credentials in chat.

**Fee and limit reference:** Report, freeze, device suspension and investigation fees are SGD 0. Open one coordinated security case per incident, linking affected transaction references rather than duplicate claims. Physical security replacement is SGD 15 plus delivery; reusable virtual replacement is SGD 0. No automatic reimbursement entitlement or daily-limit increase arises from an incident.

**Intent boundary and unsupported requests:** Support cannot locate, remotely wipe or replace a handset, and cannot bypass authentication because a phone is missing. passcode_forgotten handles a forgotten passcode without theft; apple_pay_or_google_pay handles routine wallet enrolment.

**Operational exceptions and status checks:**

- Use a trusted device or assisted recovery route; do not send recovery codes to a reported-compromised number. Urgent intake is available 24/7 at SGD 0. After verified ownership, revoke lost-device sessions and associated wallet tokens within 5 minutes and apply necessary card freeze within 60 seconds.
- Self-service identity-backed passcode recovery normally takes up to 10 minutes; unavailable credentials or failed identity checks require manual review within 2 business days of complete evidence. Holding a physical card is not sufficient recovery proof. A subsequent approved phone-number change imposes the existing 24-hour restriction on beneficiary addition and card top-ups.

### cash_withdrawal_not_recognised — Secure and investigate an alleged unauthorised ATM withdrawal

**Intent definition:** Secure and investigate an alleged unauthorised ATM withdrawal.

**Processing, conditions, fees and limits:**

- Immediately escalate an unrecognised ATM withdrawal to urgent security staff available 24/7. Freeze the affected physical card within 60 seconds of authenticated instruction, at SGD 0.
- Record the withdrawal reference, ATM location, amount, time and last four card digits. Never collect the customer's PIN or claim that successful PIN use proves the customer authorised the withdrawal.
- Report promptly; the standard ATM-discrepancy intake window is 30 calendar days from withdrawal. Late unauthorised reports are still escalated for staff assessment, without guaranteeing acceptance or reimbursement.
- Staff acknowledge within 1 business day, target an ATM reconciliation decision within 10 business days after complete evidence and credit an approved correction within 2 business days. The complaint remains unresolved until an authorised decision and resolution event.
- The ordinary ATM caps remain 500 equivalent per transaction and 1,000 daily. A completed ATM bank fee is SGD 2, but whether any disputed principal or fee is refundable is determined by investigation; neither PIN use nor a within-limit amount establishes customer authorisation.

**Verification and required evidence:** Escalate immediately. Before protective account changes, authenticate through the secure app or assisted recovery using a valid government-issued photo ID, live identity check and matching account records. Record the affected masked card/device and event or transaction reference. No fresh ID is needed when secure app verification succeeds; never collect secret credentials in chat.

**Fee and limit reference:** Report, freeze, device suspension and investigation fees are SGD 0. Open one coordinated security case per incident, linking affected transaction references rather than duplicate claims. Physical security replacement is SGD 15 plus delivery; reusable virtual replacement is SGD 0. No automatic reimbursement entitlement or daily-limit increase arises from an incident.

**Intent boundary and unsupported requests:** Guaranteed fraud refunds, automatic complaint closure and product recommendations during unresolved security complaints are prohibited. A recognised cash shortage uses wrong_amount_of_cash_received.

**Operational exceptions and status checks:**

- Unrecognised ATM debits require immediate security escalation and secure physical-card freeze within 60 seconds at SGD 0, even if the customer still has the card. ATM PIN use does not by itself determine authorisation. Record location, timestamp/timezone, amount, reference and who had card/device access.
- Standard reporting window is 30 calendar days; staff assess late reports without automatic forfeiture. Acknowledge within 1 business day and target ATM reconciliation within 10 business days after complete evidence; approved credit takes 2 business days. A recognised withdrawal with missing cash instead routes to wrong_amount_of_cash_received, with security protection retained if equipment was suspicious.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Immediately protect a physical debit card reported lost or stolen. | `lost_or_stolen_card` |
| Protect and investigate an unrecognised debit-card purchase. | `card_payment_not_recognised` |
| Respond to suspected exposure of debit-card credentials whether or not a fraudulent charge exists. | `compromised_card` |
| Respond to an alleged unrecognised direct debit when NovaBank does not offer direct-debit mandates. | `direct_debit_payment_not_recognised` |
| Secure NovaBank access and wallet tokens after a phone is lost or stolen. | `lost_or_stolen_phone` |
| Secure and investigate an alleged unauthorised ATM withdrawal. | `cash_withdrawal_not_recognised` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| lost_or_stolen_card / compromised_card | A missing physical card is loss/theft; suspected credential exposure can be compromise even while the card is in the customer's possession. |
| compromised_card / card_payment_not_recognised | Exposure may exist without a charge; an alleged unauthorised purchase needs an additional transaction dispute. |
| card_payment_not_recognised / cash_withdrawal_not_recognised | Merchant/card debits use the card-dispute path; ATM debits use ATM reconciliation and its own intake clock. |
| direct_debit_payment_not_recognised / card subscription | No direct-debit mandate exists; classify the actual ledger method without dismissing the allegation. A recurring card purchase remains a card transaction. |
| lost_or_stolen_phone / passcode_forgotten | Loss/theft requires device/token protection; a forgotten code without loss follows account recovery. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not guarantee fraud prevention or reimbursement, treat PIN use as conclusive authorisation, reactivate permanently cancelled cards, skip identity verification, dismiss alleged unauthorised debits because their described method is unsupported, create direct-debit mandates, or recommend products while a complaint remains unresolved.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
