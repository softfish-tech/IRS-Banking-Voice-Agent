---
policy_id: DOC-CAT-FX-001
business_category: currency_exchange
included_intents:
  - exchange_rate
  - fiat_currency_support
  - exchange_via_app
  - exchange_charge
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
  - REF-05
---

## NovaBank Fiat Currency Balances and Conversion Master Policy

### Purpose and Category Scope

Holding and exchanging supported fiat balances within the same NovaBank personal account. These balances are not separate foreign bank accounts or unrelated investment products.

### Common Fees, Limits and Service Conditions

Supported currencies are exactly SGD, USD, EUR, GBP and AUD. In-app conversion limits are SGD-equivalent 10 minimum, 5,000 maximum per exchange, and 10,000 aggregate per Singapore calendar day. NovaBank conversion costs 0.50% of source principal, with a minimum SGD-equivalent 0.50; quotes last 30 seconds.

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

### Conversion Owner, Rate Direction and Refund Basis

In-app quotes and recorded settlement conversions are authoritative synthetic pricing records; public market quotations are comparisons only. DCC is conversion by a merchant or ATM operator into SGD and does not attract a NovaBank FX fee. Purchases use sufficient matching supported currency, otherwise the whole purchase converts from SGD. ATM principal always debits SGD. NovaBank refunds of converted principal use the original settlement rate and create no additional conversion fee; correct original FX fees remain unless specifically corrected. Unsupported currency requests do not create a conversion route.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### exchange_rate — Explain the displayed NovaBank currency conversion quote before an exchange or debit-card purchase

**Intent definition:** Explain the displayed NovaBank currency conversion quote before an exchange or debit-card purchase.

**Processing, conditions, fees and limits:**

- The supported account currencies are SGD, USD, EUR, GBP and AUD. NovaBank quotes a synthetic reference rate updated every 60 seconds during available quoting periods; the rate is not asserted to be an actual market rate.
- An in-app conversion quote is valid for 30 seconds and displays the source amount, reference rate, destination amount and 0.50% conversion fee before confirmation. The minimum fee is SGD 0.50 or its displayed equivalent.
- For debit-card purchases in a supported currency, sufficient same-currency balance is used first. If insufficient, the full purchase is converted from SGD at the transaction's settlement quote with the same 0.50% fee and SGD 0.50 minimum.
- A pending card authorisation may use a provisional rate. The final rate and separately identified fee appear when the merchant submits settlement, normally within 7 calendar days. Provide the transaction reference and currency pair for a historical-rate enquiry; staff respond within 2 business days.
- Define rate as destination-currency units per 1 source-currency unit. Source principal excludes the separately charged conversion fee; sufficient source balance must cover both. A hypothetical quote of 1 SGD = 0.740000 USD converts SGD 100 principal into USD 74.00 with an additional SGD 0.50 fee. This is an illustrative synthetic quote, not a standing rate or a present market observation.
- Reserve sufficient SGD for a purchase requiring conversion at authorisation. Final conversion uses the recorded settlement quote; rate movement alone is not a calculation error. Do not partially combine a short foreign balance with SGD to fund one purchase.

**Verification and required evidence:** Authenticate for balance access or exchange confirmation. Record the currency pair, source principal, quote timestamp/reference and any disputed transaction receipt. No fresh identity document is required for an unchanged verified account; support must not accept a screenshot as authority to execute an exchange.

**Fee and limit reference:** Policy enquiries and calculation reviews cost SGD 0. Any actual NovaBank conversion uses 0.50%, minimum SGD-equivalent 0.50; in-app source principal is 10-5,000 equivalent per exchange and at most 10,000 equivalent daily. Purchase and ATM limits remain independently applicable.

**Intent boundary and unsupported requests:** A guaranteed future exchange rate, cryptocurrency conversion and manual overrides of a confirmed rate are unsupported. An already settled card-purchase rate dispute belongs to card_payment_wrong_exchange_rate; an ATM-rate dispute belongs to wrong_exchange_rate_for_cash_withdrawal.

**Operational exceptions and status checks:**

- The displayed rate is destination units for one source unit. For illustration only, a quote of 1 SGD = 0.75 USD makes SGD 100 principal yield USD 75 before any separately charged source-currency fee. The illustrative rate is not a live offer; retrieve the actual quote reference and timestamp.
- The reference refreshes every 60 seconds and a confirmed quote expires after 30 seconds. Obtain a fresh quote and explicit confirmation after expiry; do not substitute an inverse rate, internet estimate or purchase-day rate for the recorded settlement rate. Public rate-method enquiries are SGD 0 and immediate.

### fiat_currency_support — Identify the fiat currencies NovaBank can hold and exchange in its personal account

**Intent definition:** Identify the fiat currencies NovaBank can hold and exchange in its personal account.

**Processing, conditions, fees and limits:**

- NovaBank supports exactly five account balances: SGD, USD, EUR, GBP and AUD. Opening each supported balance costs SGD 0 and appears within 60 seconds after authenticated selection.
- In-app exchanges between these balances have a minimum source value of SGD-equivalent 10, maximum SGD-equivalent 5,000 per exchange and aggregate maximum SGD-equivalent 10,000 per Singapore calendar day.
- Domestic bank transfers and external card top-ups fund SGD only. Holding USD, EUR, GBP or AUD does not create a foreign bank account number or enable international transfers.
- A supported foreign-currency debit-card purchase consumes sufficient same-currency balance first; otherwise the entire purchase converts from SGD under exchange_rate. Staff answer a currency-support enquiry within 2 business days.
- The five supported balances belong to the same personal account. They do not imply five separately opened accounts; at most one balance of each supported currency is available. Currency-support guidance costs SGD 0.

**Verification and required evidence:** Authenticate for balance access or exchange confirmation. Record the currency pair, source principal, quote timestamp/reference and any disputed transaction receipt. No fresh identity document is required for an unchanged verified account; support must not accept a screenshot as authority to execute an exchange.

**Fee and limit reference:** Policy enquiries and calculation reviews cost SGD 0. Any actual NovaBank conversion uses 0.50%, minimum SGD-equivalent 0.50; in-app source principal is 10-5,000 equivalent per exchange and at most 10,000 equivalent daily. Purchase and ATM limits remain independently applicable.

**Intent boundary and unsupported requests:** Balances or conversion for other fiat currencies, cryptocurrency, precious metals and foreign local account details are unsupported. A card issuer's top-up currency eligibility is governed by supported_cards_and_currencies.

**Operational exceptions and status checks:**

- Holding support is exactly SGD, USD, EUR, GBP and AUD. Optional balances belong to the same personal account and do not provide foreign local bank details. Eligibility information costs SGD 0 and is immediate; adding a supported balance in the authenticated app takes up to 60 seconds at SGD 0.
- A sufficient same-currency balance can fund a supported purchase. If it is insufficient, convert the entire purchase from SGD; do not combine several balances. ATM withdrawals always debit SGD, and incoming bank transfers remain domestic SGD even when the customer holds a foreign balance.

### exchange_via_app — Execute an explicitly confirmed exchange between NovaBank's five supported account currencies

**Intent definition:** Execute an explicitly confirmed exchange between NovaBank's five supported account currencies.

**Processing, conditions, fees and limits:**

- Select source and destination balances from SGD, USD, EUR, GBP and AUD. Minimum exchange is SGD-equivalent 10, maximum is SGD-equivalent 5,000 per exchange and total maximum is SGD-equivalent 10,000 per Singapore calendar day.
- Display a quote valid for 30 seconds, the destination amount and the fee of 0.50% with a SGD 0.50 minimum equivalent. Require authenticated confirmation and sufficient source balance for the amount plus fee.
- A confirmed exchange posts within 60 seconds. If the destination balance has not updated after 5 minutes, report the exchange reference; staff acknowledge within 1 business day and review within 2 business days.
- A completed exchange cannot be cancelled. A reverse exchange is a new transaction at a new quote and attracts its own disclosed fee. No duplicate exchange should be submitted while the original is unresolved.

**Verification and required evidence:** Authenticate for balance access or exchange confirmation. Record the currency pair, source principal, quote timestamp/reference and any disputed transaction receipt. No fresh identity document is required for an unchanged verified account; support must not accept a screenshot as authority to execute an exchange.

**Fee and limit reference:** Policy enquiries and calculation reviews cost SGD 0. Any actual NovaBank conversion uses 0.50%, minimum SGD-equivalent 0.50; in-app source principal is 10-5,000 equivalent per exchange and at most 10,000 equivalent daily. Purchase and ATM limits remain independently applicable.

**Intent boundary and unsupported requests:** Crypto conversion, unsupported currencies, scheduled limit orders and retroactive rate selection are unsupported. exchange_rate explains a quote; exchange_charge explains the disclosed fee.

**Operational exceptions and status checks:**

- Verify source/destination balances, quote expiry, principal and separately disclosed fee before confirming. One quote reference permits one exchange; a timeout after confirmation is an unknown status requiring lookup, not permission for an automatic second exchange.
- Execution costs the stated 0.50% fee, minimum SGD-equivalent 0.50, and completes within 60 seconds. If the result remains absent after 5 minutes, submit the reference for a 2-business-day technical review. Principal of SGD-equivalent 10–5,000 per exchange and 10,000 daily is unchanged; fees must additionally be covered by available funds.

### exchange_charge — Explain NovaBank's separately disclosed currency-conversion fee

**Intent definition:** Explain NovaBank's separately disclosed currency-conversion fee.

**Processing, conditions, fees and limits:**

- NovaBank conversion fee is 0.50% of the converted source amount, with a SGD 0.50 minimum or displayed equivalent. It applies to supported in-app exchanges, converted card purchases and converted ATM withdrawals.
- An ordinary same-currency card purchase with sufficient same-currency balance has no conversion fee. ATM foreign-currency withdrawals always debit SGD; their SGD 2 withdrawal fee is additional and separately disclosed.
- In-app exchange displays the fee in a 30-second quote before confirmation. NovaBank purchase conversion uses the settlement quote; merchant or ATM dynamic currency conversion has its own provider's rate and charge.
- Submit an alleged bank fee-calculation error within 60 calendar days of posting. Staff acknowledge within 1 business day, review within 5 business days after complete evidence and credit confirmed errors within 2 business days after approval.
- Calculate fee as max(source principal x 0.005, the quoted source-currency equivalent of SGD 0.50), then round half-up to 2 decimal places. Charge the fee separately in source currency. There is no weekend surcharge, subscription allowance or additional NovaBank FX spread; ordinary market/quote movement remains possible.
- When a merchant or ATM operator converts a transaction into SGD through dynamic currency conversion, NovaBank performs no FX and charges no NovaBank conversion fee on that SGD principal. A completed ATM withdrawal still incurs its separate SGD 2 bank withdrawal fee.

**Verification and required evidence:** Authenticate for balance access or exchange confirmation. Record the currency pair, source principal, quote timestamp/reference and any disputed transaction receipt. No fresh identity document is required for an unchanged verified account; support must not accept a screenshot as authority to execute an exchange.

**Fee and limit reference:** Policy enquiries and calculation reviews cost SGD 0. Any actual NovaBank conversion uses 0.50%, minimum SGD-equivalent 0.50; in-app source principal is 10-5,000 equivalent per exchange and at most 10,000 equivalent daily. Purchase and ATM limits remain independently applicable.

**Intent boundary and unsupported requests:** Waiving every accurately disclosed conversion charge, refunding another provider's fee automatically and crypto conversion are unsupported. exchange_rate explains the rate rather than the fee.

**Operational exceptions and status checks:**

- Fee = the greater of 0.005 times source principal and the quote-time source-currency equivalent of SGD 0.50, rounded half-up to two decimal places. An SGD 20 exchange therefore costs SGD 0.50 and an SGD 200 exchange costs SGD 1.00. Destination principal is calculated from the full source principal; the fee is charged separately.
- There is no weekend surcharge or additional NovaBank bank spread. Merchant or ATM DCC into SGD is not NovaBank conversion and attracts no NovaBank FX fee; the completed ATM fee of SGD 2 still applies. A fee-error claim within 60 calendar days of posting is reviewed within 5 business days; approved corrections credit within 2 business days, at SGD 0 review cost.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Explain the displayed NovaBank currency conversion quote before an exchange or debit-card purchase. | `exchange_rate` |
| Identify the fiat currencies NovaBank can hold and exchange in its personal account. | `fiat_currency_support` |
| Execute an explicitly confirmed exchange between NovaBank's five supported account currencies. | `exchange_via_app` |
| Explain NovaBank's separately disclosed currency-conversion fee. | `exchange_charge` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| exchange_rate / exchange_charge | The quoted source-to-destination rate and its timestamp are exchange_rate; the separately disclosed fee is exchange_charge. |
| fiat_currency_support / exchange_via_app | Whether a currency can be held is support; confirming an actual exchange between supported balances is execution. |
| exchange_rate / settled rate disputes | General/prospective pricing stays here; a settled purchase rate dispute uses card_payment_wrong_exchange_rate and an ATM dispute uses wrong_exchange_rate_for_cash_withdrawal. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not offer unsupported fiat or crypto balances, precious metals, foreign local bank details, international transfers, scheduled or speculative limit orders, future-rate guarantees, retroactive rate choice, or cancellation of completed exchanges.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
