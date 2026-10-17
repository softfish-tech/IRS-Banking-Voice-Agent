---
policy_id: DOC-CAT-ACCOUNT-001
business_category: account_management
included_intents:
  - age_limit
  - edit_personal_details
  - passcode_forgotten
  - terminate_account
  - country_support
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
  - REF-14
  - REF-15
  - REF-13
  - REF-22
---

## NovaBank Personal Account Eligibility, Details and Access Master Policy

### Purpose and Category Scope

Personal-account age and residence eligibility, contact-detail changes, app-passcode recovery and closure. NovaBank provides one personal account per customer with an SGD current balance and optional supported fiat balances.

### Common Fees, Limits and Service Conditions

Minimum age is 18 on the application date. Ordinary residence and the verified residential address must be in Singapore. Eligibility review, detail changes, passcode recovery and eligible closure cost SGD 0. The app passcode has 6 digits; the physical-card PIN has 4 digits. A phone-number change restricts adding beneficiaries and card top-ups for 24 hours after approval.

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

### Eligibility, Recovery and Closure Dependencies

Residence, nationality, identity, contact channel and account ownership are separate facts. A contact update cannot transfer ownership or cure an ineligible residence. A registered number reported compromised cannot be used as the sole recovery proof. Recovery restores verified access; device protection additionally revokes affected sessions and tokens. Closure requires clearing every supported-currency balance and all unsettled obligations, complaints and expected refunds. Termination of cards/tokens does not terminate a merchant service contract. No branch, guardian, joint or overseas residential exception is created.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### age_limit — Apply NovaBank's minimum age rule for personal-account eligibility

**Intent definition:** Apply NovaBank's minimum age rule for personal-account eligibility.

**Processing, conditions, fees and limits:**

- An applicant must be at least 18 years old on the application date and ordinarily resident in Singapore with a supported Singapore residential address.
- Date of birth is checked against a valid government-issued identity document during secure onboarding. An automated complete application is assessed within 10 minutes; manual identity review takes up to 2 business days.
- NovaBank charges SGD 0 for an eligibility assessment. A declined under-age application does not open an account or authorise card ordering.
- If a date of birth was entered incorrectly, submit the correct document through the secure identity channel; staff review the correction within 2 business days. Parents or guardians cannot override the minimum age.

**Verification and required evidence:** Use secure onboarding for eligibility or authenticated app verification for an existing account. Birth-date/legal-name corrections require a valid government-issued photo ID; address changes require a matching 90-day address document. Manual access recovery requires valid photo ID and a live identity check. Staff must not accept account knowledge alone as ownership proof.

**Fee and limit reference:** Eligibility assessment, record changes, recovery and eligible closure cost SGD 0. One personal account per verified customer is permitted. Age, retry and restriction limits in this intent remain mandatory; recovery or closure does not increase transfer or card limits.

**Intent boundary and unsupported requests:** Under-18 accounts, guardian-managed accounts, joint accounts and business accounts are unsupported. country_support addresses residency rather than age; identity verification is a separate onboarding requirement.

**Operational exceptions and status checks:**

- Assess age from the verified date of birth on the application date, not the year of birth alone. The minimum is exactly 18; parent consent, possession of a card or a future eighteenth birthday does not permit early onboarding.
- Public eligibility advice is immediate at SGD 0. A birth-date mismatch requires a valid government-issued photo ID and manual identity review within 2 business days. Do not promise a youth, guardian, joint or student exception, or treat identity-document submission as approval.

### edit_personal_details — Update a verified customer's personal contact or residential details

**Intent definition:** Update a verified customer's personal contact or residential details.

**Processing, conditions, fees and limits:**

- Authenticated app users may change their email or phone number after secure confirmation; a successful contact change appears within 5 minutes at SGD 0.
- A residential-address change requires a proof-of-address document issued within the last 90 calendar days. Staff review a complete address submission within 2 business days; only Singapore residential addresses are supported.
- Legal-name or date-of-birth corrections require a government identity document and manual review within 2 business days. A 24-hour restriction on adding new beneficiaries and card top-ups follows an approved phone-number change.
- For physical cards, an address change cannot redirect a dispatched shipment. An undispatched card order can be amended only after the new address is verified; staff confirm whether amendment is possible within 1 business day.
- No more than 1 successful registered-phone change is permitted in a rolling 24 hours. A verified pre-dispatch card-address amendment receives confirmation within 1 minute once accepted and resets its processing Day 0. Staff eligibility review within 1 business day is distinct from the 2-business-day address-document review and from that final confirmation.

**Verification and required evidence:** Use secure onboarding for eligibility or authenticated app verification for an existing account. Birth-date/legal-name corrections require a valid government-issued photo ID; address changes require a matching 90-day address document. Manual access recovery requires valid photo ID and a live identity check. Staff must not accept account knowledge alone as ownership proof.

**Fee and limit reference:** Eligibility assessment, record changes, recovery and eligible closure cost SGD 0. One personal account per verified customer is permitted. Age, retry and restriction limits in this intent remain mandatory; recovery or closure does not increase transfer or card limits.

**Intent boundary and unsupported requests:** Changing account ownership, assigning another person's identity, overseas residential addresses and replacing identity checks with chat statements are rejected. Account closure uses terminate_account; identity approval uses verify_my_identity.

**Operational exceptions and status checks:**

- Secure phone/email updates take up to 5 minutes at SGD 0; legal-name/address/identity updates require manual review within 2 business days. Legal-name changes require valid ID plus an official name-change or marriage document linking old and new names. Address proof must show legal name and Singapore residence and be issued within 90 calendar days.
- When the old number is unavailable or compromised, use identity-backed assisted recovery rather than an OTP to that number. Allow one successful phone change per rolling 24 hours; after approval restrict beneficiary addition and card top-ups for 24 hours. Updating an address does not redirect an already dispatched card or expand Singapore residence eligibility.

### passcode_forgotten — Restore app access when a customer forgets the NovaBank login passcode

**Intent definition:** Restore app access when a customer forgets the NovaBank login passcode.

**Processing, conditions, fees and limits:**

- The app login passcode has 6 digits and is distinct from the physical card's 4-digit PIN. After 5 incorrect app-passcode attempts, app login is locked for 30 minutes.
- Use Forgot passcode in the genuine app, complete secure recovery to the registered contact channel and a live identity check, then set a new passcode. Successful automated recovery completes within 10 minutes at SGD 0.
- If the registered phone is unavailable or stolen, escalate to assisted security recovery instead of bypassing verification. Staff acknowledge within 1 business day and assess complete manual recovery evidence within 2 business days.
- After an approved registered-phone change, new beneficiaries and card top-ups are restricted for 24 hours. Support chat must never ask for the old/new passcode or any recovery code.

**Verification and required evidence:** Use secure onboarding for eligibility or authenticated app verification for an existing account. Birth-date/legal-name corrections require a valid government-issued photo ID; address changes require a matching 90-day address document. Manual access recovery requires valid photo ID and a live identity check. Staff must not accept account knowledge alone as ownership proof.

**Fee and limit reference:** Eligibility assessment, record changes, recovery and eligible closure cost SGD 0. One personal account per verified customer is permitted. Age, retry and restriction limits in this intent remain mandatory; recovery or closure does not increase transfer or card limits.

**Intent boundary and unsupported requests:** Recovering access based only on account knowledge, emailing passcodes, bypassing identity checks and treating passcode recovery as card-PIN unblocking are prohibited.

**Operational exceptions and status checks:**

- The app passcode is six digits and differs from the four-digit card PIN. Five failed passcode attempts cause a 30-minute app lock; repeated guessing, app reinstalls or new-device registration must not bypass that lock or a security restriction.
- Recovery requires secure ownership confirmation and live identity checking, costs SGD 0 and normally completes within 10 minutes. If the registered number is unavailable or the live match fails, use manual identity review within 2 business days of complete documents. A lost-device case also needs session/token revocation; passcode recovery alone does not secure a stolen handset.

### terminate_account — Close a verified personal NovaBank account after required reconciliation

**Intent definition:** Close a verified personal NovaBank account after required reconciliation.

**Processing, conditions, fees and limits:**

- Submit closure through the authenticated app. Closure requires all currency balances to be zero, no unpaid amount owed, no pending transfers, card authorisations, refunds or disputes, and no unresolved complaint or security hold.
- Eligible closure costs SGD 0 and completes within 5 business days after the prerequisites are satisfied. Staff acknowledge a request within 1 business day; an ineligible request lists the outstanding prerequisites rather than claiming closure.
- Before closure, the customer must resolve foreign balances through supported exchange and transfer out available SGD subject to the SGD 10,000 per-transfer and SGD 20,000 daily limits.
- On closure, all physical, reusable virtual and disposable cards and wallet tokens are cancelled. Closure confirmation is delivered through the registered contact channel; the academic demo uses synthetic records only.

**Verification and required evidence:** Use secure onboarding for eligibility or authenticated app verification for an existing account. Birth-date/legal-name corrections require a valid government-issued photo ID; address changes require a matching 90-day address document. Manual access recovery requires valid photo ID and a live identity check. Staff must not accept account knowledge alone as ownership proof.

**Fee and limit reference:** Eligibility assessment, record changes, recovery and eligible closure cost SGD 0. One personal account per verified customer is permitted. Age, retry and restriction limits in this intent remain mandatory; recovery or closure does not increase transfer or card limits.

**Intent boundary and unsupported requests:** Closing another person's account, waiving outstanding obligations, closing around an unresolved fraud case, or promising deletion of every retained record is unsupported. edit_personal_details changes data without closing the account.

**Operational exceptions and status checks:**

- Before accepting closure, require zero balances in every supported currency, no authorisation holds, outstanding funding reversals, expected refunds, unresolved disputes/complaints, security restrictions or amounts owed. Disable future automatic funding and ask customers to cancel merchant subscriptions; closure is not proof that a merchant contract ended.
- Eligible closure is SGD 0 within 5 business days from complete acceptance. Staff retire all cards and revoke remaining sessions/wallet tokens by completion; final closure is permanent and is not an account-freeze toggle. Customers may save statements before closure, but cannot demand deletion of all retained records. A late incoming refund after closure is a staff exception case, not a promised automatic reopening or payout.

### country_support — Define countries of residence, delivery and transfer service supported by NovaBank

**Intent definition:** Define countries of residence, delivery and transfer service supported by NovaBank.

**Processing, conditions, fees and limits:**

- Account opening is supported only for personal customers aged at least 18 ordinarily resident in Singapore with a verified Singapore residential address. Citizenship alone does not establish or disqualify Singapore residence.
- Physical cards are delivered only to Singapore residential addresses. Standard delivery is 5 business days from the processing acceptance date, with SGD 0 shipping; international forwarding arranged by the customer is not a NovaBank service.
- Bank transfers are domestic SGD only. Supported debit-card purchase and ATM currencies are SGD, USD, EUR, GBP and AUD; travel use at compatible merchants/ATMs does not expand account-opening or bank-transfer country support.
- Residency evidence is reviewed within 2 business days after complete submission, at SGD 0. A customer moving abroad must contact staff for account review and must not be promised continued eligibility or overseas replacement delivery.
- There is exactly 1 supported account-opening country of residence: Singapore. Nationality is not a substitute for residence evidence. Applicable travel merchant/ATM use does not authorize overseas account registration, foreign bank transfers or overseas replacement delivery.

**Verification and required evidence:** Use secure onboarding for eligibility or authenticated app verification for an existing account. Birth-date/legal-name corrections require a valid government-issued photo ID; address changes require a matching 90-day address document. Manual access recovery requires valid photo ID and a live identity check. Staff must not accept account knowledge alone as ownership proof.

**Fee and limit reference:** Eligibility assessment, record changes, recovery and eligible closure cost SGD 0. One personal account per verified customer is permitted. Age, retry and restriction limits in this intent remain mandatory; recovery or closure does not increase transfer or card limits.

**Intent boundary and unsupported requests:** Non-resident onboarding, overseas card delivery, international transfers, business/joint accounts and unsupported-currency transactions are rejected/unsupported. age_limit addresses age; get_physical_card addresses card eligibility and price.

**Operational exceptions and status checks:**

- Ordinary residence and the verified residential address must be in Singapore; nationality is not a substitute for residence. Temporary travel does not make an account ineligible or permit overseas card delivery, foreign local account details or overseas transfer services.
- If the customer moves their ordinary residence outside Singapore, refer for an SGD 0 eligibility review within 2 business days of complete updated evidence. Do not record a fictional Singapore address or silently maintain eligibility. Public supported-country information is immediate at SGD 0; a final staff decision may require orderly closure once all closure conditions are met.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Apply NovaBank's minimum age rule for personal-account eligibility. | `age_limit` |
| Update a verified customer's personal contact or residential details. | `edit_personal_details` |
| Restore app access when a customer forgets the NovaBank login passcode. | `passcode_forgotten` |
| Close a verified personal NovaBank account after required reconciliation. | `terminate_account` |
| Define countries of residence, delivery and transfer service supported by NovaBank. | `country_support` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| age_limit / country_support | Age is assessed on the application date; country_support assesses residence, delivery scope and permitted transfer destinations. |
| edit_personal_details / verify_my_identity | Updating an existing verified record differs from approving onboarding identity; a changed name or birth date may require re-verification. |
| passcode_forgotten / pin_blocked / change_pin | App login uses a 6-digit passcode; card payment uses a 4-digit PIN with separate locks and workflows. |
| terminate_account / edit_personal_details | Closure ends the account after reconciliation; changing contact details leaves it open. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not offer under-18, guardian-managed, joint, corporate or business accounts, non-resident onboarding, ownership transfer, overseas card delivery, authentication bypass, closure with unsettled obligations or unresolved complaints, or guaranteed deletion of all retained records.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
