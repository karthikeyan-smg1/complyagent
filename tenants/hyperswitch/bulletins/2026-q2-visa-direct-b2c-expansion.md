---
id: visa-2026-q2-011
source: Visa Business News (representative)
source_basis: Visa Direct push-payments framework expansion (Original Credit Transactions, OCT)
date: 2026-04-15
network: visa
mandatory: false
synthesized: true
difficulty: adversarial
failure_mode: surface_overlap
expected_relevance: not_relevant
expected_priority: null
---

# Visa Direct — Expanded B2C Push-Payments Program for Issuing Bank Disbursements

**Effective date:** Opt-in program; first enrolment window opens 1 July 2026

## Summary

Visa is expanding the Visa Direct framework (Original Credit Transactions, OCT) to support a broader set of issuer-driven B2C disbursement use cases — insurance payouts, gig-economy worker payouts, marketplace seller disbursements, and cross-border remittances. The expansion is targeted at **issuing banks** that originate OCT push transactions on behalf of their corporate clients.

This is an **opt-in expansion of a sender-side capability**. It does not alter how Visa transactions are accepted at the cardholder-facing point of sale or in any merchant-acceptance flow.

## What's involved (for issuing banks that elect to participate)

Participating issuing banks must:

1. Enable the new OCT use-case identifier codes in their Visa Direct integration.
2. Submit additional sender-side data on each OCT (sender purpose code, sender business reference, regulatory reporting flag).
3. Implement the EMVCo-aligned tokenization for the recipient PAN where the recipient is on a network-token-enabled Visa card.
4. Update fraud monitoring to incorporate the new OCT-specific risk signals provided by Visa Risk Manager.

## Vocabulary used in this bulletin

This bulletin discusses tokenization, 3DS authentication outcomes (for the sender-side authorization step), authorization_flow context (for the recipient credit), and recurring/scheduled disbursement series. The mentions are within the **sender / issuing bank context** — they describe what the issuing bank must do to originate compliant Visa Direct OCT transactions.

## Who this affects

- **In scope:** Visa member issuing banks that elect to enrol in the expanded Visa Direct program; the corporate clients of those banks that originate B2C disbursements.
- **Not in scope:** Merchant-side card acceptance, including in-store and online card acceptance; payment service providers, payment facilitators, gateways, and payment orchestrators operating in the merchant-acceptance capacity; cardholders receiving funds (no action required).

## What does not change

For merchant-side acceptance flows on Visa rails:

- ISO 8583 authorization message format for the merchant-acceptance leg.
- 3DS authentication requirements at point of sale.
- Stored-credential or recurring-billing tokenization requirements for merchant card-on-file.
- Chargeback or dispute workflows.
- Interchange Reimbursement Fee schedules.

## Related references

- Visa Direct Program Specification v5.0
- VBN Notice 2026-Q1-3251 (initial OCT expansion timeline)
- Visa Risk Manager — OCT signals integration guide

## Action required

Issuing banks interested in participating may contact their Visa account manager to begin enrolment. **For all merchant-side parties — acquirers, gateways, payment service providers, payment facilitators, and payment orchestrators — no action is required.** This program does not introduce any new acceptance-side rule or message-format requirement.
