---
policy_id: DOC-CAT-IDVERIFY-001
business_category: identity_verification
included_intents:
  - why_verify_identity
  - unable_to_verify_identity
  - verify_source_of_funds
  - verify_my_identity
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
  - REF-22
  - REF-23
---

## NovaBank Customer Identity and Funding-Origin Verification Master Policy

### Purpose and Category Scope

Secure identity-verification rationale, onboarding submission, failed verification, and documentary source-of-funds review. These are fictional operational controls, not statements of legal certification or statutory reporting thresholds.

### Common Fees, Limits and Service Conditions

Identity review costs SGD 0. Complete automated checks take up to 10 minutes; manual checks take up to 2 business days. At most 3 automated identity submissions are allowed in a rolling 24 hours before manual review. Required onboarding evidence is a valid government-issued photo ID, live selfie and Singapore proof of address issued within 90 calendar days. Funding-origin review takes up to 5 business days after complete evidence.

### Common Calendar, Authentication and Evidence Rules

All amounts are SGD unless explicitly stated as SGD-equivalent or another supported currency. Fees include any simulated taxes; no additional tax is added. Singapore time is UTC+08:00. Daily limits reset at 00:00 Singapore Time; calendar-month limits reset at 00:00 on the first day of the next month. Rolling 24-hour and rolling 30-calendar-day windows do not reset at midnight.

A business day is Monday to Friday, excluding the configured Singapore public-holiday calendar. Business-day counting begins on the next business day after the stated start event. Hours and calendar days run continuously. Review clocks start when all specified evidence is received, not when an incomplete request is first mentioned. If a review misses its target, staff notify the customer by that deadline, state the reason and provide a next review date; this does not itself approve a refund or resolve a complaint.

Public policy questions need no authentication. Account-specific disclosures and changes require a secure authenticated app session and OTP, or the assisted verification stated in the relevant intent. OTPs expire after 5 minutes, allow 3 attempts and lock that verification challenge for 30 minutes after 3 failures. OTPs, full PINs, CVVs, passcodes and complete card credentials must never be collected in support chat. Any required payment credentials belong only in the secure payment form. Escalate alleged fraud immediately without waiting for routine evidence collection; changing account state still requires secure verification.

For already verified customers, no new identity document is needed for an ordinary enquiry or permitted action unless identity, address or recovery records have changed. Proof of a changed Singapore address is a utility bill or bank statement issued within 90 calendar days, showing legal name and residential address; changed legal identity requires a valid government-issued identity document. Complete routine identity/address changes are reviewed within 2 business days. Files must be uploaded in the secure app, not ordinary chat. Case evidence is limited to relevant references, timestamps, amounts, masked identifiers and receipts specified below.

### Academic Scope and Safety

NovaBank is fictional. All commercial terms and controls are invented for an academic personal-retail-banking prototype. Active status is a corpus designation, not a real-world approval. Use synthetic customer records and simulated operations. The assistant must not claim a real transfer, freeze, refund, verification or account change was executed.

B-RAG returns evidence; C owns risk, business permission and complaint transitions; E owns orchestration and simulated execution. A review target is not a guaranteed favourable outcome. Intake does not resolve a complaint: keep OPEN or UNDER_REVIEW until an authorised resolution event. Unresolved complaints block recommendations; later recommendation needs explicit recommendation consent, risk clearance and eligibility. Consent to a funding or wallet feature is not recommendation consent.

Use ABSTAIN when the request is understood but reliable applicable evidence is absent; use CLARIFY for unclear intent or missing required information. Do not infer an unsupported service from a related-intent link. No real banking, credit/loan, crypto, business-account, joint-account or international-transfer service is introduced by this policy.

### Evidence Quality, Source Link and Review Start

Identity matching, funding-card ownership and funding-origin verification are separate approvals. Evidence must be readable, genuine and linked to the relevant person and transaction. Only the secure upload route accepts documents; a support chat attachment is not verification approval. A live selfie must be taken by the applicant rather than supplied as a stored image. Staff issue a deficiency notice when evidence is incomplete and retain the received-evidence timestamps. Complete-evidence review clocks do not guarantee approval or automatic restriction removal. Statutory legal advice, business-owner screening and tax filing are outside scope.

### Policy Provenance and Commercial Authority

NovaBank is the sole fictional policy entity. Version 1.1 adds operational conditions to the inherited synthetic fees, caps and service boundaries. External FAQs informed review topics only; they do not determine NovaBank prices, legal liability or service availability. Reference IDs in metadata resolve to the separate reference registry and analysis report; those references are not executable or customer-policy authority.

## Intent Rules and Service Commitments

### why_verify_identity — Explain the purpose, prerequisites and boundaries of NovaBank identity verification

**Intent definition:** Explain the purpose, prerequisites and boundaries of NovaBank identity verification.

**Processing, conditions, fees and limits:**

- Identity verification is required before opening the personal account, issuing cards, accepting funding or executing transfers. The synthetic control checks age of at least 18, Singapore residence and matching identity ownership.
- Submit a valid government-issued photo identity document, a live selfie and Singapore proof of address issued within 90 calendar days through the secure onboarding screen.
- Complete automated verification is assessed within 10 minutes; cases referred for manual verification take up to 2 business days after complete documents. NovaBank charges SGD 0 for verification.
- Support can explain required documents but cannot approve identity from an ordinary chat attachment or accept PINs, CVVs or one-time codes. This academic policy describes fictional controls and does not claim certification of legal compliance.

**Verification and required evidence:** Use secure onboarding to submit a valid government-issued photo ID, live selfie and Singapore proof of address issued within 90 calendar days. For funding-origin review, supply a transfer reference and matching salary slip, savings statement or sale agreement; bank statements must be issued within 90 calendar days. Ordinary support chat cannot approve uploaded documents.

**Fee and limit reference:** Identity and funding-origin review fees are SGD 0. Identity automation permits at most 3 submissions per rolling 24 hours. Funding-origin triggers are an incoming transfer of at least SGD 10,000, rolling 30-day incoming electronic funding of at least SGD 20,000, or a recorded risk concern; thresholds are not payment caps.

**Intent boundary and unsupported requests:** Anonymous accounts, bypassing verification, substituting marketing consent for identity approval and authenticating a real customer through the academic demo are unsupported. verify_my_identity describes submission; unable_to_verify_identity handles failure.

**Operational exceptions and status checks:**

- Identity review establishes the applicant's legal identity, age and Singapore residence; funding-origin review separately checks where a transaction's money came from. A successful card ownership check or OTP does not replace either review, and review is not a statement of statutory certification.
- Public explanations are immediate at SGD 0. Actual verification requires valid government photo ID, live selfie and name-matched Singapore address evidence issued within 90 calendar days. Automated review takes up to 10 minutes, manual review up to 2 business days after complete evidence. Customers unable to supply evidence receive an explicit deficiency notice; staff cannot approve anonymous access.

### unable_to_verify_identity — Resolve a failed or incomplete secure identity-verification attempt

**Intent definition:** Resolve a failed or incomplete secure identity-verification attempt.

**Processing, conditions, fees and limits:**

- Check whether the document is valid, all corners are visible, the name and birth date match the application, the live selfie is clear, and Singapore address evidence is no older than 90 calendar days.
- Permit up to 3 automated submissions within 24 hours. After the third unsuccessful attempt, require manual review instead of repeated automated retries; do not treat the account as verified.
- Automated assessment takes up to 10 minutes per complete submission. Manual review takes up to 2 business days after complete evidence, and costs SGD 0.
- The secure rejection screen identifies a resubmittable defect or a final eligibility decision. A customer disputing a final decision may request one staff review within 30 calendar days after the final decision is notified to the customer through the secure app or registered contact channel; staff decide within 5 business days after complete evidence.

**Verification and required evidence:** Use secure onboarding to submit a valid government-issued photo ID, live selfie and Singapore proof of address issued within 90 calendar days. For funding-origin review, supply a transfer reference and matching salary slip, savings statement or sale agreement; bank statements must be issued within 90 calendar days. Ordinary support chat cannot approve uploaded documents.

**Fee and limit reference:** Identity and funding-origin review fees are SGD 0. Identity automation permits at most 3 submissions per rolling 24 hours. Funding-origin triggers are an incoming transfer of at least SGD 10,000, rolling 30-day incoming electronic funding of at least SGD 20,000, or a recorded risk concern; thresholds are not payment caps.

**Intent boundary and unsupported requests:** Expired or altered documents, under-age eligibility exceptions, remote approval via chatbot and another person's selfie are rejected. A pending review must not be described as successful verification.

**Operational exceptions and status checks:**

- Identify whether failure concerns expired ID, missing document side, glare/cropping, mismatched legal name/date of birth, address freshness or live-selfie quality. Enable camera permissions and submit clear original evidence securely; a static selfie, altered image or another person's document is unacceptable.
- Allow at most three automated submissions per rolling 24 hours at SGD 0; after the third unsuccessful submission move to manual review, targeted within 2 business days of complete evidence. A documented final decision may receive one staff reconsideration requested within 30 calendar days after the final decision is notified to the customer through the secure app or registered contact channel, with a decision within 5 business days after complete evidence. Recording a decision internally or uploading more documents does not start or restart the 30-calendar-day window. Retrying incomplete or identical files does not restart eligibility or bypass controls.

### verify_source_of_funds — Review the origin of funding under NovaBank's synthetic source-of-funds control

**Intent definition:** Review the origin of funding under NovaBank's synthetic source-of-funds control.

**Processing, conditions, fees and limits:**

- A review is triggered when an incoming transfer is SGD 10,000 or more, total incoming electronic funding reaches SGD 20,000 within a rolling 30-calendar-day period, or a security officer records a risk concern. These are fictional review thresholds, not legal reporting thresholds.
- Submit through the secure app the transfer reference, origin bank and documentary explanation such as a salary slip, savings statement or sale agreement. Documents must identify the customer and match the transaction; statements must be issued within 90 calendar days.
- NovaBank acknowledges complete evidence within 1 business day and targets a decision within 5 business days. Review costs SGD 0; restricted funds must not be presented as available while a hold applies.
- A threshold review may affect availability without implying wrongdoing. The risk team decides release or rejection and communicates the permitted next step; chat cannot guarantee approval.
- For the rolling SGD 20,000 threshold, aggregate gross credited incoming domestic transfers and credited external-card top-ups over the preceding 30 calendar days. Failed/uncredited attempts, internal exchanges, merchant refunds and approved error corrections are excluded. Reversal of a credited funding entry does not erase its historical gross contribution. Risk concerns may trigger review below either numeric threshold.
- Collect an explanation for legitimate third-party transfers and evidence linking the sender and economic purpose. A funding-origin hold blocks use of the affected funds; it does not automatically declare unrelated balances unavailable or the complaint resolved.

**Verification and required evidence:** Use secure onboarding to submit a valid government-issued photo ID, live selfie and Singapore proof of address issued within 90 calendar days. For funding-origin review, supply a transfer reference and matching salary slip, savings statement or sale agreement; bank statements must be issued within 90 calendar days. Ordinary support chat cannot approve uploaded documents.

**Fee and limit reference:** Identity and funding-origin review fees are SGD 0. Identity automation permits at most 3 submissions per rolling 24 hours. Funding-origin triggers are an incoming transfer of at least SGD 10,000, rolling 30-day incoming electronic funding of at least SGD 20,000, or a recorded risk concern; thresholds are not payment caps.

**Intent boundary and unsupported requests:** Forged evidence, splitting funding to avoid review, treating funding-card ownership proof as complete source-of-funds proof and chatbot release of a review hold are prohibited.

**Operational exceptions and status checks:**

- Match a bank statement issued within 90 calendar days to the actual credited amount, payer, date and source explanation. Salary requires a payslip issued within 90 calendar days and matching salary credit; asset sale requires a signed sale contract and matching proceeds; inheritance requires an official estate/probate distribution record and matching credit; a gift requires donor identity/relationship declaration and transfer evidence. Document upload alone is not approval.
- Trigger review on a single incoming bank transfer of at least SGD 10,000, gross credited bank-plus-card funding of at least SGD 20,000 over rolling 30 calendar days, or a risk flag. Exclude failed attempts, internal exchanges, refunds and error corrections; a subsequent reversal does not erase prior gross credit. These are fictional controls, not statutory reporting thresholds.
- Acknowledge within 1 business day and review within 5 business days after complete evidence at SGD 0. A missing source link requires a deficiency notice and the target cannot be measured from an incomplete upload. Restrictions remain until authorised staff action; do not split funding, invent documents or promise release solely because the review target has passed.

### verify_my_identity — Submit and complete secure identity verification for NovaBank onboarding

**Intent definition:** Submit and complete secure identity verification for NovaBank onboarding.

**Processing, conditions, fees and limits:**

- Applicants must be at least 18 and ordinarily resident in Singapore. Submit a valid government-issued photo identity document, live selfie and Singapore proof of address issued within 90 calendar days through secure onboarding.
- A complete automated application is assessed within 10 minutes; manual review takes up to 2 business days after complete evidence. Verification costs SGD 0 and cannot be skipped before account opening, funding or card issuance.
- At most 3 automated submissions are accepted within 24 hours before manual review is required. A successful result must be recorded as VERIFIED by the authorised verification component, never inferred from uploaded files alone.
- The academic deployment uses fictional identity fixtures, not real customer documents. Support explains the process without collecting PINs, CVVs, one-time codes or raw identity documents through an ordinary RAG chat.

**Verification and required evidence:** Use secure onboarding to submit a valid government-issued photo ID, live selfie and Singapore proof of address issued within 90 calendar days. For funding-origin review, supply a transfer reference and matching salary slip, savings statement or sale agreement; bank statements must be issued within 90 calendar days. Ordinary support chat cannot approve uploaded documents.

**Fee and limit reference:** Identity and funding-origin review fees are SGD 0. Identity automation permits at most 3 submissions per rolling 24 hours. Funding-origin triggers are an incoming transfer of at least SGD 10,000, rolling 30-day incoming electronic funding of at least SGD 20,000, or a recorded risk concern; thresholds are not payment caps.

**Intent boundary and unsupported requests:** Anonymous onboarding, using another person's document, under-age accounts and verification performed solely by a language model are unsupported. why_verify_identity explains rationale; unable_to_verify_identity addresses rejected submissions.

**Operational exceptions and status checks:**

- Use the secure onboarding screen to capture valid government-issued photo ID, live selfie and utility bill or bank statement showing legal name and Singapore residence, issued within 90 calendar days. Show all required edges/sides and readable details; changed names require an official linking document, and unsupported evidence must be escalated rather than guessed acceptable.
- Complete automated review targets 10 minutes and manual review 2 business days, both SGD 0, with three automated submissions per rolling 24 hours before manual handling. The app must show submitted, additional-evidence-needed, under-review or approved status; a successful upload is not an approval and must not enable protected actions.

## Intra-Category Intent Distinctions

### Primary Intent Decision Matrix

| Customer need or event | Primary intent |
| --- | --- |
| Explain the purpose, prerequisites and boundaries of NovaBank identity verification. | `why_verify_identity` |
| Resolve a failed or incomplete secure identity-verification attempt. | `unable_to_verify_identity` |
| Review the origin of funding under NovaBank's synthetic source-of-funds control. | `verify_source_of_funds` |
| Submit and complete secure identity verification for NovaBank onboarding. | `verify_my_identity` |

### Overlapping Intent Boundaries

| Comparison | Required distinction |
| --- | --- |
| why_verify_identity / verify_my_identity | The rationale and required controls differ from submitting documents and obtaining an authorised result. |
| unable_to_verify_identity / verify_my_identity | A defective, failed or disputed attempt requires remediation; an initial complete submission uses verify_my_identity. |
| verify_source_of_funds / verify_my_identity | Identity establishes who the customer is; source-of-funds establishes where the money originated. |
| verify_source_of_funds / verify_top_up | Card ownership evidence is not necessarily evidence of salary, savings, sale proceeds or other economic funding origin. |

## Category Guardrails and Cross-Category Routing

### Explicitly Unsupported Requests

Do not allow anonymous accounts, altered or expired identity documents, another person's identity, under-age exceptions, ordinary-chat identity approval, unsupported-document guessing, fabricated source-of-funds evidence, splitting funding to evade review, or release of a hold by a language model.

### High-Risk, Missing-Evidence and Execution Boundaries

Suspected fraud, theft, credential compromise or an alleged unauthorised debit is escalated immediately to the Rules module and urgent security staff, available 24/7. Do not let a routine estimate, unsupported-method label or missing receipt suppress the high-risk route. Where the event belongs to a different category, retrieve that category's policy and retain its own start event, deadline and fee; related labels are not interchangeable. Never promise a real operation, unconditional refund, automatic hold release or favourable review result.

### Version and Evidence Applicability

This policy applies to synthetic events from 2026-10-11. Preserve policy_id, business_category, included_intents, version, effective_date and source_type on every retrieved chunk. An intent section includes its conditions, verification and boundary text; retrieve the applicable shared section when a local rule relies on it. If no applicable historical version exists or a conflict is unresolved, abstain and refer for staff review.

### Chunk Context and Version Selection

Retrieve this master with the relevant shared calendar, fee and verification sections. A paragraph-level chunk must retain its intent heading and exception conditions. Select version 1.1 for synthetic events on or after 2026-10-11; preserve v1.0 separately for earlier events and never index both as current authority. A related-intent link may broaden retrieval but does not broaden supported products. Where an authoritative simulated status or required evidence is missing, clarify or abstain and refer to authorised staff; do not claim an operation was executed.
