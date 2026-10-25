---
policy_id: DOC-CAT-CASHCHEQUE-001
business_category: cash_and_cheque_deposits
included_intents:
  - balance_not_updated_after_cheque_or_cash_deposit
  - top_up_by_cash_or_cheque
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
  - REF-20
  - REF-21
---

## NovaBank Cash and Cheque Funding Service Boundary Master Policy

### Purpose and Category Scope

Requests to fund by physical cash or cheque and claims of missing cash/cheque deposit proceeds. Both services are deliberately unsupported; a BANKING77 label does not establish product availability.

### Common Fees, Limits and Service Conditions

The accepted cash-deposit limit is SGD 0 and the accepted cheque-deposit limit is SGD 0. There are 0 NovaBank cash-deposit counters, deposit ATMs and authorised cash-collection agents. Unsupported deposit submission is rejected immediately. No deposit fee is collected (SGD 0) and no clearing or crediting SLA exists. Routine clarification is free and answered within 2 business days.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Accepting Institution and Subsequent Electronic Proceeds

A real bank accepting cash or a cheque owns its receipt, reconciliation and clearing process. NovaBank accepts neither instrument. An electronic domestic SGD transfer of those proceeds is a separate event governed by bank_transfers, and a deposit receipt alone is not a transfer receipt. NovaBank cannot guarantee another institution's acceptance, clearing date or refund. An agent claiming to collect deposits for NovaBank contradicts the authorised service boundary and triggers urgent security intake, without waiting for the routine clarification target.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### balance_not_updated_after_cheque_or_cash_deposit — Respond to a claimed cash or cheque deposit where NovaBank offers no such deposit service

**Intent definition:** Respond to a claimed cash or cheque deposit where NovaBank offers no such deposit service.

**Processing, conditions, fees and limits:**

- NovaBank does not accept cash deposits or cheque deposits. The accepted cash/cheque deposit limit is SGD 0, and no cash/cheque clearing or crediting window exists.
- Do not promise to credit a cash or cheque receipt from a third-party bank, merchant, ATM or postal service. Identify the institution named on the receipt and ask the customer to contact that institution.
- If another bank converted the proceeds into a domestic SGD transfer to NovaBank, trace the bank-transfer reference instead: normal receipt within 60 seconds, trace after 24 hours, staff trace review within 2 business days.
- NovaBank charges SGD 0 to clarify this unsupported-service report. A receipt naming NovaBank or a purported NovaBank cash-deposit agent is immediately escalated as suspected fraud; routine clarification otherwise receives a response within 2 business days.
- Capture the institution named on the receipt, claimed deposit amount, date/time and reference. If the actual event is a domestic electronic transfer, carry over only its bank-transfer reference; do not relabel a third-party cash receipt as proof of NovaBank credit.

**Verification and required evidence:** General unsupported-method guidance requires no authentication. Authenticate before examining NovaBank records. For an alleged deposit, obtain a masked receipt identifying the institution, amount, date and reference. No deposit-verification document can make the unsupported method valid; retain only synthetic evidence in the academic system.

**Fee and limit reference:** Accepted cash and cheque limits are both SGD 0. No unsupported deposit fee is collected: SGD 0. Clarification and security referral cost SGD 0. There is no clearing SLA because no cash/cheque deposit is accepted.

**Intent boundary and unsupported requests:** Cash collection, cheque clearing, branch deposits, agent deposits and guaranteed credit of third-party receipts are explicitly unsupported. A genuine incoming electronic transfer uses balance_not_updated_after_bank_transfer.

**Operational exceptions and status checks:**

- Ask which institution actually accepted the cash or cheque and whether a separate domestic SGD electronic transfer was sent to NovaBank. A third-party clearing receipt does not demonstrate receipt by NovaBank. NovaBank accepts principal SGD 0 for both services and has no deposit clearing clock.
- Routine clarification is SGD 0 within 2 business days. If a supported electronic transfer exists, switch to balance_not_updated_after_bank_transfer: normal receipt 60 seconds and trace after 24 hours. An alleged NovaBank collection-agent receipt triggers immediate security escalation; do not promise a fabricated cash/cheque credit or advise a second deposit.

### top_up_by_cash_or_cheque — State that NovaBank does not accept physical cash or cheque funding

**Intent definition:** State that NovaBank does not accept physical cash or cheque funding.

**Processing, conditions, fees and limits:**

- Cash deposits and cheque deposits are not supported. Accepted deposit limit is SGD 0; no deposit fee, clearing deadline, branch counter or deposit-agent service exists for these methods.
- Do not mail cash or cheques to NovaBank or hand funds to someone claiming to be a NovaBank deposit agent. An alleged deposit agent or NovaBank-branded receipt is a suspected-fraud escalation to 24/7 security staff.
- A customer may independently deposit at a different bank and then send a domestic SGD electronic transfer to NovaBank. NovaBank receives that transfer at SGD 0, normally within 60 seconds after sender acceptance; the other bank's fees and clearing times are not NovaBank terms.
- Routine method enquiries receive staff clarification within 2 business days. An already initiated domestic transfer missing after 24 hours receives a trace update within 2 business days after complete evidence.
- Reject a cash/cheque deposit request immediately at SGD 0; accepted principal is SGD 0 and there are 0 permitted deposit agents. The 2-business-day clarification deadline is a support response, not a cheque-clearing promise.

**Verification and required evidence:** General unsupported-method guidance requires no authentication. Authenticate before examining NovaBank records. For an alleged deposit, obtain a masked receipt identifying the institution, amount, date and reference. No deposit-verification document can make the unsupported method valid; retain only synthetic evidence in the academic system.

**Fee and limit reference:** Accepted cash and cheque limits are both SGD 0. No unsupported deposit fee is collected: SGD 0. Clarification and security referral cost SGD 0. There is no clearing SLA because no cash/cheque deposit is accepted.

**Intent boundary and unsupported requests:** Cash collection, cheque scanning for deposit, ATM cash deposits, branch deposits and guaranteed credit from a third-party deposit receipt are explicitly rejected/unsupported.

**Operational exceptions and status checks:**

- Reject a physical cash or cheque funding request immediately, at SGD 0 fee, because accepted cash and cheque limits are both SGD 0. There are zero authorised NovaBank collection agents, deposit ATMs, counters, mail-in channels or cheque-image deposit services.
- The payer may independently use another institution's permitted services and then send a supported domestic SGD bank transfer, but NovaBank cannot quote that institution's fees or clearing date. Such electronic receipt normally takes 60 seconds after sender acceptance, with NovaBank fee SGD 0. Do not instruct customers to mail cash, endorse cheques to an agent or provide credentials to a collector.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Respond to a claimed cash or cheque deposit where NovaBank offers no such deposit service. | `balance_not_updated_after_cheque_or_cash_deposit` |
| State that NovaBank does not accept physical cash or cheque funding. | `top_up_by_cash_or_cheque` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| top_up_by_cash_or_cheque / balance_not_updated_after_cheque_or_cash_deposit | Prospective method questions ask whether cash/cheque funding is available; an alleged completed deposit requires receipt identification and possible fraud referral. |
| cash/cheque receipt / bank transfer | A deposit at another institution is not a NovaBank deposit. If that institution subsequently sends SGD electronically, trace the electronic transfer under bank_transfers. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not collect cash, accept or scan cheques for deposit, provide branch or agent deposit services, quote invented clearing dates, credit third-party deposit receipts, or instruct customers to send cash by mail. NovaBank-branded deposit-agent claims trigger immediate security escalation.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
