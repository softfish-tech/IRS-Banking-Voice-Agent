---
policy_id: DOC-CAT-TRANSFER-001
business_category: bank_transfers
included_intents:
  - top_up_by_bank_transfer_charge
  - cancel_transfer
  - transfer_not_received_by_recipient
  - declined_transfer
  - pending_transfer
  - transfer_timing
  - beneficiary_not_allowed
  - transfer_fee_charged
  - receiving_money
  - failed_transfer
  - transfer_into_account
  - balance_not_updated_after_bank_transfer
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
  - REF-16
  - REF-17
---

## NovaBank Domestic SGD Electronic Transfers Master Policy

### Purpose and Category Scope

Domestic SGD incoming funding and outgoing transfers to supported Singapore bank accounts. Incoming third-party transfers are permitted subject to identity, funding-source and security controls; third-party external card top-ups remain prohibited.

### Common Fees, Limits and Service Conditions

Outgoing limits are SGD 10,000 per transfer and 20,000 per Singapore calendar day. The new-beneficiary waiting period is 24 hours. NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Normal receipt/completion target is 60 seconds after sending-bank acceptance; trace an unresolved or missing transfer after 24 hours. Outgoing limits are not incoming limits, and bank transfers do not consume card-top-up counters.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Funding-Origin Review Boundary

An incoming domestic transfer of SGD 10,000 or more, gross credited incoming electronic funding of SGD 20,000 over a rolling 30-calendar-day window, or a recorded risk concern triggers synthetic source-of-funds review. Aggregate credited bank transfers and external-card top-ups; exclude failed/uncredited attempts, internal exchanges, merchant refunds and approved error corrections. A later funding reversal does not erase its historical contribution. Complete evidence is acknowledged within 1 business day and reviewed within 5 business days, at SGD 0. These thresholds are review triggers, not incoming payment caps or statutory thresholds; review may restrict availability even when a payment has posted. Funding-card ownership verification alone does not satisfy this review.

### Counter and Available-Balance Interpretation

Purchase, ATM, card-top-up and outgoing bank-transfer limits are separate channel counters and apply at account level, not separately to each physical card, virtual card, wallet device or funding card. Available balance excludes authorisation holds and funds under an applicable review restriction. Principal counts toward transaction value limits; available balance must additionally cover disclosed fees. An approved attempt is assigned to its acceptance date for daily/monthly counting; a release can restore reserved capacity only in the still-current counting period. A refund or reversal of a completed transaction does not reset historical used limits or create new capacity in the earlier period. Where a product-specific limit is lower, the stricter limit applies.

### Final Status, Recall and Incoming Availability

The definitive transfer reference distinguishes PENDING, COMPLETED, DECLINED, FAILED and CANCELLED. A network timeout is not a final result. Cancel applies only to an eligible pending order; recall asks for cooperation after completion and cannot guarantee recovery. Sender acceptance starts ordinary receipt timing; actual receipt of returned money starts the one-business-day return posting target. Incoming funds can be credited but unavailable under an authorised review. Correct receiving-bank selection and account identifier matter more than a saved recipient nickname. Staff disclose no beneficiary private data to an unverified caller.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### top_up_by_bank_transfer_charge — Explain NovaBank fees for funding the SGD account by a domestic bank transfer

**Intent definition:** Explain NovaBank fees for funding the SGD account by a domestic bank transfer.

**Processing, conditions, fees and limits:**

- Incoming domestic SGD bank transfers have a NovaBank receiving fee of SGD 0. They are bank transfers, not debit-card top-ups, and do not consume the SGD 5,000 card-top-up daily limit.
- The sending bank may impose its own fee. NovaBank cannot quote or refund another bank's fee; ask the sender for the transfer receipt and fee breakdown.
- Supported domestic transfers normally arrive within 60 seconds after sender acceptance. A pending transfer is traced after 24 hours; trace review takes up to 2 business days after complete evidence.
- If the NovaBank statement itself shows a receiving fee, submit its reference within 60 calendar days. Staff review within 5 business days and credit a confirmed erroneous bank fee within 2 business days after approval.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** International transfers, cash/cheque deposits and external-bank fee reimbursement are unsupported. transfer_fee_charged concerns outgoing transfer charges; top_up_by_card_charge concerns card funding.

**Operational exceptions and status checks:**

- Domestic SGD incoming bank funding has NovaBank fee SGD 0. A sending bank's own charge is not reimbursed or quoted as a NovaBank charge. No international transfer, foreign-currency bank receipt or correspondent-fee schedule is introduced.
- If a NovaBank incoming transfer fee appears, obtain the ledger/transfer references and sender receipt within 60 calendar days of fee posting. Review costs SGD 0 and takes 5 business days from complete evidence; approved correction credits within 2 business days. If the principal is missing, use balance_not_updated_after_bank_transfer rather than a fee correction.

### cancel_transfer — Request cancellation of a domestic SGD transfer that has not completed

**Intent definition:** Request cancellation of a domestic SGD transfer that has not completed.

**Processing, conditions, fees and limits:**

- Cancellation is available only while the transfer is PENDING and its details screen shows Cancel. Verify the transfer reference, beneficiary and amount, then confirm in the authenticated app.
- A successful cancellation is displayed within 60 seconds and costs SGD 0. Reserved funds are released within 1 business day. If settlement wins the race, the cancellation request fails and the transfer becomes COMPLETED.
- Completed transfers cannot be unilaterally cancelled. Staff can submit one recovery request within 30 calendar days of completion, acknowledge within 1 business day and provide an initial trace update within 2 business days.
- A recovery request depends on recipient-bank cooperation and recipient authorisation; recovery is not guaranteed. Suspected scam transfers are escalated immediately rather than processed as routine cancellation.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** Cancelling a completed transfer by chatbot instruction, guaranteeing recovery, and reversing another customer's transfer are prohibited. pending_transfer explains status; failed_transfer handles technical failure.

**Operational exceptions and status checks:**

- Cancellation is permitted only while the authoritative state is PENDING and the secure app displays Cancel. Verify transfer reference, amount and destination, then submit once. A race with completion may reject the request; a button click alone is not evidence of cancellation.
- An accepted cancellation costs SGD 0 and confirms within 60 seconds; reserved funds release within 1 business day of confirmed cancellation. A COMPLETED wrong-recipient transfer instead allows a recovery request within 30 calendar days, with acknowledgement within 1 business day and initial update within 2 business days; receiving-side cooperation and recovery are not guaranteed.

### transfer_not_received_by_recipient — Trace an outgoing transfer shown as completed by NovaBank but missing at the beneficiary bank

**Intent definition:** Trace an outgoing transfer shown as completed by NovaBank but missing at the beneficiary bank.

**Processing, conditions, fees and limits:**

- Domestic SGD transfers normally complete within 60 seconds. First verify that the NovaBank transfer is COMPLETED, not PENDING or FAILED, and compare beneficiary details against the transfer receipt.
- If the recipient has not received it after 24 hours, collect the reference, completion time, amount and masked beneficiary details. Staff acknowledge within 1 business day and provide an initial trace result within 2 business days after complete evidence.
- Trace requests cost SGD 0. If the receiving bank confirms rejection and returns funds, NovaBank credits them within 1 business day of receipt; receipt by NovaBank is the start of this credit window.
- An incorrect-beneficiary recovery can be requested within 30 calendar days of completion, but depends on receiving-bank cooperation and is not guaranteed.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** A recipient's verbal report alone cannot prove transfer loss or authorise a duplicate transfer. pending_transfer applies before completion; transfer_timing states the normal delivery window. International transfers are unsupported.

**Operational exceptions and status checks:**

- A NovaBank COMPLETED transfer missing at the beneficiary bank requires the original reference, actual completion timestamp, amount, receiving bank and masked recipient evidence. Correct spelling of a saved nickname does not establish the account number was correct. The sender, rather than an unrelated third party, submits the trace.
- Normal supported completion is within 60 seconds; if still missing after 24 hours, open one SGD 0 trace per reference. Acknowledge within 1 business day and provide an initial result within 2 business days after complete evidence. A returned payment credits within 1 business day after NovaBank actually receives the returned funds; it cannot be fabricated from a recipient statement.

### declined_transfer — Explain a domestic SGD transfer refused by a business or eligibility control

**Intent definition:** Explain a domestic SGD transfer refused by a business or eligibility control.

**Processing, conditions, fees and limits:**

- A DECLINED transfer was refused because of a control such as insufficient available SGD, an ineligible beneficiary, a security restriction or the daily limit; it is not a completed transfer.
- Outgoing limits are SGD 10,000 per transfer and SGD 20,000 per Singapore calendar day, with NovaBank fee SGD 0. A newly added beneficiary is unavailable for 24 hours after secure addition.
- Check the displayed decline reason in the authenticated app. A refused transfer creates no final beneficiary credit; any temporary reserved amount is released within 1 business day.
- Staff acknowledge a decline enquiry within 1 business day and review complete evidence within 2 business days. Suspected scams or security blocks are escalated rather than overridden.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** Overriding risk controls, transferring unsupported currencies or exceeding limits through transaction splitting are rejected. A technical outage uses failed_transfer; an unresolved submitted transfer uses pending_transfer.

**Operational exceptions and status checks:**

- DECLINED means a business, eligibility, limit or security refusal; it differs from a technical FAILED status. Check enabled destination, the 24-hour new-beneficiary wait, any phone-change restriction, available funds and outgoing SGD 10,000 each/20,000 daily limits.
- A declined transfer has NovaBank fee SGD 0 and no completed transfer principal. If a restriction is unexplained, staff review within 2 business days after masked evidence; source-of-funds evidence uses its separate 5-business-day review. Changing spelling, splitting amounts or repeatedly adding the destination cannot bypass a block.

### pending_transfer — Explain an outgoing domestic SGD transfer accepted but not yet completed or failed

**Intent definition:** Explain an outgoing domestic SGD transfer accepted but not yet completed or failed.

**Processing, conditions, fees and limits:**

- Supported domestic transfers normally complete within 60 seconds. A transfer still marked PENDING may remain under processing or review for up to 24 hours from acceptance.
- The amount is reserved while pending. Do not create a duplicate merely because the recipient has not yet received funds. If Cancel is available, a confirmed cancellation completes within 60 seconds and releases funds within 1 business day.
- After 24 hours without a final status, provide the reference, time, SGD amount and masked beneficiary. Staff acknowledge within 1 business day and provide a trace update within 2 business days after complete evidence.
- Outgoing limits are SGD 10,000 per transaction and SGD 20,000 daily; NovaBank's transfer fee is SGD 0. A security hold is reviewed by staff, never bypassed by chat.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** A pending transfer is not proof that the beneficiary has been paid, and completion at a fixed minute is not guaranteed. Completed-but-missing transfers use transfer_not_received_by_recipient; technical failures use failed_transfer.

**Operational exceptions and status checks:**

- PENDING means accepted without a final outcome, not completed or failed. A timeout after confirmation must be reconciled against the original reference; do not send a duplicate. Source-of-funds or security notices may explain why funds are unavailable.
- The ordinary target is 60 seconds at SGD 0; investigate an unresolved transfer after 24 hours, acknowledge within 1 business day and update within 2 business days after complete evidence. Only a visible eligible Cancel action permits cancellation; no automatic cancellation or duplicate reimbursement follows from a delay.

### transfer_timing — State normal delivery and exception windows for domestic SGD bank transfers

**Intent definition:** State normal delivery and exception windows for domestic SGD bank transfers.

**Processing, conditions, fees and limits:**

- NovaBank supports domestic SGD transfers only. A supported transfer normally completes within 60 seconds after acceptance; this normal target is not a guaranteed recipient-credit promise.
- Outgoing transfers still pending after 24 hours require a trace. Completed outgoing transfers not received after 24 hours also require a trace; the reference and status determine which intent applies.
- Staff acknowledge trace requests within 1 business day and provide an initial trace update within 2 business days after complete evidence. Returned incoming funds are credited within 1 business day after NovaBank receives them.
- Outgoing limits are SGD 10,000 per transaction and SGD 20,000 daily, at SGD 0 bank fee. Newly added beneficiaries have a 24-hour waiting period, and approved phone changes restrict adding beneficiaries and card top-ups for 24 hours.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** International/SWIFT transfers, foreign-currency transfers and guaranteed completion during a security review are unsupported. This policy explains timing rather than cancelling a transfer or proving recipient receipt.

**Operational exceptions and status checks:**

- Supported domestic SGD transfers normally complete within 60 seconds after sending-bank acceptance. This is a continuous-time target, not a business-day promise; a queued external bank instruction has not started the NovaBank receipt clock. New beneficiaries cannot be used until their 24-hour wait expires.
- A missing or unresolved transfer is traceable after 24 hours at SGD 0, with acknowledgement within 1 business day and initial update within 2 business days of complete evidence. Source-of-funds review takes up to 5 business days after complete evidence. Do not apply card-top-up 72-hour pending or five-business-day issuer-release clocks to bank transfers.

### beneficiary_not_allowed — Explain why a proposed domestic transfer beneficiary cannot be used

**Intent definition:** Explain why a proposed domestic transfer beneficiary cannot be used.

**Processing, conditions, fees and limits:**

- A beneficiary must be a valid supported Singapore bank account accepting SGD and must pass NovaBank's synthetic security checks. International destinations and foreign-currency payment instructions are rejected.
- A newly added beneficiary requires authenticated confirmation and a 24-hour waiting period before transfers. Following an approved phone-number change, adding beneficiaries is restricted for 24 hours.
- NovaBank charges SGD 0 to add a supported beneficiary. Correct formatting errors in the app; an alleged mistaken security rejection is reviewed within 2 business days after complete evidence.
- Accepted outgoing transfers remain limited to SGD 10,000 each and SGD 20,000 daily. Suspected scam recipients are escalated immediately; an agent must not remove the block merely to complete a payment.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** Using another beneficiary as a pass-through to evade a restriction, sending to unsupported countries, and overriding security screening through chat are prohibited. declined_transfer describes the resulting refused transaction.

**Operational exceptions and status checks:**

- Validate the receiving bank selection, account identifier, domestic SGD route and active/eligible destination. A bank-name mismatch, closed account or security-blocked destination is not fixed by editing the recipient nickname. New-beneficiary eligibility starts only after the 24-hour waiting period.
- A public eligibility enquiry is immediate at SGD 0; masked destination errors receive a 2-business-day staff review. Beneficiary addition remains restricted for 24 hours after an approved phone-number change. Do not expose security decision criteria, instruct evasion or create an overseas beneficiary under this domestic product.

### transfer_fee_charged — Explain a fee associated with an outgoing domestic SGD bank transfer

**Intent definition:** Explain a fee associated with an outgoing domestic SGD bank transfer.

**Processing, conditions, fees and limits:**

- NovaBank's outgoing domestic SGD transfer fee is SGD 0, including cancellation and routine trace requests. The supported limits are SGD 10,000 per transfer and SGD 20,000 per calendar day.
- Inspect the transaction reference, fee descriptor and party that charged the fee. A receiving bank or other institution may levy its own charge; NovaBank cannot guarantee or reimburse that charge.
- Submit an alleged NovaBank transfer-fee error within 60 calendar days of the posting. Staff acknowledge within 1 business day and complete the internal fee review within 5 business days after complete evidence.
- A confirmed erroneous NovaBank fee is credited within 2 business days after approval. Domestic transfer timing is normally 60 seconds; a pending or missing transfer is traced after 24 hours.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** International transfer pricing, SWIFT charges and automatic reimbursement of another institution's fee are unsupported. top_up_by_bank_transfer_charge concerns incoming funding rather than outgoing transfers.

**Operational exceptions and status checks:**

- NovaBank outgoing domestic SGD transfer, cancellation and routine trace fees are all SGD 0. Distinguish a third-party bank charge, unrelated FX exchange fee and actual NovaBank transfer-fee line before reviewing it; a foreign currency balance does not create a foreign-transfer product.
- Collect transfer and fee references within 60 calendar days of fee posting. The SGD 0 internal fee review target is 5 business days after complete evidence, with approved correction within 2 business days. Recovering a fee is separate from recalling principal and never certifies that a completed payment was cancelled.

### receiving_money — Explain how a customer can receive a supported domestic SGD electronic bank transfer

**Intent definition:** Explain how a customer can receive a supported domestic SGD electronic bank transfer.

**Processing, conditions, fees and limits:**

- A verified NovaBank customer can receive domestic SGD transfers using account details displayed in the authenticated app. Incoming payments may come from the customer's own account or a third party; funding-source checks still apply.
- NovaBank charges SGD 0 to receive a supported transfer. Receipt normally appears within 60 seconds after sending-bank acceptance, unless a source-of-funds/security review restricts availability.
- Incoming bank transfers do not consume the SGD 5,000 card-top-up daily limit. A transfer of SGD 10,000 or more or aggregate incoming funding of SGD 20,000 in 30 calendar days triggers the synthetic source-of-funds review.
- If a receipt is absent after 24 hours, request the sender's reference and masked receipt; staff acknowledge within 1 business day and trace within 2 business days after complete evidence.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** International or non-SGD incoming transfers, cash/cheque deposits and disclosure of account details without secure authentication are unsupported. transfer_into_account provides the own-account funding steps; missing balances use balance_not_updated_after_bank_transfer.

**Operational exceptions and status checks:**

- Receive supported domestic SGD transfers using the authenticated account details. Third-party bank transfers are permitted, whereas third-party card top-ups are prohibited. There is no separate NovaBank numeric incoming cap; sender-bank caps and funding-origin/security controls still apply.
- Ordinary receipt is within 60 seconds after sender-bank acceptance, at SGD 0. An unexpected stranger's credit or alleged mistaken transfer must be referred to staff; do not spend it or return money to a different account supplied by a caller. Staff acknowledge within 1 business day and provide an initial review within 2 business days of complete evidence; no legal or recovery outcome is promised.

### failed_transfer — Handle a domestic SGD transfer that failed for a technical or processing reason

**Intent definition:** Handle a domestic SGD transfer that failed for a technical or processing reason.

**Processing, conditions, fees and limits:**

- A FAILED transfer means processing did not complete because of a technical or payment-processing fault. A business-rule refusal is DECLINED and uses declined_transfer.
- NovaBank charges SGD 0 for a failed transfer. Reserved funds are released within 1 business day after the FAILED status; a completed transfer must not be relabelled failed only because the recipient reports nonreceipt.
- Retry only after the final failure is visible and reserved funds are released. Supported retries have limits of SGD 10,000 per transfer and SGD 20,000 daily and may still require security checks.
- If the release is missing after 1 business day, provide the failure reference and time; staff acknowledge within 1 business day and issue an initial trace update within 2 business days after complete evidence.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** Guaranteeing retry success, treating technical failure as beneficiary misconduct and reversing a completed transfer through this policy are unsupported. pending_transfer has no final outcome yet.

**Operational exceptions and status checks:**

- FAILED is a final technical or processing failure, including confirmed invalid or closed destination returns; a business refusal stays DECLINED. A debit followed by a return is not two transfers. Confirm the final reference and validate destination details before a customer-authorised retry.
- NovaBank failure fee is SGD 0. Failed-transfer reservations release within 1 business day of the final failure; returned principal credits within 1 business day of NovaBank's actual receipt. Investigate an overdue release within 2 business days of complete evidence. A confirmation-screen error with an unknown result must not be labelled FAILED.

### transfer_into_account — Fund the customer's own NovaBank SGD account from an external domestic bank account

**Intent definition:** Fund the customer's own NovaBank SGD account from an external domestic bank account.

**Processing, conditions, fees and limits:**

- Copy the NovaBank SGD account details from the authenticated app and initiate a domestic SGD transfer at the sending bank. Verify the account number and recipient name before confirming at the sender.
- NovaBank receiving fee is SGD 0 and normal receipt is within 60 seconds after sending-bank acceptance. The sender's bank sets its own sending limit and fee; NovaBank's outgoing SGD 10,000 limit must not be misquoted as an incoming limit.
- Incoming bank funding does not use the SGD 5,000 card-top-up daily counter. Transfers of SGD 10,000 or more and rolling 30-day incoming totals of SGD 20,000 trigger NovaBank's synthetic source-of-funds review.
- If missing after 24 hours, collect the sending reference, date/time, amount and masked receipt; staff acknowledge within 1 business day and trace within 2 business days after complete evidence.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** Cash/cheque funding, international bank funding and non-SGD transfers are unsupported. receiving_money also covers third-party domestic receipts; balance_not_updated_after_bank_transfer covers an already initiated missing credit.

**Operational exceptions and status checks:**

- Use the verified NovaBank account number and supported receiving-bank details for an external domestic SGD transfer from the customer's own bank. A transfer from another person is handled under receiving_money; cash or cheque accepted by another bank is not a NovaBank cash/cheque deposit.
- NovaBank fee is SGD 0 and normal receipt is within 60 seconds after sending-bank acceptance. Preserve the sending-bank reference and check actual sending status before retrying. No separate numeric incoming cap exists, but a single incoming transfer of SGD 10,000 or qualifying rolling gross funding of SGD 20,000 triggers the source-of-funds review defined in identity_verification.

### balance_not_updated_after_bank_transfer — Trace an incoming domestic SGD bank transfer missing from the NovaBank balance

**Intent definition:** Trace an incoming domestic SGD bank transfer missing from the NovaBank balance.

**Processing, conditions, fees and limits:**

- Incoming supported transfers normally appear within 60 seconds after the sending bank accepts them. Check account details, sender status, currency and any source-of-funds/security-review notice.
- After 24 hours without credit, collect the sending-bank reference, acceptance date/time, SGD amount and masked receipt. Staff acknowledge within 1 business day and provide an initial trace update within 2 business days after complete evidence.
- NovaBank receiving fee is SGD 0. If a receiving rejection returns funds, the sender bank controls the sender's credit timing; if NovaBank receives returned funds for a customer credit, it posts within 1 business day of receipt.
- A source-of-funds review has a target decision within 5 business days after complete evidence. A transfer receipt alone does not authorise NovaBank to manually invent a balance credit.

**Verification and required evidence:** Authenticate before disclosing account or beneficiary data or submitting an action. Provide the transfer reference, accepted/completed timestamp, SGD amount, payment status and masked sender/beneficiary details; missing incoming payments also require the sender receipt. An unchanged verified customer needs no new ID, but a funding-origin hold needs its separate evidence.

**Fee and limit reference:** NovaBank incoming, outgoing, cancellation and routine trace fees are SGD 0. Outgoing caps are SGD 10,000 each and 20,000 daily; these are not incoming limits. No separate NovaBank numeric incoming cap is imposed by this policy, but sender limits and mandatory funding-origin/security reviews still apply. One active trace per reference is permitted.

**Intent boundary and unsupported requests:** Cash/cheque receipts, non-SGD or international funding, guaranteed credit before reconciliation and duplicate funding recommendations are unsupported. transfer_into_account explains initiation rather than missing credit.

**Operational exceptions and status checks:**

- Compare ledger balance with available balance and check whether the transfer is merely scheduled externally, actually accepted by the sender, received by NovaBank or restricted for review. An external screenshot, recipient nickname or deposit receipt alone does not permit manual credit.
- After 24 hours from sender acceptance without a matched credit, submit reference, timestamp/timezone, SGD amount, correct recipient details and a masked sender receipt. One free trace is allowed per reference, acknowledged within 1 business day and initially updated within 2 business days after complete evidence. A source-of-funds restriction has its own 5-business-day decision target.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Explain NovaBank fees for funding the SGD account by a domestic bank transfer. | `top_up_by_bank_transfer_charge` |
| Request cancellation of a domestic SGD transfer that has not completed. | `cancel_transfer` |
| Trace an outgoing transfer shown as completed by NovaBank but missing at the beneficiary bank. | `transfer_not_received_by_recipient` |
| Explain a domestic SGD transfer refused by a business or eligibility control. | `declined_transfer` |
| Explain an outgoing domestic SGD transfer accepted but not yet completed or failed. | `pending_transfer` |
| State normal delivery and exception windows for domestic SGD bank transfers. | `transfer_timing` |
| Explain why a proposed domestic transfer beneficiary cannot be used. | `beneficiary_not_allowed` |
| Explain a fee associated with an outgoing domestic SGD bank transfer. | `transfer_fee_charged` |
| Explain how a customer can receive a supported domestic SGD electronic bank transfer. | `receiving_money` |
| Handle a domestic SGD transfer that failed for a technical or processing reason. | `failed_transfer` |
| Fund the customer's own NovaBank SGD account from an external domestic bank account. | `transfer_into_account` |
| Trace an incoming domestic SGD bank transfer missing from the NovaBank balance. | `balance_not_updated_after_bank_transfer` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| receiving_money / transfer_into_account | receiving_money explains all permitted incoming domestic payments; transfer_into_account gives own-account funding steps. |
| transfer_timing / pending_transfer | Timing is a general delivery question; pending_transfer is a specific accepted outgoing order without a final result. |
| pending_transfer / transfer_not_received_by_recipient | Pending is not completed; completed-but-not-received requires a recipient-bank trace after 24 hours. |
| declined_transfer / failed_transfer | Business/risk controls produce DECLINED; technical or processing faults produce FAILED. |
| beneficiary_not_allowed / declined_transfer | Beneficiary eligibility explains a blocked destination; declined_transfer explains the resulting refused transfer. |
| cancel_transfer / failed_transfer | Customer cancellation is a permitted pending-state action; failure is a technical terminal result. |
| top_up_by_bank_transfer_charge / transfer_fee_charged | The first concerns incoming funding charges; the second concerns outgoing transfer charges. |
| balance_not_updated_after_bank_transfer / transfer_not_received_by_recipient | Missing NovaBank incoming credit differs from an outgoing NovaBank transfer missing at the recipient bank. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not offer SWIFT/international transfers, foreign-currency transfers, cash/cheque funding, guaranteed recovery of completed transfers, beneficiary/security-block bypass, automatic duplicate transfers, or reimbursement guarantees for another institution's fees.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
