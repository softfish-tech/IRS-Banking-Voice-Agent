# 固定−6门控：新增32题人工审核表

全部pending；未运行模型或查看分数。8题建议no_evidence、16题supported（含2道多块）、8题unsupported。

审核原则：缺少精确报价与Policy明确不支持服务要分开。no_evidence题的上下文只能解释不能据此确定所问数值，不能把“可说明未知”当作已知该数值。若认为标签或gold不准确，请给出题ID、正确类别和全部必要chunk。

新问法不等于新意图/全新盲测，历史关联仅用于暴露说明，不作为标签依据。固定阈值后首次查询，可作为新问法确认；不应宣称政策事实独立。

## B-GATE6-001 · missing_fee · 建议 no_evidence

The ATM says a separate operator fee may apply. What exact operator surcharge in SGD will its owner charge for my next withdrawal?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：B-EVAL-033

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_cash_withdrawals_master_policy.md) · chunk `NB-v1_1-cash_withdrawal_charge-001`

> Submit a disputed NovaBank ATM fee within 60 calendar days of its posting, using the receipt, separate fee lines and masked reference through the secure account channel. Review costs SGD 0. Staff acknowledge within 1 business day, review the bank calculation within 5 business days after complete evidence and credit approved corrections within 2 business days. Distinguish bank withdrawal fee, conversion fee and operator surcharge. A failed no-cash withdrawal has NovaBank withdrawal fee SGD 0; disputes about actual dispensed cash use the 10-business-day reconciliation decision route. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-002 · missing_fee · 建议 no_evidence

A shop is converting my purchase to SGD before charging the card. What exact percentage markup has that shop built into its DCC rate?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_payments_master_policy.md) · chunk `NB-v1_1-card_payment_fee_charged-001`

> An ordinary NovaBank debit-card purchase has bank purchase fee SGD 0. Only actual NovaBank conversion creates a separate 0.50% FX fee with minimum SGD-equivalent 0.50; sufficient same-currency purchases have no NovaBank conversion fee. Merchant surcharges and DCC margins are not NovaBank purchase fees, and no extra overseas administrative fee is introduced. A correct original FX fee is not automatically refunded when purchase principal is refunded. Review the fee reference, principal, source and charged currencies, conversion record and settlement date before identifying a bank fee error.

审核状态：pending；审批人/日期未记录。

## B-GATE6-003 · missing_fee · 建议 no_evidence

My external debit card issuer charges separately when I fund NovaBank. What precise issuer fee percentage applies to my next SGD 300 top-up?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：B-EVAL-042

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_top_ups_master_policy.md) · chunk `NB-v1_1-top_up_by_card_charge-001`

> Eligible NovaBank manual and automatic SGD debit-card top-ups cost SGD 0 in bank funding fees. The external card issuer may charge independently; retain its statement and masked funding reference and direct issuer-charge enquiries to that issuer. NovaBank cannot quote the issuer tariff or guarantee reimbursement. An issuer charge is not evidence that NovaBank charged a funding fee. Do not import premium-plan, foreign-issued-card or commercial-card fees into the eligible zero-fee product; those unsupported card types do not become eligible by paying a fee.

审核状态：pending；审批人/日期未记录。

## B-GATE6-004 · missing_fee · 建议 no_evidence

I am sending SGD from another Singapore bank into NovaBank. What exact sending-bank fee will that institution charge me?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-top_up_by_bank_transfer_charge-001`

> NovaBank charges SGD 0 to receive supported domestic SGD bank transfers. Incoming bank funding is distinct from debit-card top-ups and does not consume the SGD 5,000 card-funding daily counter. The sending bank sets its own fees and limits; NovaBank cannot quote or refund that bank's charge. Request the sender receipt and fee breakdown when needed. No international, foreign-currency bank receipt or correspondent-fee schedule is introduced. Normal supported receipt is within 60 seconds after sending-bank acceptance, subject to security or funding-origin review.

审核状态：pending；审批人/日期未记录。

## B-GATE6-005 · missing_fee · 建议 no_evidence

The receiving bank has its own charges on a domestic SGD transfer from NovaBank. What exact receiving-bank tariff applies to this beneficiary?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：B-EVAL-061

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-transfer_fee_charged-001`

> NovaBank outgoing domestic SGD transfers, cancellation and routine trace requests have bank fee SGD 0. Outgoing principal is limited to SGD 10,000 per transfer and SGD 20,000 per Singapore calendar day, resetting daily at 00:00 Singapore Time. Inspect the transaction reference, fee descriptor and charging institution before treating a line as a NovaBank fee. Other banks may charge independently; NovaBank does not guarantee or reimburse their charges. Foreign balances do not create an international-transfer product or a SWIFT fee schedule.

审核状态：pending；审批人/日期未记录。

## B-GATE6-006 · missing_fee · 建议 no_evidence

The merchant says my Visa debit payment includes a merchant surcharge. What exact surcharge rate did that merchant contractually agree with its acquirer?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_payments_master_policy.md) · chunk `NB-v1_1-card_payment_fee_charged-001`

> An ordinary NovaBank debit-card purchase has bank purchase fee SGD 0. Only actual NovaBank conversion creates a separate 0.50% FX fee with minimum SGD-equivalent 0.50; sufficient same-currency purchases have no NovaBank conversion fee. Merchant surcharges and DCC margins are not NovaBank purchase fees, and no extra overseas administrative fee is introduced. A correct original FX fee is not automatically refunded when purchase principal is refunded. Review the fee reference, principal, source and charged currencies, conversion record and settlement date before identifying a bank fee error.

审核状态：pending；审批人/日期未记录。

## B-GATE6-007 · missing_fee · 建议 no_evidence

My funding-card issuer listed a separate fee. What is that issuer fee cap per calendar month for NovaBank funding?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：B-EVAL-042

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_top_ups_master_policy.md) · chunk `NB-v1_1-top_up_by_card_charge-001`

> Eligible NovaBank manual and automatic SGD debit-card top-ups cost SGD 0 in bank funding fees. The external card issuer may charge independently; retain its statement and masked funding reference and direct issuer-charge enquiries to that issuer. NovaBank cannot quote the issuer tariff or guarantee reimbursement. An issuer charge is not evidence that NovaBank charged a funding fee. Do not import premium-plan, foreign-issued-card or commercial-card fees into the eligible zero-fee product; those unsupported card types do not become eligible by paying a fee.

审核状态：pending；审批人/日期未记录。

## B-GATE6-008 · missing_fee · 建议 no_evidence

For a transfer funded from another bank, what exact fee discount does that sending bank give its premium customers?

Exact external-provider price/tariff is not specified. Generic warnings or zero NovaBank fees do not provide the requested number. Absence requires human corpus review.

必要gold建议：无；下列只作近邻上下文

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-top_up_by_bank_transfer_charge-001`

> NovaBank charges SGD 0 to receive supported domestic SGD bank transfers. Incoming bank funding is distinct from debit-card top-ups and does not consume the SGD 5,000 card-funding daily counter. The sending bank sets its own fees and limits; NovaBank cannot quote or refund that bank's charge. Request the sender receipt and fee breakdown when needed. No international, foreign-currency bank receipt or correspondent-fee schedule is introduced. Normal supported receipt is within 60 seconds after sending-bank acceptance, subject to security or funding-origin review.

审核状态：pending；审批人/日期未记录。

## B-GATE6-009 · clock_distinction · 建议 supported

I submitted a top-up at 09:10, and the issuer authorised it at 09:25. Which timestamp governs the 72-hour pending limit?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-pending_top_up-002

历史关联：B-EVAL-038, B-EVAL-090

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_top_ups_master_policy.md) · chunk `NB-v1_1-pending_top_up-002`

> NovaBank manual and automatic card top-ups must be released or marked failed within 72 hours from the recorded issuer-authorisation timestamp, not request initiation or NovaBank acceptance. Ownership review does not restart this clock. No duplicate retry or cancellation is offered while pending. After final FAILED status, NovaBank sends release within 1 business day; the issuer may take up to 5 business days from that instruction to display release. If pending exceeds 72 hours, report the reference securely; staff acknowledge within 1 business day and review within 2 business days after complete evidence at SGD 0. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-010 · clock_distinction · 建议 supported

The top-up finally shows FAILED. Does the issuer release window begin with my original request or with the release instruction sent by NovaBank?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-pending_top_up-002

历史关联：B-EVAL-038, B-EVAL-090

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_top_ups_master_policy.md) · chunk `NB-v1_1-pending_top_up-002`

> NovaBank manual and automatic card top-ups must be released or marked failed within 72 hours from the recorded issuer-authorisation timestamp, not request initiation or NovaBank acceptance. Ownership review does not restart this clock. No duplicate retry or cancellation is offered while pending. After final FAILED status, NovaBank sends release within 1 business day; the issuer may take up to 5 business days from that instruction to display release. If pending exceeds 72 hours, report the reference securely; staff acknowledge within 1 business day and review within 2 business days after complete evidence at SGD 0. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-011 · clock_distinction · 建议 supported

A transfer form was saved yesterday but NovaBank accepted the transfer this morning. From which event is the maximum pending period measured?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-pending_transfer-001

历史关联：B-EVAL-058, B-EVAL-090

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-pending_transfer-001`

> NovaBank PENDING means an accepted bank transfer without a final outcome, not completed or failed. Domestic SGD transfers normally complete within 60 seconds; processing or review may remain pending for up to 24 hours from acceptance. Funds are reserved while pending. Inspect the original reference after a confirmation timeout and do not send a duplicate because the recipient has not received money. Security or funding-origin notices may explain unavailable funds. An eligible displayed Cancel action is required for cancellation; chat cannot bypass holds.

审核状态：pending；审批人/日期未记录。

## B-GATE6-012 · clock_distinction · 建议 supported

My card purchase settled on Tuesday; the disputed bank purchase fee posted on Friday. Which date anchors the 60-day fee complaint window?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-card_payment_fee_charged-002

历史关联：B-EVAL-022

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_payments_master_policy.md) · chunk `NB-v1_1-card_payment_fee_charged-002`

> Submit an alleged NovaBank purchase-fee error within 60 calendar days of the disputed fee posting to the NovaBank ledger, not purchase settlement if the dates differ. Securely provide the fee reference, transaction reference, purchase currency, balance used, receipt and conversion record. Staff acknowledge within 1 business day and complete the internal fee review within 5 business days after complete evidence. Review is free; a confirmed NovaBank fee error credits within 2 business days after approval. Accurate disclosed fees and another party's surcharge are not automatically refunded or waived. A fee investigation does not promise a favourable outcome or refund of a correctly charged original FX fee. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-013 · clock_distinction · 建议 supported

Staff finished my identity decision internally on Monday and notified me on Thursday. Which event starts the reconsideration request period?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-unable_to_verify_identity-002

历史关联：B-EVAL-074

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_identity_verification_master_policy.md) · chunk `NB-v1_1-unable_to_verify_identity-002`

> A NovaBank customer disputing a documented final identity-verification decision may request one staff reconsideration within 30 calendar days after the final decision is notified through the secure app or registered contact channel. Internal recording or additional uploads do not start or restart this window. Staff decide within 5 business days after complete evidence. This is distinct from a routine manual identity review, which takes up to 2 business days, and does not permit unlimited automated retries or a new under-age eligibility exception. Provide genuine evidence securely. A pending reconsideration must not be represented as verification success, and the target deadline does not guarantee approval. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-014 · clock_distinction · 建议 supported

The card application was submitted before lunch on Sunday, and processing acceptance occurred on Monday. What event defines delivery Day 0?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-card_delivery_estimate-001

历史关联：B-EVAL-001, B-EVAL-081, B-EVAL-102, B-EVAL-103, B-FILTER-025, B-FILTER-040

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-card_delivery_estimate-001`

> NovaBank physical-card delivery starts at processing acceptance, after verification, entitlement, address, fee approval and an available order slot. Acceptance by 14:00 on a Singapore business day makes that date Day 0; later or non-business-day acceptance uses the next business day. Day 1 is the next business day. Standard shipping costs SGD 0, dispatches by Day 2 and arrives by Day 5. Express shipping costs SGD 10, dispatches by Day 1 and arrives by Day 2. Business days exclude weekends and configured Singapore public holidays. No same-day, overseas, branch-pickup, PO-box or unverified third-party-address delivery is offered.

审核状态：pending；审批人/日期未记录。

## B-GATE6-015 · clock_distinction · 建议 supported

The merchant promised a refund yesterday, but my recognised settled purchase remains unresolved. Does that promise replace settlement as the dispute-intake start event?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-request_refund-002

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_refunds_master_policy.md) · chunk `NB-v1_1-request_refund-002`

> If a merchant refuses or fails to resolve a recognised settled NovaBank purchase, submit a dispute within 60 calendar days of settlement with receipt, reason and evidence of merchant contact. NovaBank acknowledges within 1 business day and targets a decision within 30 calendar days after complete evidence; review costs SGD 0. Only 1 active refund/dispute case per original purchase is permitted. No refund is guaranteed, and an unresolved complaint remains unresolved until authorised resolution. Inform staff if the merchant pays during the dispute to prevent double recovery. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence. Use the secure account channel for account-specific checks and changes.

审核状态：pending；审批人/日期未记录。

## B-GATE6-016 · clock_distinction · 建议 supported

I reported a suspected conversion-fee error, then uploaded the missing documents three days later. Which event starts the five-business-day review target?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-exchange_charge-002

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_currency_exchange_master_policy.md) · chunk `NB-v1_1-exchange_charge-002`

> Submit an alleged NovaBank conversion-fee error within 60 calendar days of posting with the relevant transaction and calculation evidence through the secure account channel. Review costs SGD 0. Staff acknowledge within 1 business day, review within 5 business days after complete evidence and credit a confirmed error within 2 business days after approval. Accurate disclosed fees are not automatically waived, and another provider's fee is not automatically refunded. Review targets do not guarantee approval or reimbursement; distinguish a fee calculation error from ordinary quote movement. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-017 · applicability · 建议 unsupported

I already use the disposable card for one approved purchase. May I make a second independent purchase if the first one has not settled?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-disposable_card_limits-001

历史关联：B-EVAL-068, B-FILTER-038

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_virtual_cards_master_policy.md) · chunk `NB-v1_1-disposable_card_limits-001`

> A NovaBank disposable card permits exactly 1 approved online purchase of at most SGD-equivalent 500; approval consumes it before settlement, while a failed authorisation does not. It expires after 24 hours unused. Subscriptions, recurring payments, deposits, preauthorisations, wallet enrolment, ATM use, zero-value verification and multiple independent authorisations are unsupported, even at the same merchant. Disposable spending also consumes shared SGD-equivalent 5,000 per-purchase and 10,000 daily account caps; the stricter 500 limit applies. Public limit information is immediate at SGD 0.

审核状态：pending；审批人/日期未记录。

## B-GATE6-018 · applicability · 建议 unsupported

Can I enrol a disposable virtual card into my phone wallet instead of using its number online?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-disposable_card_limits-001

历史关联：B-EVAL-068, B-FILTER-038

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_virtual_cards_master_policy.md) · chunk `NB-v1_1-disposable_card_limits-001`

> A NovaBank disposable card permits exactly 1 approved online purchase of at most SGD-equivalent 500; approval consumes it before settlement, while a failed authorisation does not. It expires after 24 hours unused. Subscriptions, recurring payments, deposits, preauthorisations, wallet enrolment, ATM use, zero-value verification and multiple independent authorisations are unsupported, even at the same merchant. Disposable spending also consumes shared SGD-equivalent 5,000 per-purchase and 10,000 daily account caps; the stricter 500 limit applies. Public limit information is immediate at SGD 0.

审核状态：pending；审批人/日期未记录。

## B-GATE6-019 · applicability · 建议 unsupported

The ATM displays the Visa logo. Can I withdraw cash using only a NovaBank virtual card or wallet token, without the physical card?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-atm_support-001

历史关联：B-EVAL-027, B-EVAL-082, B-EVAL-106

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_cash_withdrawals_master_policy.md) · chunk `NB-v1_1-atm_support-001`

> NovaBank cash withdrawal requires an active physical Visa debit card with valid PIN at a compatible Visa/PLUS ATM dispensing SGD, USD, EUR, GBP or AUD. Virtual cards, wallet tokens, disposable cards and ATM deposits are unsupported. Principal limits are SGD-equivalent 500 per withdrawal and 1,000 per Singapore calendar day; each completed withdrawal costs SGD 2, with operator fees disclosed separately. Denominations, machine cash stock, operator limits and risk controls may further restrict acceptance. A Visa/PLUS logo is not guaranteed approval. Public compatibility information is immediate at SGD 0.

审核状态：pending；审批人/日期未记录。

## B-GATE6-020 · applicability · 建议 unsupported

I qualify for a spare card. May I give that spare to my spouse to spend from my account?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-getting_spare_card-001

历史关联：B-EVAL-005, B-EVAL-079, B-FILTER-029

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-getting_spare_card-001`

> A NovaBank spare physical card requires 1 non-retired main card, no existing spare, no issuance restriction and no unfulfilled dispatch order. At most 1 spare is allowed for the same customer. It has its own number and PIN but shares the balance and existing purchase and ATM allowances. It cannot be lent to a spouse or child, bypass security restrictions or increase account limits. An active spare may continue during ordinary main-card renewal only without account-wide or spare-specific restrictions; suspected account compromise requires security clearance. Losing a spare uses replacement, not another spare entitlement. Accepted order confirmation takes up to 1 minute.

审核状态：pending；审批人/日期未记录。

## B-GATE6-021 · applicability · 建议 unsupported

The merchant accepts only American Express. Can NovaBank issue my next debit card on that network?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-visa_or_mastercard-001

历史关联：B-EVAL-013, B-FILTER-034

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_usage_and_access_master_policy.md) · chunk `NB-v1_1-visa_or_mastercard-001`

> All NovaBank-issued physical, reusable virtual and disposable debit cards use Visa. Network choice costs SGD 0 because it is fixed; switching to Mastercard, American Express or another network is unsupported. An external eligible Singapore-issued Visa or Mastercard debit card may fund SGD top-ups, but that does not mean NovaBank issues Mastercard. A Mastercard-only merchant is not made compatible by replacing a NovaBank card. Public network information is immediate without authentication at SGD 0; staff clarify a network enquiry within 2 business days. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-022 · applicability · 建议 unsupported

I hold foreign currency in NovaBank. Does that let me register an overseas bank beneficiary and send a foreign-currency bank transfer?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-beneficiary_not_allowed-001

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-beneficiary_not_allowed-001`

> A NovaBank beneficiary must be a supported Singapore bank account accepting SGD and must pass security checks. Verify receiving bank, account identifier and active destination; international or foreign-currency payment instructions are rejected. A nickname change cannot fix a closed account, bank mismatch or blocked destination. Public eligibility guidance and adding a supported beneficiary cost SGD 0. Formatting or alleged mistaken rejection can be reviewed within 2 business days after masked evidence. Do not expose security criteria, use pass-through beneficiaries or remove a suspected-scam block merely to complete payment. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-023 · applicability · 建议 unsupported

Can I scan a cheque in the NovaBank app rather than deposit it at a counter?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-top_up_by_cash_or_cheque-001

历史关联：B-EVAL-070, B-FILTER-039

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_cash_and_cheque_deposits_master_policy.md) · chunk `NB-v1_1-top_up_by_cash_or_cheque-001`

> NovaBank accepts neither cash nor cheque deposits: both accepted principal limits are SGD 0, with 0 authorised collection agents, deposit ATMs, counters, mail-in channels or cheque-image deposit services. Unsupported requests are rejected immediately at SGD 0, and no deposit clearing or crediting SLA exists. Do not mail cash or cheques or hand funds to a purported agent. A NovaBank-branded deposit receipt or claimed collection agent requires immediate 24/7 security escalation; routine clarification within 2 business days is not a cheque-clearing promise. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。

## B-GATE6-024 · applicability · 建议 unsupported

I am willing to pay extra for my replacement. Can NovaBank send the physical card abroad?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-card_delivery_estimate-001

历史关联：B-EVAL-001, B-EVAL-081, B-EVAL-102, B-EVAL-103, B-FILTER-025, B-FILTER-040

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-card_delivery_estimate-001`

> NovaBank physical-card delivery starts at processing acceptance, after verification, entitlement, address, fee approval and an available order slot. Acceptance by 14:00 on a Singapore business day makes that date Day 0; later or non-business-day acceptance uses the next business day. Day 1 is the next business day. Standard shipping costs SGD 0, dispatches by Day 2 and arrives by Day 5. Express shipping costs SGD 10, dispatches by Day 1 and arrives by Day 2. Business days exclude weekends and configured Singapore public holidays. No same-day, overseas, branch-pickup, PO-box or unverified third-party-address delivery is offered.

审核状态：pending；审批人/日期未记录。

## B-GATE6-025 · fee_control · 建议 supported

For an eligible manual SGD debit-card top-up, what funding fee does NovaBank itself charge, excluding my issuer charges?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-top_up_by_card_charge-001

历史关联：B-EVAL-042

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_top_ups_master_policy.md) · chunk `NB-v1_1-top_up_by_card_charge-001`

> Eligible NovaBank manual and automatic SGD debit-card top-ups cost SGD 0 in bank funding fees. The external card issuer may charge independently; retain its statement and masked funding reference and direct issuer-charge enquiries to that issuer. NovaBank cannot quote the issuer tariff or guarantee reimbursement. An issuer charge is not evidence that NovaBank charged a funding fee. Do not import premium-plan, foreign-issued-card or commercial-card fees into the eligible zero-fee product; those unsupported card types do not become eligible by paying a fee.

审核状态：pending；审批人/日期未记录。

## B-GATE6-026 · fee_control · 建议 supported

What does NovaBank itself charge to receive an eligible domestic SGD bank transfer, regardless of the sending bank tariff?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-top_up_by_bank_transfer_charge-001

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-top_up_by_bank_transfer_charge-001`

> NovaBank charges SGD 0 to receive supported domestic SGD bank transfers. Incoming bank funding is distinct from debit-card top-ups and does not consume the SGD 5,000 card-funding daily counter. The sending bank sets its own fees and limits; NovaBank cannot quote or refund that bank's charge. Request the sender receipt and fee breakdown when needed. No international, foreign-currency bank receipt or correspondent-fee schedule is introduced. Normal supported receipt is within 60 seconds after sending-bank acceptance, subject to security or funding-origin review.

审核状态：pending；审批人/日期未记录。

## B-GATE6-027 · fee_control · 建议 supported

What is the NovaBank fee for an outgoing domestic SGD transfer and a routine trace request?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-transfer_fee_charged-001

历史关联：B-EVAL-061

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_bank_transfers_master_policy.md) · chunk `NB-v1_1-transfer_fee_charged-001`

> NovaBank outgoing domestic SGD transfers, cancellation and routine trace requests have bank fee SGD 0. Outgoing principal is limited to SGD 10,000 per transfer and SGD 20,000 per Singapore calendar day, resetting daily at 00:00 Singapore Time. Inspect the transaction reference, fee descriptor and charging institution before treating a line as a NovaBank fee. Other banks may charge independently; NovaBank does not guarantee or reimburse their charges. Foreign balances do not create an international-transfer product or a SWIFT fee schedule.

审核状态：pending；审批人/日期未记录。

## B-GATE6-028 · fee_control · 建议 supported

An ordinary debit-card purchase uses sufficient balance in the purchase currency. What NovaBank purchase and conversion fees apply?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-card_payment_fee_charged-001

历史关联：未发现共享gold

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_payments_master_policy.md) · chunk `NB-v1_1-card_payment_fee_charged-001`

> An ordinary NovaBank debit-card purchase has bank purchase fee SGD 0. Only actual NovaBank conversion creates a separate 0.50% FX fee with minimum SGD-equivalent 0.50; sufficient same-currency purchases have no NovaBank conversion fee. Merchant surcharges and DCC margins are not NovaBank purchase fees, and no extra overseas administrative fee is introduced. A correct original FX fee is not automatically refunded when purchase principal is refunded. Review the fee reference, principal, source and charged currencies, conversion record and settlement date before identifying a bank fee error.

审核状态：pending；审批人/日期未记录。

## B-GATE6-029 · fee_control · 建议 supported

For a replacement caused by my own card loss with express delivery, what separate issuance and shipping charges apply, and which event establishes delivery Day 0?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-order_physical_card-002, NB-v1_1-card_delivery_estimate-001

历史关联：B-EVAL-079

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-order_physical_card-002`

> NovaBank physical first-card issuance and scheduled or permitted early renewal cost SGD 0. Spare cards, customer-loss, damage, verified credential-exposure, ATM-retention replacements and reissuance after an activation deadline cost SGD 15. Confirmed courier-loss or bank production-error replacement issuance costs SGD 0. Delivery is charged separately: standard SGD 0 or express SGD 10. All amounts include simulated taxes. If confirmed bank or courier fault misses an original paid express deadline, refund that SGD 10 surcharge within 3 business days after confirmation and provide any required replacement express delivery without another surcharge. A supplied spare's issuance fee remains payable. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-card_delivery_estimate-001`

> NovaBank physical-card delivery starts at processing acceptance, after verification, entitlement, address, fee approval and an available order slot. Acceptance by 14:00 on a Singapore business day makes that date Day 0; later or non-business-day acceptance uses the next business day. Day 1 is the next business day. Standard shipping costs SGD 0, dispatches by Day 2 and arrives by Day 5. Express shipping costs SGD 10, dispatches by Day 1 and arrives by Day 2. Business days exclude weekends and configured Singapore public holidays. No same-day, overseas, branch-pickup, PO-box or unverified third-party-address delivery is offered.

审核状态：pending；审批人/日期未记录。

## B-GATE6-030 · fee_control · 建议 supported

The courier has confirmed loss, and I choose standard delivery for the replacement. What issuance and delivery fees apply, and what event starts the replacement delivery clock?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-card_arrival-002, NB-v1_1-card_delivery_estimate-001

历史关联：B-EVAL-081

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-card_arrival-002`

> Confirmed NovaBank courier loss, misdelivery or production error requires retirement of the affected card and closure of its order before replacement acceptance. Replacement issuance and standard delivery cost SGD 0; express delivery costs SGD 10 unless a confirmed fault-related missed paid express deadline grants free express replacement and refund of the original surcharge within 3 business days after confirmation. A paid spare issuance fee remains attached to the entitlement. Replacement does not resolve an associated transaction dispute. A temporary freeze may be released after verified receipt and ownership checks; permanent cancellation is irreversible. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence. Use the secure account channel for account-specific checks and changes.

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_card_lifecycle_master_policy.md) · chunk `NB-v1_1-card_delivery_estimate-001`

> NovaBank physical-card delivery starts at processing acceptance, after verification, entitlement, address, fee approval and an available order slot. Acceptance by 14:00 on a Singapore business day makes that date Day 0; later or non-business-day acceptance uses the next business day. Day 1 is the next business day. Standard shipping costs SGD 0, dispatches by Day 2 and arrives by Day 5. Express shipping costs SGD 10, dispatches by Day 1 and arrives by Day 2. Business days exclude weekends and configured Singapore public holidays. No same-day, overseas, branch-pickup, PO-box or unverified third-party-address delivery is offered.

审核状态：pending；审批人/日期未记录。

## B-GATE6-031 · fee_control · 建议 supported

If the merchant already converts the purchase principal into SGD through DCC, does NovaBank charge an FX conversion fee on that principal?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-exchange_charge-001

历史关联：B-EVAL-019

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_currency_exchange_master_policy.md) · chunk `NB-v1_1-exchange_charge-001`

> NovaBank conversion costs the greater of source principal multiplied by 0.005 and the quote-time source-currency equivalent of SGD 0.50, rounded half-up to 2 decimal places and charged separately in source currency. The rate applies to in-app exchange, converted purchases and converted ATM withdrawals. There is no weekend surcharge or extra NovaBank FX spread. Sufficient same-currency card purchases have no FX fee. When a merchant or ATM converts into SGD through DCC, NovaBank performs no FX and charges no FX fee on that principal; a completed ATM withdrawal still has its separate SGD 2 bank fee.

审核状态：pending；审批人/日期未记录。

## B-GATE6-032 · fee_control · 建议 supported

My ATM attempt was declined and dispensed no cash. What is NovaBank bank withdrawal fee for that failed attempt?

The listed chunk explicitly defines the requested fee, clock start, or restriction. Human reviewer must confirm sufficiency and add required alternative/missing chunks if necessary.

必要gold建议：NB-v1_1-declined_cash_withdrawal-002

历史关联：B-EVAL-030

来源：[Policy](../../novabank_category_master_policies_enriched_v1_1/policies/NovaBank_cash_withdrawals_master_policy.md) · chunk `NB-v1_1-declined_cash_withdrawal-002`

> A declined no-cash NovaBank ATM attempt has bank withdrawal fee SGD 0 and must not be represented as a completed withdrawal. An associated authorisation hold settles or reverses within 3 calendar days. Do not repeatedly withdraw to compensate for funds reserved or debited without cash. Provide ATM identifier, time, amount, reference and receipt if available; staff acknowledge within 1 business day. A cash-dispensing discrepancy requires evidence-based reconciliation, with approved corrections only after review; an operator's charge is assessed separately from NovaBank's withdrawal fee. Business days exclude weekends and configured Singapore public holidays; counting begins on the next business day after the stated event. Review clocks require complete evidence.

审核状态：pending；审批人/日期未记录。
