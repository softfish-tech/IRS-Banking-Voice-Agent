---
policy_id: DOC-CAT-REFUND-001
business_category: refunds
included_intents:
  - request_refund
  - Refund_not_showing_up
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
  - REF-24
  - REF-06
  - REF-18
  - REF-04
---

## NovaBank Recognised Purchase Refund Requests and Missing Refunds Master Policy

### Purpose and Category Scope

Requests and traces for recognised settled debit-card purchases. Unrecognised payments belong to security; normal authorisation releases and network reversals belong to card_payments.

### Common Fees, Limits and Service Conditions

Refund request intake, dispute review and refund trace cost SGD 0. Merchant-issued refunds normally appear within 5 business days from confirmation of issuance. NovaBank-approved dispute refunds credit within 2 business days after approval. The standard recognised card-dispute intake window is 60 calendar days after settlement; target decision is 30 calendar days after complete evidence.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Issuance Evidence, Credit Ownership and Recovery Ceilings

A merchant agreement to refund, a submitted merchant instruction and an actual posted credit are different events. Record the issuance date and reference before starting the five-business-day clock. Original-transaction identity determines destination even when the payment credential is no longer active. Authorisation releases and settled reversals use card_payments rather than the merchant-refund clock. Partial credits reduce outstanding recoverable principal; simultaneous merchant and bank recovery must be reconciled without double compensation. No refund processing action is executed merely by retrieval.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### request_refund — Request a refund or dispute for a recognised, settled debit-card purchase

**Intent definition:** Request a refund or dispute for a recognised, settled debit-card purchase.

**Processing, conditions, fees and limits:**

- First request a refund from the merchant for a recognised purchase, keeping the receipt, return/cancellation confirmation and transaction reference. An ordinary merchant refund appears within 5 business days after the merchant confirms it has been issued.
- If the merchant refuses or fails to resolve the recognised dispute, submit a NovaBank dispute within 60 calendar days of settlement. Provide the receipt, reason and evidence of contact with the merchant.
- NovaBank acknowledges within 1 business day and targets a decision within 30 calendar days after complete evidence. Approved bank dispute refunds are credited within 2 business days after approval; review costs SGD 0.
- Card refunds return to the originating account balance used for the purchase; refunds to an expired, replaced or retired disposable card are matched to the original transaction. Any conversion uses the original settlement treatment, avoiding a newly invented refund fee.
- A refund cannot exceed original settled principal less earlier refunds. If NovaBank converted an original purchase from SGD, restore principal using its original settlement rate; do not apply a current FX quote. The original correctly charged NovaBank conversion fee remains unless an approved bank-error correction explicitly refunds it. A same-currency purchase refunds to its original currency balance.
- A bank-approved correction and an issued merchant refund for the same principal must be coordinated under one case. Staff reconcile any confirmed double recovery after notice and verified evidence; the review fee remains SGD 0.

**Verification and required evidence:** Authenticate before accessing purchase/refund records. Supply the original transaction reference, amount, settlement date, receipt and merchant correspondence. A missing issued refund also requires issue date, refund amount and merchant refund reference. No fresh ID is required with current account verification; a mere merchant promise is not issuance evidence.

**Fee and limit reference:** Request, recognised dispute and trace fees are SGD 0. At most one active refund/dispute case per original purchase is permitted. Total credited refunds must not exceed its original settled principal; prevent double recovery across merchant credits and bank-approved corrections. Refund credits do not create a new purchase allowance or restore an earlier day's spending counter.

**Intent boundary and unsupported requests:** Refund approval based only on a request, guaranteed recovery, and refunds to another person or unrelated card are unsupported. An already issued but missing refund uses Refund_not_showing_up; unauthorised transactions are urgent security reports.

**Operational exceptions and status checks:**

- For a recognised settled purchase, retain the original receipt, merchant communications and reason: cancellation, goods not received, wrong goods or agreed partial refund. The merchant's promise is not issuance. A pending original purchase instead uses hold/reversal handling; an unrecognised purchase goes immediately to security.
- Intake and trace cost SGD 0. Submit a recognised dispute within 60 calendar days of settlement, with acknowledgement within 1 business day and target decision within 30 calendar days after complete evidence. Merchant-issued credits target 5 business days from issuance; bank-approved compensation targets 2 business days from approval. Aggregate principal recovery cannot exceed the original settled principal less prior credits.
- A matched refund can reach the original account after a physical replacement or virtual/disposable retirement. For a converted purchase, refund principal uses the original settlement rate with no new NovaBank conversion fee; the correct original FX fee remains unless an authorised error correction refunds it. Inform staff if a merchant pays during an open dispute to prevent double compensation.

### Refund_not_showing_up — Trace a merchant-confirmed refund that has not appeared on the originating NovaBank account

**Intent definition:** Trace a merchant-confirmed refund that has not appeared on the originating NovaBank account.

**Processing, conditions, fees and limits:**

- The merchant-refund window is 5 business days from the merchant's confirmation that the refund was issued, not from the date the customer first requested it.
- After the fifth business day ends, provide the original transaction reference, refund amount, issue date and merchant refund reference. Staff acknowledge within 1 business day and provide an initial trace result within 2 business days after complete evidence.
- Merchant refunds return to the originating account balance used for the purchase; replacement, expiry or disposable-card retirement does not prevent matching the original transaction. NovaBank charges SGD 0 to trace the refund.
- A NovaBank-approved dispute refund has a separate 2-business-day credit window after approval. A mere merchant promise to consider a refund is not proof of issuance.
- Partial refunds are matched to the original purchase and cumulatively capped at its settled principal. Confirmed duplicate recovery is reconciled after notice; tracing does not create entitlement to a second refund. Use the original currency/settlement treatment and do not add a new FX fee.

**Verification and required evidence:** Authenticate before accessing purchase/refund records. Supply the original transaction reference, amount, settlement date, receipt and merchant correspondence. A missing issued refund also requires issue date, refund amount and merchant refund reference. No fresh ID is required with current account verification; a mere merchant promise is not issuance evidence.

**Fee and limit reference:** Request, recognised dispute and trace fees are SGD 0. At most one active refund/dispute case per original purchase is permitted. Total credited refunds must not exceed its original settled principal; prevent double recovery across merchant credits and bank-approved corrections. Refund credits do not create a new purchase allowance or restore an earlier day's spending counter.

**Intent boundary and unsupported requests:** A duplicate provisional refund, crediting an unissued merchant refund, or paying an unrelated account is unsupported. request_refund concerns requesting or disputing a purchase before a refund has been issued.

**Operational exceptions and status checks:**

- Obtain the original purchase reference, refund amount/currency, merchant issuance date and refund reference or acquirer reference if available. Search both a new refund credit and an update to the original authorisation/reversal; merchant and issuer descriptors or dates may differ. An unused promise does not start the five-business-day issuance clock.
- After 5 business days from confirmed merchant issuance without credit, open an SGD 0 trace with an initial update within 2 business days of complete evidence. A declined/reverted merchant refund needs confirmation and reissue by the merchant; do not claim it already credited. A bank-approved missing credit instead uses the 2-business-day approval clock.
- Refund matching uses the original transaction, including inactive, replaced and one-use cards; no new disposable card or unrelated recipient account is required. Partial credits leave only the unrecovered principal eligible for investigation. An already closed account requires staff exception handling; do not promise reopening or invent a new payout route.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Request a refund or dispute for a recognised, settled debit-card purchase. | `request_refund` |
| Trace a merchant-confirmed refund that has not appeared on the originating NovaBank account. | `Refund_not_showing_up` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| request_refund / Refund_not_showing_up | Before confirmed issuance, request/refusal/dispute uses request_refund; after confirmed issuance and its deadline, trace under Refund_not_showing_up. |
| merchant refund / bank-approved dispute credit | Merchant issuance starts a 5-business-day clock; bank dispute approval starts a 2-business-day clock. |
| refund / reverted_card_payment? | Refund follows settlement and merchant issuance; authorisation release/network reversal uses a different event and clock. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not guarantee merchant cooperation, credit a merely promised or unissued refund, grant duplicate provisional refunds, send refunds to an unrelated card/account, invent new refund-conversion fees, or treat an unresolved dispute as resolved on intake.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
