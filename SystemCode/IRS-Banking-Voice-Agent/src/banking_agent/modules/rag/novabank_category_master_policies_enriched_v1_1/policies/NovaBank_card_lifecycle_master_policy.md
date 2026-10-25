---
policy_id: DOC-CAT-CARDLIFE-001
business_category: card_lifecycle
included_intents:
  - card_arrival
  - card_delivery_estimate
  - get_physical_card
  - getting_spare_card
  - order_physical_card
  - activate_my_card
  - card_about_to_expire
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
---

## NovaBank Physical Debit Card Lifecycle Master Policy

### Purpose, Products and Applicability

This policy governs physical Visa debit cards for verified personal retail customers with an active NovaBank SGD current account. All NovaBank fees, limits and deadlines are synthetic contractual design choices for the academic prototype. Public banking material informed operational topics, not NovaBank prices or legal liability. Active status applies within the simulation.

Customers must be at least 18 and ordinarily resident at a verified Singapore residential address. A spare is another card for the same customer, not a supplementary card for a family member. Joint, guardian-managed, business and credit accounts are unsupported. Card possession or uploading evidence does not establish identity approval.

### Calendar, Cutoff and Service Start Events

A business day is Monday to Friday excluding the configured Singapore public-holiday calendar. All times use Singapore Time, UTC+08:00. Day 0 is the processing acceptance date: orders accepted by 14:00 on a business day use that date; later or non-business-day orders use the next business day. Day 1 is the next business day after Day 0.

Order acceptance requires completed verification, an eligible card entitlement, confirmed address, payment approval and an available order slot. Submitting an incomplete request does not start delivery time. Business-day review and refund clocks begin on the next business day after their stated event. Calendar days and hour windows run continuously.

App requests may be submitted 24/7. Production follows the cutoff; urgent security reporting operates 24/7 without waiting for production hours. A missed service deadline requires investigation and a dated update, not automatic complaint resolution.

### Fees and Delivery Service Matrix

All fees are SGD, inclusive of simulated taxes. There is no additional tax. Issuance and delivery are separate charges.

| Issuance purpose | Issuance fee | Standard total | Express total |
| --- | ---: | ---: | ---: |
| First main card | 0 | 0 | 10 |
| Spare card | 15 | 15 | 25 |
| Scheduled or permitted early renewal | 0 | 0 | 10 |
| Customer-loss, damage, verified credential-exposure or ATM-retention replacement | 15 | 15 | 25 |
| Confirmed courier-loss or NovaBank production-error replacement | 0 | 0 | 10, unless waived below |
| Reissuance after an activation deadline | 15 | 15 | 25 |

Standard delivery costs SGD 0, dispatches by the end of Day 2 and arrives by the end of Day 5. Express delivery costs SGD 10, dispatches by the end of Day 1 and arrives by the end of Day 2. There is no same-day, branch-pickup, overseas, PO-box or unverified third-party-address service. A service deadline assumes verified address details and successful delivery access.

If an original paid express deadline is missed through confirmed NovaBank or courier fault, refund that original SGD 10 surcharge within 3 business days after confirmation. A required replacement is sent express without another delivery surcharge. Issuance fees remain payable when the applicable card is supplied; a spare issuance fee is not refunded merely because its shipment is replaced. No automatic compensation for indirect losses is specified by this lifecycle policy.

### Card Counts, Renewal Overlap and Order States

One account may hold at most 2 non-retired physical cards, including ordered or inactive cards: one main and one spare. A renewal temporarily permits a third non-retired physical card, but never creates a third concurrently usable card; activation retires its predecessor. Virtual-card entitlements are separate and governed by virtual_cards. All cards use existing account-level allowances; extra cards do not multiply transaction limits.

Only 1 unfulfilled dispatch order is permitted per account. Relevant order states are ACCEPTED, DISPATCHED, DELIVERY_EXCEPTION, DELIVERED, CANCELLED and CLOSED. These are synthetic fulfilment records, not additions to the project's executable AgentState enums. An exception remains unfulfilled until the original order is delivered or closed. Replacement acceptance requires closing the predecessor's dispatch order.

A temporary freeze blocks new use but can be removed only after permitted verification. Permanent cancellation or retirement cannot be undone. Returning or finding a cancelled card does not restore it. Do not confuse cancellation of an undispatched order with cancellation of an active card.

### Authentication, Evidence and Secure Channels

Public policy enquiries need no authentication. Individual tracking and changes require a secure authenticated app session and OTP, or assisted verification when the registered phone is unavailable. An OTP expires after 5 minutes, allows 3 attempts and locks that challenge for 30 minutes after 3 failures. App-passcode and card-PIN blocks are separate controls under their own policies.

Customers enter secret codes only in the secure app. Support chat must not collect OTPs, full card numbers, CVVs, PINs, passwords or complete-card photographs. Identify a card using its last 4 digits plus the displayed order or card-record identifier where the suffix is ambiguous.

An unchanged verified customer needs no new identity document for routine lifecycle service. Changed address evidence is a utility bill or bank statement issued within 90 calendar days, showing legal name and Singapore residential address. Changed legal identity or assisted recovery requires a valid government-issued photo ID and secure live identity check. Complete identity/address evidence is reviewed within 2 business days. A production name may use up to 20 characters, including letters, spaces, hyphens and apostrophes; unsupported rendering is reviewed within 2 business days without changing the verified legal identity.

### Security, Payment Continuity and Liability Boundaries

Report loss, theft, suspected exposure or an unrecognised debit immediately, including while abroad. Urgent escalation precedes routine delivery questions and does not wait for a police report. Secure verification is still required before changing account state. An authenticated protective card freeze takes up to 60 seconds at SGD 0. Associated wallet-token suspension is completed within 5 minutes through the security workflow.

Freeze or cancellation cannot guarantee that an already authorised payment will not settle. It does not erase merchant contracts, cancel subscriptions with merchants, refund earlier debits or resolve a complaint. A missing or replaced card does not prevent matching a legitimate refund to its originating account.

Customer liability, reimbursement and dispute eligibility are decided under the applicable security/dispute policy after evidence review. This policy imposes no automatic 48-hour loss-forfeiture rule, no inference that OTP/PIN use conclusively establishes authorisation, and no unconditional zero-liability promise. The existing standard card-dispute intake window is 60 calendar days after settlement; late security allegations still receive assessment. That intake window is not a deadline to delay reporting and is not an automatic liability decision.

## Intent-Specific Policies

### get_physical_card — Eligibility and First-Card Access

Use this intent for availability, eligibility or first-card instructions without actual order submission. The customer must be at least 18, have an active verified personal SGD account and a verified Singapore address, have no existing main physical card and have no issuance restriction.

The authenticated eligibility check returns immediately at SGD 0. The initial entitlement is 1 main physical card. Initial issuance costs SGD 0; standard arrival is Day 5 at SGD 0 delivery, or express arrival is Day 2 at SGD 10. Address or identity defects require the specified evidence and up to 2 business days of review before ordering.

If no card appears in the app despite apparent eligibility, collect a masked account reference and error message. Staff acknowledge within 1 business day and review within 2 business days after complete evidence. Do not issue a second initial card to bypass an existing record. An old main card must be retired through its appropriate replacement or closure path.

This intent does not grant joint-account or family-member card access, a credit line, or spending before physical receipt. Independent reusable virtual-card availability, if needed while waiting, belongs to virtual_cards and requires its own permission. Actual submission uses order_physical_card.

### order_physical_card — Order Acceptance, Changes and Replacement Submission

Use this intent to submit an eligible initial, spare or authorised replacement order. A renewal decision belongs to card_about_to_expire; this order workflow may fulfil it. Authenticate, select the card/replacement reason, confirm the verified address and production name, choose service and approve the itemised fee. No fresh ID is needed with unchanged verified records.

Confirmation and an order ID appear within 1 minute of acceptance. Standard dispatch/arrival are Day 2/Day 5; express dispatch/arrival are Day 1/Day 2. Fees follow the issuance matrix. Only 1 unfulfilled dispatch order is permitted; only 1 replacement may be issued against the same retirement event. A repeated submission carrying the same accepted request ID returns that order, not another fee or card.

Insufficient available funds for a required fee prevent acceptance; no production or delivery clock starts. A security freeze must proceed independently even when a paid replacement cannot yet be funded. A technical submission error with no confirmed order is reviewed within 2 business days; check the existing order before retrying.

Before dispatch, cancellation costs SGD 0 and refunds collected order fees within 3 business days. If cancellation loses the race to dispatch, the order cannot be recalled through routine cancellation; any security concern is escalated immediately. Cancellation of a replacement order does not reactivate its cancelled predecessor.

Before dispatch, an address amendment is accepted only after the new Singapore address is verified. Complete address evidence is reviewed within 2 business days; pending verification does not reroute the current order. Once an amendment is accepted, confirmation occurs within 1 minute and Day 0 resets. The confirmation shows the revised deadline and any customer-approved change in delivery service. After dispatch, no rerouting or name amendment is supported.

For a damaged-card replacement, explain the interruption and obtain explicit replacement approval; retire the predecessor before accepting its replacement so the 2-card limit remains intact. The customer cannot keep using that retired card while waiting; an existing spare may be used only if independently eligible and unrestricted. Lost, stolen, reported-missing or compromised predecessors remain blocked and are retired through security before replacement acceptance. If a defect is confirmed as NovaBank production error, reissuance is SGD 0; ordinary damage, loss, ATM retention and security replacements are SGD 15 plus selected delivery. Only renewal receives the defined third-card overlap.

### card_delivery_estimate — Prospective and In-Window Delivery Enquiries

Use this intent before ordering or while the accepted order remains within its deadline. Quote standard arrival by Day 5 at SGD 0, or express arrival by Day 2 at SGD 10. Use the actual processing Day 0, including a confirmed pre-dispatch amendment; do not count from an incomplete request, enquiry date or fee-review date.

Authenticate for an existing order and provide its order ID. The estimate is returned immediately at SGD 0, for 1 order per enquiry; no new ID is required with unchanged records. Courier events appear within 4 hours after NovaBank receives a scan. Absence of a scan is not proof of loss, and a scan does not prove verified customer receipt.

Quote an absolute expected date when the configured holiday calendar is available. A weekend enquiry does not change the acceptance cutoff. A missed dispatch checkpoint before the arrival deadline receives a fulfilment update within 1 business day; security concerns may be reported immediately. Routine nonarrival after Day 5 or Day 2, and any delivered-but-not-received claim, use card_arrival.

Known delivery disruption must show the reason and next dated update; it cannot silently reset the original deadline. No guaranteed overseas arrival, same-day dispatch or acceleration through repeated requests is permitted. A renewal estimate uses its actual renewal order, not the predecessor's expiry date as a substitute start event.

### card_arrival — Nonreceipt, Delivery Exceptions and Unsafe Packaging

Use this intent after the standard Day 5 or express Day 2 arrival deadline, or immediately for delivered-but-not-received status, a wrong recipient, damaged/tampered packaging, or a delivered card bearing the wrong customer identity. Security concerns must not wait for the ordinary deadline.

Authenticate and obtain the order ID, verified-address confirmation, courier status and claimed receipt circumstances. Submit a masked envelope/tracking image if available, hiding full card details. No fresh ID is needed for an unchanged verified address. Open 1 investigation per order within 1 minute at SGD 0 and reach a delivery decision within 2 business days after the complete report. A delayed investigation requires notification by its deadline and a next dated review; it does not automatically prove delivery or loss.

For denied receipt or suspected tampering, apply protective freeze within 60 seconds of authenticated instruction and route security concerns immediately. A building concierge's receipt or courier signature is evidence to examine, not authority to activate. A different person's card must not be used or disclosed; secure staff arrange its handling and investigate possible data exposure.

Confirmed courier loss, misdelivery or production error requires retirement of the affected card and closure of its order before replacement acceptance. Replacement issuance and standard delivery cost SGD 0 with arrival by new Day 5. Express costs SGD 10 with arrival by new Day 2, except that a confirmed fault-related missed paid express deadline earns free express replacement and refund of the original SGD 10 surcharge within 3 business days. A paid spare issuance fee remains attached to the replacement entitlement.

For customer-unavailability failures, allow 1 free standard redelivery within 3 business days of the agreed redelivery instruction. After a second failed attempt, retire the returned card; new dispatch costs SGD 5 plus SGD 10 if express is selected, without another issuance fee, and uses Day 5 or Day 2. No post-dispatch change to an unverified or overseas address is allowed.

If an investigation verifies receipt and secure custody, the authorised team may release a temporary freeze after ownership checks. If loss or compromise led to permanent cancellation, later discovery never restores the card. A replacement order and fee waiver do not themselves resolve an associated transaction dispute.

### getting_spare_card — Additional Card for the Same Account Holder

Use this intent for a second physical card while retaining the customer's main card. Eligibility requires 1 non-retired main card, no spare, no account issuance restriction and no unfulfilled dispatch order. A spare has its own number and PIN, uses the same balance and shares existing purchase/ATM limits.

Authenticate, confirm the verified address and itemised charge, and obtain order confirmation within 1 minute. Spare issuance is SGD 15; standard total is SGD 15 with arrival by Day 5, and express total is SGD 25 with arrival by Day 2. At most 1 spare per account is permitted. No new ID is needed with unchanged records; address changes require 90-day evidence and review within 2 business days.

The spare is not transferable to a spouse, child or joint-account holder. It cannot serve as a security-block bypass or an additional account allowance. An already active spare may continue during ordinary main-card renewal only if no account-wide or spare-specific restriction applies. An unrecognised transaction or account-level compromise requires security clearance rather than assurance that the spare remains safe.

A spare cannot be created as an emergency overseas delivery product. Its activation follows activate_my_card; its own expiry follows card_about_to_expire. Loss of an existing spare uses replacement, not a second spare entitlement.

### activate_my_card — Possession Verification and First Use

Use this intent for a received inactive initial, spare, replacement or renewal card. Authenticate, complete OTP verification, select the exact card record and matching last 4 digits, confirm expiry month/year against the card, and confirm physical possession. No fresh identity document is needed with current verification. A damaged seal, wrong printed identity or missing card must be handled before activation.

Activation costs SGD 0 and completes within 60 seconds after successful verification. Maximum is 1 card per request and 3 activation submissions per card per Singapore calendar day. The daily block resets at 00:00 the following day; OTP lockout remains separately applicable. Initial and spare cards must activate within 90 calendar days after dispatch; retire them on Day 91. Reissuance is SGD 15 plus selected delivery, with Day 5 or Day 2 arrival. Replacement cards issued for loss, damage or activation-deadline retirement follow the same 90-day dispatch window; renewal follows its separate expiry-based window below.

Successful renewal activation retires the predecessor within 60 seconds. Other replacement predecessors were already retired before replacement acceptance and cannot return to use. Suspended, reported-missing, expired or retired cards cannot be activated. Being overseas does not waive verification or create overseas delivery eligibility; activation of a securely received card is permitted through the secure app from abroad.

Set or confirm the 4-digit PIN only in the secure app. This policy creates no PIN-by-email or shared-envelope service. First physical contactless use requires one successful chip-and-PIN purchase; PIN changes/unblocking and tap thresholds belong to card_usage_and_access. Activation does not remove account restrictions or guarantee merchant approval.

A replacement or renewal has newly recorded card credentials and expiry. Customers must update relevant merchant card-on-file and recurring-payment details through each merchant's secure channel; automatic credential update is not guaranteed. Old merchant obligations are not cancelled by changing the card. Associated old-card wallet tokens are suspended through the security/wallet workflow within 5 minutes of predecessor retirement; any new token requires its own enrolment. Existing account-level notification preferences remain, and order/activation alerts are generated within 1 minute to the registered app/contact channel, subject to channel delivery.

If activation is still unresolved after 5 minutes, check the authoritative card status before another submission. Staff acknowledge within 1 business day and diagnose within 2 business days after receiving the masked card identifier, activation reference and timestamp. A success message alone does not authorize manual status override.

### card_about_to_expire — Scheduled Renewal, Travel and Nonrenewal

Use this intent when a card approaches or passes expiry without a security incident. Expiry occurs at 23:59:59 Singapore Time on the final calendar day of its printed expiry month. There is no grace period, no expiry extension and no fee to report expiry.

Create scheduled renewal 30 calendar days before expiry, or on the next business day if the trigger date is non-business, provided identity/address records are current, the account is eligible and a fulfilment slot is available. Renewal issuance and standard delivery are SGD 0, arriving by Day 5; express is SGD 10, arriving by Day 2. Only 1 renewal per predecessor is permitted. An early renewal suppresses the later duplicate scheduled order.

For declared travel before expiry, allow an early-renewal request when the current card expires within 90 calendar days. Securely confirm the planned departure date, current card record and verified Singapore address; a passport or travel ticket is not routinely required. Staff approve or decline eligibility within 2 business days after complete information at SGD 0. After acceptance, the same free renewal and Day 5/Day 2 delivery terms apply. No completion-before-departure guarantee or overseas dispatch is offered. Cards expiring beyond 90 days do not qualify for this exception.

Renew main and spare separately. If both require renewal, accept the second on the next business day after the first order closes and its predecessor retires, keeping at most 3 non-retired physical cards during overlap. Notify the customer immediately of a delayed second renewal; neither delay nor early-renewal request extends expiry.

If eligibility, verification or an account restriction prevents renewal, issue the reason and next required step within 1 business day of recording that blocker. Address evidence is reviewed within 2 business days. An expired card requires manual renewal eligibility review within 2 business days; do not label it active while awaiting delivery. An overdue existing renewal shipment uses card_arrival rather than creating a duplicate renewal.

The predecessor remains usable until expiry or renewal activation, whichever occurs first, and retires automatically at expiry. Renewal activation retires it within 60 seconds. Activate the renewal within 60 calendar days after predecessor expiry; retire an unactivated renewal on Day 61. Subsequent reissuance costs SGD 15 plus the selected delivery fee with Day 5 or Day 2 arrival.

Update saved merchant and recurring-payment credentials after activating the renewal; the bank does not guarantee automatic migration. Match later valid refunds to the originating account even when the predecessor has expired. Destroy a retired card by cutting through its chip and magnetic stripe and obscuring printed credentials; do not send card photographs as disposal proof. PIN support, wallet enrolment, refunds and transaction disputes retain their own category rules.

## Intent Distinction and Cross-Category Routing

### Primary Intent Decision Matrix

| Customer situation | Primary intent | Operational boundary |
| --- | --- | --- |
| Can I get my first physical card? | get_physical_card | Eligibility information; no order is placed. |
| Submit or change an eligible order before dispatch | order_physical_card | Acceptance, fees and fulfilment records. |
| When will an in-window card arrive? | card_delivery_estimate | Use actual order acceptance and service type. |
| Overdue, denied receipt, wrong recipient or unsafe packaging | card_arrival | Investigate; protect immediately when security is implicated. |
| Second card while keeping my main card | getting_spare_card | Same owner, one spare, no additional account allowance. |
| Received inactive card; enable it | activate_my_card | Secure possession verification; retire applicable predecessor. |
| Expiry, scheduled renewal or eligible pre-travel renewal | card_about_to_expire | One renewal, expiry unchanged, separate activation clock. |

### Security and Related Categories

Lost/stolen cards, exposed credentials and unrecognised purchases route immediately to security_and_unrecognised_transactions, including abroad. ATM retention also needs cash_withdrawals evidence; any missing cash has a separate reconciliation. An already active card failing at a terminal uses card_usage_and_access or card_payments. Forgotten PINs are not failed activation; forgotten app passcodes belong to account_management.

Card credential updates are lifecycle guidance; merchant contract cancellation, settlement disputes and refunds are governed by card_payments/refunds. Foreign travel does not establish foreign-resident account eligibility. A family-card request remains unsupported and does not create a joint/supplementary product.

### Unsupported Services and Liability Decisions

NovaBank does not support overseas physical-card dispatch, hotel delivery abroad, emergency overseas cash, branch pickup, same-day cards, PO-box delivery, unverified third-party rerouting, family/supplementary cards, joint accounts, third concurrently usable physical cards, activation without receipt, revival of retired cards or expiry extensions.

Credit limits, overdrafts, credit instalments, rewards, loans and investments are outside this category and are not introduced by a public reference. No lifecycle rule adjudicates fraud liability or guarantees chargeback rights. If applicable evidence is missing, abstain; if required facts or intent are unclear, clarify. New shared-state fields or execution controls require C/E contract coordination.

## Evidence, Version and Academic Execution

### Effective Version and Retrieval Context

Version 1.1 applies to synthetic events on or after 2026-10-11; version 1.0 remains the historical reference for 2026-01-01 through 2026-10-10. Do not apply an early-renewal exception or new workflow retroactively. Existing accepted orders retain their confirmed fees and service deadlines unless an explicitly accepted amendment changes them. Different Active-labelled files must be filtered by effective date and version; their status alone does not select the governing version.

Keep policy_id, version, effective_date, business_category, included_intents and synthetic in chunk metadata. Intent-level chunks must preserve the applicable local conditions and retrieve the fee matrix, authentication or security context when necessary. Public reference pages are research provenance, not customer-specific NovaBank evidence. Numeric NovaBank terms are synthetic; reference-bank terms do not override them.

### Simulated Execution and Case Completion

All orders, freezes, cancellations, activations, refunds and renewals are simulated. B supplies evidence, C owns permission and risk decisions, and E owns orchestration, authoritative simulated status and reply assembly. Order states and timestamps described here do not authorize adding executable schema fields without coordination.

Opening a case, replacing a card or refunding a delivery fee does not automatically resolve a complaint. Product recommendations remain blocked while a complaint is OPEN or UNDER_REVIEW. Do not claim that a real banking operation occurred or that a public reference establishes NovaBank legal compliance.
