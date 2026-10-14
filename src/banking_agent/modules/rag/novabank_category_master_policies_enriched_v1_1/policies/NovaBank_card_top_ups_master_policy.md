---
policy_id: DOC-CAT-CARDTOPUP-001
business_category: card_top_ups
included_intents:
  - automatic_top_up
  - pending_top_up
  - top_up_limits
  - supported_cards_and_currencies
  - top_up_reverted
  - topping_up_by_card
  - verify_top_up
  - top_up_failed
  - top_up_by_card_charge
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
  - REF-09
  - REF-10
  - REF-11
---

## NovaBank External Debit Card Funding Master Policy

### Purpose and Category Scope

Manual or opt-in automatic funding of the NovaBank SGD balance using a same-owner external Singapore-issued Visa or Mastercard debit card. A NovaBank-issued card cannot be used to circularly fund its own account.

### Common Fees, Limits and Service Conditions

Top-ups are SGD-only: minimum 20 and maximum 2,000 each, maximum 5,000 per Singapore calendar day, and maximum 20,000 per calendar month. NovaBank top-up fee is SGD 0. Manual and automatic attempts share these counters. Pending authorised attempts reserve capacity; failed uncredited attempts release it; reversals of completed credits do not restore used capacity.

### Pending Top-Up Start Event

For every manual or automatic card top-up, the 72-hour pending/finalisation clock starts at the recorded issuer-authorisation timestamp, not request initiation or NovaBank acceptance. Ownership review does not restart this clock. The separate release-instruction clock starts at final FAILED status; the issuer release window starts when NovaBank sends that instruction.

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

### Issuer, NovaBank and Funding Counter Reconciliation

The external issuer controls its authorisation/release record; NovaBank controls the accepted attempt and credited ledger. A pending issuer debit is not proof of a successful NovaBank credit. Compare references rather than dates alone. Once a funding attempt is authorised, support cannot cancel it. Manual and automated attempts share calendar counters; successful funding reversals do not erase historical usage. An issuer-disputed funding amount can be restricted pending its case outcome, which is separate from routine technical reversal timing. No advance balance or external-fee waiver is promised.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### automatic_top_up — Configure consented automatic SGD funding from an eligible external debit card

**Intent definition:** Configure consented automatic SGD funding from an eligible external debit card.

**Processing, conditions, fees and limits:**

- Automatic top-up is opt-in: when available SGD balance falls below SGD 100, NovaBank attempts a SGD 200 top-up from the customer's saved eligible Singapore-issued debit card.
- At most 1 automatic attempt is made per Singapore calendar day. It counts toward the shared card-top-up limits of SGD 5,000 daily and SGD 20,000 per calendar month; all manual and automatic top-ups use the same counters.
- Setup requires a verified account, confirmed ownership of the funding card and a secure issuer authentication flow. The NovaBank fee is SGD 0; an issuer may impose its own charge.
- Enable or disable in Add money > Automatic top-up; the setting changes within 60 seconds. A failed automatic attempt is not retried that day. A normally successful top-up posts within 60 seconds; pending attempts follow the 72-hour NovaBank finalisation deadline.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Automatic top-up from credit, prepaid, virtual, third-party or non-Singapore-issued cards is rejected. Automatic consent authorises this funding feature only and must not be treated as marketing or product-recommendation consent.

**Operational exceptions and status checks:**

- The customer must consent in the secure app to a same-owner eligible funding card, a trigger below SGD 100 and a fixed SGD 200 amount, at SGD 0 fee. One automated attempt per Singapore calendar day shares manual daily/month counters. Do not queue additional automated attempts while the original is pending.
- Enabling or disabling the feature takes up to 60 seconds at SGD 0. Disabling stops future triggers but cannot cancel an already authorised attempt. A 24-hour phone-change restriction, expiry, issuer authentication challenge or insufficient limit capacity prevents the trigger; no substitute card may be selected without new customer consent.

### pending_top_up — Explain a card-funded top-up authorisation awaiting confirmation or release

**Intent definition:** Explain a card-funded top-up authorisation awaiting confirmation or release.

**Processing, conditions, fees and limits:**

- Eligible SGD card top-ups normally credit within 60 seconds. An issuer-authorised but unresolved attempt can remain pending for up to 72 hours from authorisation.
- Record the top-up reference, initiation time, SGD amount and funding card's last four digits. Do not initiate a duplicate while the first attempt is pending.
- At 72 hours, an uncompleted pending top-up is released or marked failed by NovaBank. After a FAILED outcome, NovaBank sends the release instruction within 1 business day; the issuing bank may take up to 5 business days from that instruction to reflect release of its own hold.
- If pending status persists beyond 72 hours, staff acknowledge within 1 business day and review within 2 business days. NovaBank's top-up fee is SGD 0; eligible attempts are SGD 20-2,000 each, within SGD 5,000 daily and SGD 20,000 monthly limits.
- The 72-hour deadline is for NovaBank finalisation, not issuer statement credit. If the final status is FAILED, send the release instruction within 1 business day of that final status; the issuer then has up to 5 business days from the instruction to display release. A reference marked released at expiry may have an earlier instruction timestamp.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Immediate guaranteed release of an external issuer's hold is unsupported. A completed reversal uses top_up_reverted; a declined or failed initiation uses top_up_failed.

**Operational exceptions and status checks:**

- Compare the NovaBank attempt reference with the issuer authorisation, amount and currency; statement booking dates can differ. An external debit or hold alone does not prove a NovaBank credit. No duplicate retry or cancellation is offered for a pending authorised attempt.
- Normal accepted credit is within 60 seconds; pending may last at most 72 hours from issuer authorisation, not NovaBank acceptance or request initiation. If it ends FAILED, NovaBank sends a release instruction within 1 business day of that final status; the external issuer release target is 5 business days from that instruction, not from the attempt. Escalate status overdue beyond 72 hours at SGD 0 for a 2-business-day technical review.

### top_up_limits — State the shared limits for manual and automatic debit-card funding

**Intent definition:** State the shared limits for manual and automatic debit-card funding.

**Processing, conditions, fees and limits:**

- Each card top-up must be at least SGD 20 and no more than SGD 2,000. Aggregate manual and automatic card top-ups cannot exceed SGD 5,000 per Singapore calendar day or SGD 20,000 per calendar month.
- The daily counter resets at 00:00 Singapore time; the monthly counter resets at 00:00 on the first day of the next calendar month. Pending authorised top-ups reserve limit capacity until released or failed; completed reversals do not restore already used daily/monthly capacity.
- Automatic top-up attempts SGD 200 when available SGD balance is below SGD 100, at most once per calendar day. It uses the same limits and requires prior feature-specific consent.
- NovaBank's card-top-up fee is SGD 0. A limit rejection does not create a new charge; staff explain a counter discrepancy within 2 business days after receiving the top-up references.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Splitting transactions to bypass limits, increasing these limits through support chat, and treating incoming bank transfers as card top-ups are unsupported. Disposable-card merchant limits are unrelated to funding limits.

**Operational exceptions and status checks:**

- Manual and automatic funding, regardless of eligible funding card count, share SGD 20 minimum, 2,000 per attempt, 5,000 per Singapore calendar day and 20,000 per calendar month. NovaBank does not import another bank's rolling seven-day, new-user or adaptive numeric caps.
- Accepted pending principal reserves capacity in its acceptance period. Failed uncredited attempts release reservations only if that period is still current; reversing a completed credit does not erase historical usage. Public limit enquiries are immediate at SGD 0; bank-transfer funding is a separate counter and may still trigger source-of-funds review.

### supported_cards_and_currencies — Identify eligible external funding cards and currency for NovaBank card top-ups

**Intent definition:** Identify eligible external funding cards and currency for NovaBank card top-ups.

**Processing, conditions, fees and limits:**

- NovaBank accepts only Singapore-issued Visa or Mastercard debit cards in the verified customer's own name for SGD top-ups. The secure form verifies the cardholder and invokes issuer authentication where requested.
- Credit cards, prepaid cards, virtual/disposable cards, corporate cards, third-party cards and cards issued outside Singapore are rejected before a new top-up is submitted.
- Funding is SGD only, with limits of SGD 20-2,000 per transaction, SGD 5,000 daily and SGD 20,000 monthly. NovaBank's top-up fee is SGD 0; the issuer's own fees are outside NovaBank's control.
- An accepted top-up normally posts within 60 seconds. Card eligibility errors are reviewed within 2 business days using the issuer name, card type and last four digits; never submit full card credentials in support chat.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Holding USD, EUR, GBP or AUD does not permit card funding in those currencies. This policy is external-funding eligibility, not NovaBank debit-card merchant acceptance or the list of account currencies.

**Operational exceptions and status checks:**

- Accept only same-owner Singapore-issued Visa or Mastercard debit cards in SGD; reject credit, prepaid, corporate, virtual, third-party and non-Singapore-issued cards. NovaBank-issued cards cannot circularly fund the same account. Wallet-token top-up is not a supported funding method.
- Public compatibility checking is immediate at SGD 0. If secure issuer/card-type metadata is inconsistent, staff review masked last four digits and an ownership statement issued within 90 calendar days within 2 business days. Do not infer ownership from possession of a card or disclose a full card number in support chat.

### top_up_reverted — Explain a card-funded top-up that was reversed after initiation or credit

**Intent definition:** Explain a card-funded top-up that was reversed after initiation or credit.

**Processing, conditions, fees and limits:**

- A reversed top-up is marked REVERTED, and any previously credited SGD amount is debited back from the NovaBank balance. NovaBank's original top-up fee is SGD 0.
- The refund or authorisation-release instruction is sent to the original funding card within 1 business day after reversal. The issuing bank can take up to 5 business days after that instruction to display it.
- If no issuer credit or release is visible after those 5 business days, provide the top-up reference and a masked issuer statement. Staff acknowledge within 1 business day and trace within 2 business days.
- Reverted completed top-ups do not restore daily/monthly used top-up capacity. A reversal that creates an amount owed triggers staff review; NovaBank does not promise automatic debt forgiveness or permit new spending against missing funds.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Routing a reversal to a different card or a third-party account is rejected. pending_top_up has not yet reached a final outcome; top_up_failed concerns an attempt that did not complete successfully.

**Operational exceptions and status checks:**

- Distinguish an uncompleted technical attempt returned to the issuer from a previously credited amount later reversed. Retain both credit and reversal references. A reversal of completed funding does not reset the original daily/monthly usage or itself certify that the external issuer has restored funds.
- NovaBank sends a routine reversal instruction within 1 business day; issuer return target is 5 business days after that instruction, with NovaBank fee SGD 0. An issuer-disputed top-up is separately investigated: acknowledge within 1 business day and provide an initial update within 5 business days of complete evidence. No external dispute outcome or final deadline is guaranteed; a funding restriction cannot be bypassed.

### topping_up_by_card — Fund the NovaBank SGD balance using an eligible external debit card

**Intent definition:** Fund the NovaBank SGD balance using an eligible external debit card.

**Processing, conditions, fees and limits:**

- Use Add money > Debit card and the secure payment form. Only a Singapore-issued Visa or Mastercard debit card in the verified customer's own name is accepted; approve the issuer authentication prompt where required.
- Top-ups must be SGD 20-2,000 each, with shared limits of SGD 5,000 per Singapore calendar day and SGD 20,000 per calendar month including automatic top-ups. NovaBank's fee is SGD 0.
- Successful top-ups normally credit within 60 seconds. A pending authorisation may remain for up to 72 hours; do not retry a duplicate during that period.
- Save the top-up reference and funding card's last four digits. If credited status and balance disagree after 5 minutes, staff acknowledge within 1 business day and review within 2 business days.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Credit, prepaid, virtual, corporate, third-party and non-Singapore-issued funding cards, non-SGD card funding and funding through chatbot credentials are rejected. Bank-transfer funding uses transfer_into_account.

**Operational exceptions and status checks:**

- Confirm the eligible card, SGD amount, disclosed zero NovaBank fee and issuer authentication in the secure payment form. A customer-abandoned challenge is not successful funding. Never request OTP, CVV or full credentials in chat, and never convert a manual instruction into automatic-top-up consent.
- A successfully accepted top-up normally credits within 60 seconds and uses the existing SGD 20–2,000 each, 5,000 daily and 20,000 monthly limits. If a confirmation screen times out, inspect the original reference before another attempt. Once authorised, it cannot be cancelled by support; any later outgoing domestic transfer follows its own controls.

### verify_top_up — Verify ownership of an external debit card used for NovaBank funding

**Intent definition:** Verify ownership of an external debit card used for NovaBank funding.

**Processing, conditions, fees and limits:**

- Eligible funding cards are Singapore-issued Visa or Mastercard debit cards held in the verified customer's own name. Secure issuer authentication and matching cardholder details are required where prompted.
- An ownership-review request may require a masked issuer statement issued within 90 calendar days, showing customer name and last four card digits. Upload through the secure app; never send full card numbers, CVVs or codes in chat.
- Staff assess complete ownership evidence within 2 business days at SGD 0. Ownership approval does not raise the SGD 20-2,000 transaction, SGD 5,000 daily or SGD 20,000 monthly limits.
- A pending authorisation still follows the 72-hour pending-top-up window. Review of card ownership does not guarantee that an issuer will authorise a payment or that source-of-funds checks are complete.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Third-party ownership permission, credit/prepaid/virtual funding cards and waiver of secure verification are rejected. verify_my_identity verifies the customer; verify_source_of_funds verifies the origin of money.

**Operational exceptions and status checks:**

- Card-ownership evidence must match the NovaBank legal account holder and the funding card's last four digits. Upload an issuer statement issued within 90 calendar days in the secure app; show name, issuer, issue date and masked card identifier, while hiding unrelated transactions.
- Ownership review is SGD 0 within 2 business days after complete evidence. A successful match neither guarantees issuer approval nor satisfies a separate source-of-funds request. A third-party owner, unsupported card type or altered statement is rejected; do not accept a family member's consent as ownership.

### top_up_failed — Handle a debit-card top-up marked failed or rejected before successful completion

**Intent definition:** Handle a debit-card top-up marked failed or rejected before successful completion.

**Processing, conditions, fees and limits:**

- Check eligible funding-card type, same-name ownership, sufficient issuer balance, secure issuer authentication and shared SGD 20-2,000 per-attempt, SGD 5,000 daily and SGD 20,000 monthly limits.
- A failed initiation credits SGD 0 to NovaBank and has a NovaBank top-up fee of SGD 0. If an issuer created a hold, NovaBank sends release within 1 business day of final failure; the issuer may take up to 5 business days to display it.
- Do not retry while the first attempt is still PENDING. An uncompleted pending authorisation must be released or marked failed by 72 hours; after final failure NovaBank sends release within 1 business day, and subsequent issuer release can take up to 5 business days from that instruction.
- For a failed attempt with an issuer debit still present beyond the applicable release window, submit the reference and masked issuer evidence; staff acknowledge within 1 business day and trace within 2 business days.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Guaranteeing issuer approval, bypassing limits and treating a failed top-up as a completed NovaBank deposit are unsupported. top_up_reverted concerns a reversal after initiation or credit; pending_top_up is unresolved.

**Operational exceptions and status checks:**

- Classify failed issuer authentication, issuer refusal, insufficient external funds, NovaBank eligibility restriction and technical failure by the final reference status. A bank statement showing two lines may contain one authorisation and one settlement; compare both issuer references with actual NovaBank credited attempts before claiming duplication.
- A final FAILED attempt costs SGD 0 and creates no successful credit. If funds were authorised, NovaBank issues release within 1 business day of FAILED; issuer release target is 5 business days after that instruction. Retry only when final status and reservation handling are confirmed and the cause is corrected; an unknown or pending status is not a failed result.

### top_up_by_card_charge — Explain NovaBank and external issuer charges for debit-card funding

**Intent definition:** Explain NovaBank and external issuer charges for debit-card funding.

**Processing, conditions, fees and limits:**

- NovaBank charges SGD 0 for eligible manual and automatic SGD debit-card top-ups. Eligible cards are Singapore-issued Visa or Mastercard debit cards in the verified customer's own name.
- A funding-card issuer may independently charge a fee; NovaBank cannot quote that issuer's tariff or guarantee reimbursement. An issuer fee is not evidence that NovaBank charged for funding.
- Top-up limits are SGD 20-2,000 each, SGD 5,000 per calendar day and SGD 20,000 per calendar month. A successful top-up normally credits within 60 seconds; pending attempts use the 72-hour window.
- Submit an alleged NovaBank top-up-fee error within 60 calendar days of posting with references and masked evidence. Staff review within 5 business days after complete evidence and credit an approved error within 2 business days.

**Verification and required evidence:** Authenticate in the app; match the external debit-card owner to the verified customer and complete issuer authentication in the secure payment form when prompted. Record the top-up reference, amount, timestamp and last 4 card digits. Ownership review may require a masked issuer statement issued within 90 calendar days showing name and last 4 digits.

**Fee and limit reference:** NovaBank funding and related enquiry/review fees are SGD 0. Limits are SGD 20-2,000 per attempt, 5,000 daily and 20,000 per calendar month; external issuer fees are not NovaBank fees. Do not open duplicate traces for the same reference.

**Intent boundary and unsupported requests:** Credit-card cash-advance fees, non-SGD card top-ups, guaranteed issuer fee refunds and using another person's card are unsupported. top_up_by_bank_transfer_charge concerns incoming bank funding.

**Operational exceptions and status checks:**

- NovaBank eligible manual and automatic card funding costs SGD 0. An external issuer may post its own fee; retain the issuer statement and masked funding reference and direct an issuer-charge enquiry to that issuer without quoting a waiver or fixed issuer amount.
- If a NovaBank ledger line is labelled as a funding fee, submit its reference within 60 calendar days of posting for an SGD 0 review within 5 business days. An approved correction credits within 2 business days. Do not import premium-plan, foreign-issued-card or commercial-card fees into this zero-fee eligible product.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Configure consented automatic SGD funding from an eligible external debit card. | `automatic_top_up` |
| Explain a card-funded top-up authorisation awaiting confirmation or release. | `pending_top_up` |
| State the shared limits for manual and automatic debit-card funding. | `top_up_limits` |
| Identify eligible external funding cards and currency for NovaBank card top-ups. | `supported_cards_and_currencies` |
| Explain a card-funded top-up that was reversed after initiation or credit. | `top_up_reverted` |
| Fund the NovaBank SGD balance using an eligible external debit card. | `topping_up_by_card` |
| Verify ownership of an external debit card used for NovaBank funding. | `verify_top_up` |
| Handle a debit-card top-up marked failed or rejected before successful completion. | `top_up_failed` |
| Explain NovaBank and external issuer charges for debit-card funding. | `top_up_by_card_charge` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| topping_up_by_card / automatic_top_up | A customer-confirmed individual payment is manual; a prior-consented balance trigger is automatic. |
| pending_top_up / top_up_failed / top_up_reverted | Pending has no final outcome; failed never completed a credit; reverted unwinds an initiated/credited attempt and may remove an earlier credit. |
| supported_cards_and_currencies / top_up_limits | Eligible card type, owner, issuer location and currency are support questions; transaction and aggregate counters are limits. |
| verify_top_up / identity and funding origin | Funding-card ownership is not onboarding identity approval or proof of the economic origin of funds. |
| top_up_by_card_charge / bank-transfer charges | External card funding and electronic bank-transfer funding are different channels and use separate policies. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not accept credit, prepaid, virtual, disposable, corporate, third-party or non-Singapore-issued funding cards, non-SGD funding, insecure collection of card credentials, duplicate pending retries, fee guarantees for external issuers, or limit evasion. Bank-transfer funding has separate rules.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
