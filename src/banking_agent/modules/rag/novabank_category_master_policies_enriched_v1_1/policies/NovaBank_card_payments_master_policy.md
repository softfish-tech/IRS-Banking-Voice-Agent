---
policy_id: DOC-CAT-CARDPAY-001
business_category: card_payments
included_intents:
  - card_payment_wrong_exchange_rate
  - extra_charge_on_statement
  - card_payment_fee_charged
  - pending_card_payment
  - declined_card_payment
  - transaction_charged_twice
  - reverted_card_payment?
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
  - REF-04
  - REF-06
  - REF-03
---

## NovaBank Debit Card Purchases, Authorisations and Posting Disputes Master Policy

### Purpose and Category Scope

Recognised physical, reusable virtual, disposable virtual and eligible wallet purchases, including purchase status, fees, duplicate postings and reversals. An unrecognised purchase immediately routes to the security category.

### Common Fees, Limits and Service Conditions

Account purchase limits are SGD-equivalent 5,000 per transaction and 10,000 per Singapore calendar day, shared across all card forms. Disposable purchases additionally have a maximum of 500 each. Ordinary NovaBank purchase fee is SGD 0. Conversion costs 0.50%, minimum SGD-equivalent 0.50, only when NovaBank performs conversion. Normal authorisation holds last up to 7 calendar days; eligible labelled hotel/rental deposits last up to 30 calendar days.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Currency Conversion Boundary

Only SGD, USD, EUR, GBP and AUD are supported. Card purchases use a sufficient same-currency balance first; otherwise the whole purchase converts from SGD. ATM cash withdrawals always use SGD funding. NovaBank FX fee is 0.50% of source principal, minimum SGD-equivalent 0.50, rounded half-up to 2 decimal places. No weekend surcharge or additional NovaBank FX spread applies. If the merchant or ATM operator converts into SGD, NovaBank performs no conversion and charges no NovaBank FX fee; operator/merchant pricing is independent. A completed ATM withdrawal still costs SGD 2.

### Counter and Available-Balance Interpretation

Purchase, ATM, card-top-up and outgoing bank-transfer limits are separate channel counters and apply at account level, not separately to each physical card, virtual card, wallet device or funding card. Available balance excludes authorisation holds and funds under an applicable review restriction. Principal counts toward transaction value limits; available balance must additionally cover disclosed fees. An approved attempt is assigned to its acceptance date for daily/monthly counting; a release can restore reserved capacity only in the still-current counting period. A refund or reversal of a completed transaction does not reset historical used limits or create new capacity in the earlier period. Where a product-specific limit is lower, the stricter limit applies.

### Authorisation, Settlement, Reversal and Refund Definitions

PENDING reserves available funds; SETTLED posts principal; DECLINED refuses authorisation; an authorisation release removes a hold; a settled reversal unwinds a posted transaction; a merchant refund is a separate credit linked to a settled purchase. Compare masked references and statuses before deciding the route. A released hold, frozen card or retired credential does not automatically nullify earlier valid authorisations. Two separate merchant submissions need investigation rather than an automatic duplicate conclusion. Only labelled physical/reusable hotel or rental deposits receive the 30-calendar-day hold ceiling.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### card_payment_wrong_exchange_rate — Investigate the exchange rate applied to a settled debit-card purchase

**Intent definition:** Investigate the exchange rate applied to a settled debit-card purchase.

**Processing, conditions, fees and limits:**

- Check the settled transaction reference, original merchant currency, settlement date, SGD debit, quoted rate and any merchant dynamic currency conversion receipt. A pending purchase is not yet a final-rate discrepancy.
- NovaBank conversion applies only when the purchase currency has insufficient same-currency balance. It uses the settlement quote, with a separately identified 0.50% conversion fee subject to a SGD 0.50 minimum.
- A merchant-selected SGD conversion uses the merchant's rate, not NovaBank's reference rate. Staff must distinguish that choice from a NovaBank calculation error.
- Submit an alleged rate error within 60 calendar days of settlement. Staff acknowledge within 1 business day and finish the internal calculation review within 5 business days after complete evidence; a confirmed bank error is corrected within 2 business days after approval, at SGD 0.
- Use rate as destination units per source unit and show the transaction-specific quote timestamp. A transaction that the merchant converted into SGD attracts no NovaBank FX fee, although the merchant conversion itself may be disputed through the recognised merchant-dispute process.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** Profit from later exchange-rate changes, reimbursement of an accurately disclosed rate and automatic reversal of merchant dynamic currency conversion are unsupported. Merchant disputes may be reviewed separately; cash-withdrawal rates use a different intent.

**Operational exceptions and status checks:**

- Collect original receipt currency, DCC selection if shown, authorised amount, final settlement amount/date and masked reference. If a merchant converted to SGD, its rate cannot be compared as a NovaBank rate. A sufficient same-currency purchase has no NovaBank conversion; insufficient matching funds route the entire purchase through SGD.
- The settled calculation, rather than an earlier authorisation or public rate, governs the check. Intake is within 60 calendar days of settlement at SGD 0; internal calculation review is 5 business days and an approved correction credits within 2 business days. A merchant conversion disagreement follows the 30-calendar-day recognised-dispute review instead of an automatic bank fee refund.

### extra_charge_on_statement — Explain an additional settled debit-card statement amount that is not yet identified as a fee or duplicate

**Intent definition:** Explain an additional settled debit-card statement amount that is not yet identified as a fee or duplicate.

**Processing, conditions, fees and limits:**

- Compare the original purchase, separate statement entry, merchant name, settlement date and reference. A pending deposit or authorisation hold is not a settled extra charge.
- NovaBank purchase fees are SGD 0 for ordinary purchases; applicable currency conversion is 0.50% with a SGD 0.50 minimum. A merchant surcharge is merchant-originated and must be evidenced by its receipt.
- Submit a recognised-merchant amount enquiry within 60 calendar days of settlement with a masked receipt and transaction reference. Staff acknowledge within 1 business day and explain the entry within 5 business days after receiving complete evidence.
- If a bank posting error is confirmed, the correction is credited within 2 business days after approval. A contested merchant amount proceeds to the 30-calendar-day dispute review; no refund is guaranteed.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** An unexplained charge must not automatically be labelled a bank fee or duplicate. Unrecognised purchases are escalated under card_payment_not_recognised; two matching settled entries use transaction_charged_twice.

**Operational exceptions and status checks:**

- Check whether the extra line is a hold, settlement, disclosed FX fee, merchant adjustment or another merchant descriptor before calling it an extra settled charge. A merchant trading name may differ from its legal descriptor; recognition checking must not delay a customer who denies authorising it.
- Submit receipts, both masked ledger references and amounts for an SGD 0 review within 60 calendar days of settlement. Internal posting/fee errors use 5 business days and approved correction 2 business days; recognised merchant amount disputes target 30 calendar days from complete evidence. Unrecognised lines route immediately to security.

### card_payment_fee_charged — Explain or challenge an explicitly identified NovaBank fee on a debit-card purchase

**Intent definition:** Explain or challenge an explicitly identified NovaBank fee on a debit-card purchase.

**Processing, conditions, fees and limits:**

- Ordinary debit-card purchases have a NovaBank purchase fee of SGD 0. Where NovaBank converts currency, the conversion fee is 0.50% with a SGD 0.50 minimum equivalent, separately shown from the purchase amount.
- Merchant surcharges and merchant dynamic currency conversion are not NovaBank purchase fees. A same-currency purchase paid from sufficient same-currency balance has no NovaBank conversion fee.
- Compare the fee entry, transaction reference, purchase currency, balance used and receipt. Submit an alleged fee error within 60 calendar days of settlement.
- Staff acknowledge within 1 business day and complete an internal fee review within 5 business days after complete evidence. A confirmed NovaBank fee error is credited within 2 business days after approval; no blanket fee waiver is promised.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** Refunding a properly disclosed fee merely because it is unwanted, or refunding another party's surcharge without a dispute decision, is unsupported. extra_charge_on_statement concerns an unidentified extra entry; exchange_charge covers conversion fees generally.

**Operational exceptions and status checks:**

- Ordinary purchase fee is SGD 0. Separately posted NovaBank conversion costs 0.50%, minimum SGD-equivalent 0.50, only when NovaBank actually converts. Do not label a merchant surcharge or DCC margin as a NovaBank fee, or introduce an overseas administrative fee from another bank.
- Request the fee reference, principal, source/charged currencies, conversion record and settlement date. A fee-only complaint is free to review within 5 business days after complete evidence, with approved correction within 2 business days; submit within 60 calendar days of posting. A correct original FX fee is not automatically refunded when the purchase principal is later refunded.

### pending_card_payment — Explain a merchant card authorisation not yet submitted as a settled purchase

**Intent definition:** Explain a merchant card authorisation not yet submitted as a settled purchase.

**Processing, conditions, fees and limits:**

- A normal pending card purchase holds available balance until merchant settlement or release, normally within 7 calendar days from authorisation. A supported reusable/physical-card hotel or rental deposit may hold for up to 30 calendar days when labelled as a deposit.
- A pending authorisation is not a second settled charge. Compare transaction references before treating one pending and one settled entry as a duplicate.
- NovaBank cannot unilaterally cancel a valid merchant authorisation. An authenticated customer may submit a merchant release confirmation; staff review within 2 business days, without promising immediate release.
- Report a normal hold still present after 7 calendar days, or a deposit hold after 30 calendar days; staff acknowledge within 1 business day and review within 2 business days. Pending-status enquiries cost SGD 0.
- Authorisation reserves both available principal and expected applicable NovaBank FX fee. Merchant settlement replaces the hold rather than adding an independent debit for the same purchase. A pending enquiry costs SGD 0 and does not permit exceeding account caps.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** Disposable cards do not support deposits or preauthorisations. Unknown pending payments are still security reports; a pending status must not delay escalation. Merchant refunds use request_refund or Refund_not_showing_up.

**Operational exceptions and status checks:**

- An approved authorisation reduces available funds without proving settlement. A normal hold expires after at most 7 calendar days; labelled hotel/rental deposit holds on physical or reusable cards allow at most 30 calendar days. Disposable deposit/preauthorisation attempts are unsupported.
- Customer freeze, replacement or merchant cancellation confirmation does not itself cancel an approved hold. Check for a matching settlement before treating a hold plus posting as duplication. Report a hold beyond its applicable deadline immediately for an SGD 0 technical review within 2 business days; do not wait out an alleged fraudulent authorisation.

### declined_card_payment — Explain an actual card-purchase authorisation decline

**Intent definition:** Explain an actual card-purchase authorisation decline.

**Processing, conditions, fees and limits:**

- Check available balance, activation, expiry, freeze status, merchant/currency acceptance and required authentication. Account purchase limits are SGD-equivalent 5,000 per transaction and 10,000 per calendar day.
- A declined purchase costs SGD 0 in NovaBank purchase fees and should not create a final settled purchase. Any associated normal authorisation hold follows the 7-calendar-day release/settlement window.
- Three incorrect physical-card PIN entries cause a PIN block; contactless over SGD-equivalent 100 per transaction or 300 cumulative requires chip-and-PIN. Security declines cannot be bypassed by support.
- Collect the masked reference, merchant, amount, timestamp and displayed decline reason. Staff acknowledge within 1 business day and diagnose within 2 business days after complete evidence.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** Forcing authorisation, assuring merchant acceptance and treating a declined attempt as a settled refund case are unsupported. card_not_working covers general physical-card malfunction; pending_card_payment covers a successful unresolved authorisation.

**Operational exceptions and status checks:**

- An issuer DECLINED record is a refusal, not a settled debit. Check available principal plus fees, account-shared limits, card controls and secure merchant authentication. A merchant error or app timeout without a final issuer record is unknown status; look up the original reference before retrying.
- A declined attempt costs SGD 0 in NovaBank purchase fees. An approved hold associated with another reference follows pending_card_payment rather than a refund promise. Staff investigate an unexplained persistent refusal within 2 business days after masked evidence; never ask the customer to defeat a security control or generate multiple retries.

### transaction_charged_twice — Investigate two settled debit-card purchase entries alleged to represent one purchase

**Intent definition:** Investigate two settled debit-card purchase entries alleged to represent one purchase.

**Processing, conditions, fees and limits:**

- A duplicate allegation requires 2 settled entries for the same underlying purchase. One pending authorisation plus one settled transaction is not sufficient evidence of a double charge.
- Collect both transaction references, merchant name, dates, amounts and one-purchase receipt. Submit the recognised duplicate dispute within 60 calendar days of settlement.
- Staff acknowledge within 1 business day and complete the initial posting check within 5 business days after complete evidence. A confirmed NovaBank duplicate posting is corrected within 2 business days after approval.
- If the merchant submitted two independent settled purchases, request merchant correction or proceed to the 30-calendar-day dispute decision target. Review costs SGD 0; no automatic duplicate refund is guaranteed.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** Two different purchases of the same amount are not automatically duplicates. Unknown purchases use card_payment_not_recognised; an unidentified additional fee uses extra_charge_on_statement.

**Operational exceptions and status checks:**

- Two SETTLED debits for one underlying purchase can be a duplicate; one PENDING hold and one SETTLED debit are not two settled debits. Two intentional orders, split shipment captures totalling the approved principal, and recurring payments on separate dates are not assumed to be duplicates.
- Provide both references, dates, amounts and the one-order receipt. Intake within 60 calendar days of settlement is SGD 0; internal duplicate posting review takes 5 business days and approved correction 2 business days. If separate merchant submissions need a dispute, target 30 calendar days after complete evidence. Deduct any merchant refund already received from the outstanding claim.

### reverted_card_payment? — Explain a purchase authorisation or settled card purchase marked reversed

**Intent definition:** Explain a purchase authorisation or settled card purchase marked reversed.

**Processing, conditions, fees and limits:**

- A reversed normal authorisation releases its reserved balance within the original 7-calendar-day authorisation window; labelled supported deposits can remain within their 30-calendar-day window.
- For an already settled purchase, NovaBank posts an accepted reversal credit within 2 business days after receiving the merchant/network reversal instruction. This is not the same start event as a customer's cancellation request.
- The merchant may later submit a valid settlement against an earlier authorisation. A temporary release must not be represented as cancellation of the customer's merchant obligation.
- If the release/credit is missing beyond the applicable window, provide the original reference and reversal timestamp; staff acknowledge within 1 business day and trace within 2 business days. NovaBank charges SGD 0 for reversal processing.

**Verification and required evidence:** Authenticate before accessing purchase records. Provide transaction references, merchant descriptor, settlement status/date, amount/currency and masked purchase receipt; duplicates require both references, and rate cases require the original-currency receipt. No fresh ID is required unless account verification needs updating.

**Fee and limit reference:** Enquiry and dispute intake/review cost SGD 0. Ordinary purchase fee is SGD 0; bank conversion, if performed, is 0.50% with minimum 0.50 equivalent. General purchase caps are 5,000 equivalent each and 10,000 daily; disposable purchases are capped at 500. One coordinated active case per underlying purchase avoids duplicate corrections.

**Intent boundary and unsupported requests:** A reversal is not a guaranteed final refund or permission to spend twice. request_refund concerns a requested refund; Refund_not_showing_up concerns an issued merchant refund rather than an authorisation reversal.

**Operational exceptions and status checks:**

- An authorisation release removes a hold under its original 7-calendar-day or eligible 30-calendar-day deadline; it is not a merchant-issued refund. A settled network reversal credits within 2 business days after the accepted reversal instruction. Use the reversal reference, not an email promising cancellation, as evidence of that start event.
- A later valid settlement can still be investigated after a hold release; do not promise that a released authorisation makes collection impossible. Trace the original and later references at SGD 0, applying the 60-calendar-day settled-dispute intake and the relevant 5-business-day posting or 30-calendar-day merchant review. Do not pay both a reversal and a refund for the same principal.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Investigate the exchange rate applied to a settled debit-card purchase. | `card_payment_wrong_exchange_rate` |
| Explain an additional settled debit-card statement amount that is not yet identified as a fee or duplicate. | `extra_charge_on_statement` |
| Explain or challenge an explicitly identified NovaBank fee on a debit-card purchase. | `card_payment_fee_charged` |
| Explain a merchant card authorisation not yet submitted as a settled purchase. | `pending_card_payment` |
| Explain an actual card-purchase authorisation decline. | `declined_card_payment` |
| Investigate two settled debit-card purchase entries alleged to represent one purchase. | `transaction_charged_twice` |
| Explain a purchase authorisation or settled card purchase marked reversed. | `reverted_card_payment?` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| extra_charge_on_statement / card_payment_fee_charged | An unidentified extra settled amount uses extra_charge_on_statement; an explicitly identified NovaBank fee uses card_payment_fee_charged. |
| transaction_charged_twice / pending_card_payment | Two settled entries for one purchase may be a duplicate; one hold and one settlement are not two settled charges. |
| declined_card_payment / pending_card_payment | Declined is refused authorisation; pending is an approved authorisation awaiting settlement or release. |
| reverted_card_payment? / refunds | A release/reversal uses the reversal instruction or original hold clock; a merchant-issued refund uses the issuance clock in refunds. |
| card_payment_wrong_exchange_rate / card_payment_fee_charged | Challenge the conversion rate under the rate intent; challenge the separately posted conversion fee under the fee intent. If both are disputed, retrieve both and open one coordinated case. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not guarantee merchant acceptance, force approval, treat a pending hold as a settled duplicate, provide provisional refunds automatically, reimburse valid disclosed charges without grounds, refund merchant conversion automatically, or bypass security. Disposable cards cannot support deposits, recurring payments or preauthorisations.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
