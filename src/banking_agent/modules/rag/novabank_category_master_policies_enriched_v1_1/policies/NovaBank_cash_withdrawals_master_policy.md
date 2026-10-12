---
policy_id: DOC-CAT-ATM-001
business_category: cash_withdrawals
included_intents:
  - pending_cash_withdrawal
  - wrong_amount_of_cash_received
  - atm_support
  - declined_cash_withdrawal
  - card_swallowed
  - wrong_exchange_rate_for_cash_withdrawal
  - cash_withdrawal_charge
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
  - REF-07
  - REF-08
  - REF-05
  - REF-04
---

## NovaBank ATM Access, Cash Dispensing and Withdrawal Charges Master Policy

### Purpose and Category Scope

Recognised ATM withdrawals and physical-card retention at supported Visa/PLUS ATMs. Cash and cheque deposits are not supported services.

### Common Fees, Limits and Service Conditions

Use an active physical NovaBank Visa debit card and its PIN. Withdrawal limits are SGD-equivalent 500 per transaction and 1,000 per Singapore calendar day. Each completed withdrawal costs SGD 2; a failed no-cash attempt costs SGD 0 in NovaBank withdrawal fees. Withdrawals debit SGD, including foreign-currency cash, and conversion adds 0.50% with minimum SGD-equivalent 0.50. Operator fees are separate.

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

### Currency Conversion Boundary

Only SGD, USD, EUR, GBP and AUD are supported. Card purchases use a sufficient same-currency balance first; otherwise the whole purchase converts from SGD. ATM cash withdrawals always use SGD funding. NovaBank FX fee is 0.50% of source principal, minimum SGD-equivalent 0.50, rounded half-up to 2 decimal places. No weekend surcharge or additional NovaBank FX spread applies. If the merchant or ATM operator converts into SGD, NovaBank performs no conversion and charges no NovaBank FX fee; operator/merchant pricing is independent. A completed ATM withdrawal still costs SGD 2.

### Counter and Available-Balance Interpretation

Purchase, ATM, card-top-up and outgoing bank-transfer limits are separate channel counters and apply at account level, not separately to each physical card, virtual card, wallet device or funding card. Available balance excludes authorisation holds and funds under an applicable review restriction. Principal counts toward transaction value limits; available balance must additionally cover disclosed fees. An approved attempt is assigned to its acceptance date for daily/monthly counting; a release can restore reserved capacity only in the still-current counting period. A refund or reversal of a completed transaction does not reset historical used limits or create new capacity in the earlier period. Where a product-specific limit is lower, the stricter limit applies.

### Physical Safety and Cash-Outcome Evidence

ATM acceptance, authorisation, cash dispensing and final ledger posting are different events. Record requested principal and actual cash, even if the ledger is pending. Do not inspect or open ATM equipment, accept help from an unverified person or repeat a withdrawal to offset a shortfall. A retained card needs protection immediately; an associated cash debit receives a separately linked reconciliation. A physical-card replacement does not resolve a cash claim. Terminal currency and DCC choice must be captured independently from fee lines.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### pending_cash_withdrawal — Explain an ATM debit that remains pending rather than settled or reversed

**Intent definition:** Explain an ATM debit that remains pending rather than settled or reversed.

**Processing, conditions, fees and limits:**

- Record the ATM location, withdrawal date/time, requested currency/amount, transaction reference, and whether any cash was dispensed. A normal ATM authorisation settles or reverses within 3 calendar days.
- If the third calendar day ends with the authorisation still pending, open an ATM enquiry. Staff acknowledge within 1 business day and complete an ATM reconciliation decision within 10 business days after complete evidence.
- If no cash was dispensed, report the failure immediately rather than retrying solely because the balance has a hold. A confirmed erroneous debit is restored within 2 business days after approval.
- ATM withdrawals are limited to SGD-equivalent 500 per transaction and 1,000 per Singapore calendar day. Each completed withdrawal has a SGD 2 NovaBank fee; a failed withdrawal must not retain that bank fee.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** Immediate release of a valid ATM hold without reconciliation is unsupported. Cash shortage after a settled withdrawal belongs to wrong_amount_of_cash_received; an unknown withdrawal is a security escalation.

**Operational exceptions and status checks:**

- Record requested amount, actual cash received, ATM operator/location/ID, local time with timezone and masked reference. No cash or short cash must be reported immediately even if the ledger is PENDING; the customer is not required to wait three days before reporting.
- The pending hold ceiling is 3 calendar days. An internal overdue-status case is reviewed within 2 business days at SGD 0; a cash-dispensing discrepancy uses the 30-calendar-day intake, acknowledgement within 1 business day and 10-business-day reconciliation after complete evidence. A failed no-cash attempt has no NovaBank withdrawal fee; assess any operator charge separately.

### wrong_amount_of_cash_received — Investigate a cash shortage or excess from a recognised ATM withdrawal

**Intent definition:** Investigate a cash shortage or excess from a recognised ATM withdrawal.

**Processing, conditions, fees and limits:**

- ATM limits are SGD-equivalent 500 per transaction and 1,000 per calendar day, with a SGD 2 NovaBank fee for each completed withdrawal. Compare the requested amount, posted debit and actual banknotes dispensed.
- Report a discrepancy within 30 calendar days of the withdrawal. Provide the transaction reference, ATM identifier/location, timestamp, receipt and counted cash amount; never include a PIN.
- Staff acknowledge within 1 business day and complete an ATM reconciliation decision within 10 business days after receiving complete evidence. A confirmed shortage or erroneous fee is credited within 2 business days after approval.
- An ATM-reported excess requires reconciliation and may be corrected only after notice and verified evidence. No adjustment is promised solely from an unverified customer statement.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** A pending authorisation without settled cash reconciliation uses pending_cash_withdrawal. An unknown withdrawal is escalated under cash_withdrawal_not_recognised. Guaranteed provisional refunds are unsupported.

**Operational exceptions and status checks:**

- Treat both shortages and excess cash as discrepancies. Retain the receipt if safely available and note denomination counts; do not retry to compensate, tamper with the machine or hand cash to an unverified caller. Actual cash figures, not only the requested amount, are required for reconciliation.
- Report within 30 calendar days, at SGD 0 investigation cost. Acknowledge within 1 business day, target a decision within 10 business days after complete evidence and credit an approved shortage within 2 business days. Excess cash is referred for an authorised reconciliation instruction; the assistant cannot invent a repayment recipient or outcome.

### atm_support — Explain supported ATM use for a physical NovaBank Visa debit card

**Intent definition:** Explain supported ATM use for a physical NovaBank Visa debit card.

**Processing, conditions, fees and limits:**

- Only an active physical NovaBank Visa debit card with a valid PIN can withdraw at compatible Visa/PLUS ATMs. ATM currency must be SGD, USD, EUR, GBP or AUD.
- Withdrawals are limited to SGD-equivalent 500 per transaction and 1,000 per Singapore calendar day. NovaBank charges SGD 2 for each completed withdrawal; an ATM operator may separately disclose its own fee.
- ATM withdrawals debit SGD and convert foreign ATM currency using the NovaBank quote plus a 0.50% conversion fee with SGD 0.50 minimum. ATM-selected dynamic currency conversion uses the operator's rate.
- Virtual cards, wallet tokens and disposable cards cannot withdraw cash. An ATM-support enquiry is reviewed within 2 business days; no-cash or cash-shortage cases use the 10-business-day reconciliation decision window.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** Cash deposits, cheque deposits, ATM support at every machine, unsupported currencies and virtual-card cash withdrawal are rejected or unsupported. An actual withdrawal decline uses declined_cash_withdrawal.

**Operational exceptions and status checks:**

- Use only an active physical Visa card at a Visa/PLUS ATM dispensing SGD, USD, EUR, GBP or AUD. Acceptance, available denominations, terminal cash stock and operator limits may further constrain a request; a network logo is not an approval guarantee.
- Public compatibility advice is immediate at SGD 0. Each completed withdrawal costs SGD 2 plus applicable NovaBank FX and disclosed operator charges, with principal caps of SGD-equivalent 500 each and 1,000 daily. Virtual cards, wallet tokens, unsupported currencies and deposit transactions are not permitted at an ATM under this policy.

### declined_cash_withdrawal — Troubleshoot an ATM withdrawal that was refused and dispensed no cash

**Intent definition:** Troubleshoot an ATM withdrawal that was refused and dispensed no cash.

**Processing, conditions, fees and limits:**

- Check card activation/freeze status, PIN block, supported ATM network/currency and available SGD balance. Limits are SGD-equivalent 500 per transaction and 1,000 per calendar day; a completed withdrawal costs SGD 2 plus disclosed conversion or operator fees.
- A declined attempt has a NovaBank withdrawal fee of SGD 0. If the attempt created an authorisation hold, it must settle or reverse within 3 calendar days.
- Do not repeat a withdrawal if a no-cash attempt already debited or reserved funds. Record ATM identifier, time, amount, reference and any receipt; staff acknowledge within 1 business day.
- Unresolved holds or debit-with-no-cash incidents receive an ATM reconciliation decision within 10 business days after complete evidence, with approved corrections within 2 business days.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** A declined withdrawal cannot be forced through by support chat. A wrong cash amount is a shortage/excess case; an unrecognised withdrawal requires immediate security escalation.

**Operational exceptions and status checks:**

- Check activation, expiry, eligible physical card, PIN-block state, enabled card controls, SGD available funds including fees and ATM/operator limits. A foreign balance cannot replace insufficient SGD withdrawal funds. Stop guessing the PIN after three consecutive wrong attempts.
- A refused no-cash withdrawal has NovaBank fee SGD 0 and must not be described as completed. If a debit or hold is present, route also to pending_cash_withdrawal or wrong_amount_of_cash_received. An unexplained terminal refusal is reviewed within 2 business days at SGD 0; do not advise multiple rapid withdrawals.

### card_swallowed — Secure a physical debit card retained by an ATM

**Intent definition:** Secure a physical debit card retained by an ATM.

**Processing, conditions, fees and limits:**

- Freeze the retained card in the authenticated app within 60 seconds and record the ATM operator, location, timestamp and card's last four digits. Urgent security staff are available 24/7 if theft or tampering is suspected.
- Contact the ATM operator for its retention process; NovaBank does not guarantee card retrieval. Permanently cancel a card not securely recovered rather than unfreezing it on an unverified operator statement.
- Customer-requested physical replacement costs SGD 15 and takes 5 business days. Card cancellation or replacement does not itself resolve an associated cash debit.
- If cash was not dispensed but the account was debited, open an ATM reconciliation: acknowledgement within 1 business day, decision within 10 business days after complete evidence and approved correction within 2 business days.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** Forcing an ATM to release a card, instructing a customer to dismantle the ATM, and guaranteeing a swallowed-card refund are prohibited. atm_support concerns compatibility; wrong_amount_of_cash_received concerns dispensed cash.

**Operational exceptions and status checks:**

- Securely freeze the retained card within 60 seconds at SGD 0 and notify urgent security staff immediately if the ATM seems altered. Note ATM ID/operator and time without touching the machine. Staff cannot guarantee operator retrieval; even an operator-returned card remains blocked until a security decision.
- Permanent retirement is irreversible and suspends linked wallet tokens within 5 minutes. An accepted replacement costs SGD 15, with standard arrival Day 5 for SGD 0 shipping or express Day 2 for SGD 10 shipping to a verified Singapore address. No overseas emergency delivery or agent pickup is offered; a related no-cash debit gets a separate linked reconciliation.

### wrong_exchange_rate_for_cash_withdrawal — Investigate the conversion rate applied to a recognised ATM cash withdrawal

**Intent definition:** Investigate the conversion rate applied to a recognised ATM cash withdrawal.

**Processing, conditions, fees and limits:**

- NovaBank ATM withdrawals debit SGD, including supported foreign-currency cash withdrawals. When converting, apply the transaction quote plus a 0.50% conversion fee with a SGD 0.50 minimum; each completed withdrawal also has a SGD 2 bank fee.
- ATM dynamic currency conversion uses the operator's rate when the customer accepts it. An operator surcharge is separate from NovaBank conversion and withdrawal fees.
- Provide the ATM identifier, receipt, requested currency, cash amount, SGD debit and transaction reference. Submit an alleged rate-calculation error within 60 calendar days of settlement.
- Staff acknowledge within 1 business day and finish an internal calculation review within 5 business days after complete evidence. A confirmed NovaBank error is corrected within 2 business days after approval.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** Reimbursement merely for an accurately applied unfavourable rate and overriding an operator quote are unsupported. A cash shortage uses wrong_amount_of_cash_received; purchase-rate disputes use card_payment_wrong_exchange_rate.

**Operational exceptions and status checks:**

- The receipt must identify local cash currency/amount and whether the operator converted into SGD. NovaBank converts supported foreign cash from SGD; holding enough foreign currency does not change this. Operator DCC rates are distinct from NovaBank settlement-rate calculations.
- Fee-free rate review intake is 60 calendar days after posting; internal calculation review takes 5 business days with approved correction within 2 business days. Separate the SGD 2 withdrawal fee, 0.50% FX fee with minimum equivalent 0.50 and operator surcharge. A cash shortage instead uses the 30-calendar-day ATM reconciliation window.

### cash_withdrawal_charge — Explain fees on a completed recognised ATM withdrawal

**Intent definition:** Explain fees on a completed recognised ATM withdrawal.

**Processing, conditions, fees and limits:**

- NovaBank charges SGD 2 for each completed ATM withdrawal, with limits of SGD-equivalent 500 per transaction and 1,000 per calendar day. No NovaBank withdrawal fee is retained for a failed no-cash withdrawal.
- The ATM operator may separately disclose a surcharge. Foreign-currency cash withdrawals debit SGD and add NovaBank conversion of 0.50% with SGD 0.50 minimum, unless operator-selected dynamic conversion determines the currency rate.
- Check the ATM receipt and separate fee entries to distinguish bank withdrawal fee, conversion fee and operator surcharge. Report an alleged NovaBank fee error within 60 calendar days of posting.
- Staff acknowledge within 1 business day and review bank fee calculations within 5 business days after complete evidence. Approved bank fee corrections post within 2 business days; missing cash instead receives ATM reconciliation within 10 business days.

**Verification and required evidence:** Authenticate before accessing the debit or changing card state. Provide ATM identifier/location, date/time, reference, currency, requested amount and dispensed amount; include a masked ATM receipt if available. No fresh ID is required with current verification. Never supply a PIN; a missing receipt does not postpone urgent security escalation.

**Fee and limit reference:** Enquiry, freeze and reconciliation review cost SGD 0. A completed cash withdrawal costs SGD 2 plus applicable conversion and disclosed operator fees; maximum principal is 500 equivalent each and 1,000 daily. A physical replacement is SGD 15 plus delivery. One coordinated ATM case per withdrawal prevents duplicate corrections.

**Intent boundary and unsupported requests:** Guaranteed reimbursement of another ATM operator's surcharge or waiver of all valid withdrawal fees is unsupported. Rate disputes use wrong_exchange_rate_for_cash_withdrawal; retained cards use card_swallowed.

**Operational exceptions and status checks:**

- The completed principal counts against the withdrawal limits; available SGD must additionally cover NovaBank fee SGD 2, the applicable 0.50% FX fee with minimum equivalent 0.50, and any accepted operator surcharge. Operator fees are determined by that operator and cannot be quoted as a fixed NovaBank charge.
- A failed no-cash attempt has NovaBank withdrawal fee SGD 0. Submit receipt, fee lines and reference within 60 calendar days of a disputed bank-fee posting for a 5-business-day free review; approved correction credits within 2 business days. Disputes about actual cash use the 10-business-day cash reconciliation route instead.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Explain an ATM debit that remains pending rather than settled or reversed. | `pending_cash_withdrawal` |
| Investigate a cash shortage or excess from a recognised ATM withdrawal. | `wrong_amount_of_cash_received` |
| Explain supported ATM use for a physical NovaBank Visa debit card. | `atm_support` |
| Troubleshoot an ATM withdrawal that was refused and dispensed no cash. | `declined_cash_withdrawal` |
| Secure a physical debit card retained by an ATM. | `card_swallowed` |
| Investigate the conversion rate applied to a recognised ATM cash withdrawal. | `wrong_exchange_rate_for_cash_withdrawal` |
| Explain fees on a completed recognised ATM withdrawal. | `cash_withdrawal_charge` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| atm_support / declined_cash_withdrawal | A general network/currency question uses atm_support; an actual refused cash request uses declined_cash_withdrawal. |
| pending_cash_withdrawal / wrong_amount_of_cash_received | Unsettled ATM authorisation uses pending; settled cash shortage or excess uses wrong_amount_of_cash_received. A no-cash debit is reported immediately regardless of pending status. |
| card_swallowed / cash discrepancy | Retention concerns securing the physical card; an associated debit needs its own ATM reconciliation. |
| wrong_exchange_rate_for_cash_withdrawal / cash_withdrawal_charge | The conversion rate differs from the bank withdrawal fee, FX fee and operator surcharge. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not offer cash or cheque deposits, wallet/virtual/disposable ATM withdrawals, ATM acceptance guarantees, unauthenticated PIN disclosure, physical ATM tampering, guaranteed recovery of retained cards, or automatic refunds before reconciliation. Unrecognised withdrawals route immediately to security.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
