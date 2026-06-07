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

## Who this affects

The program is open to Visa member issuing banks that elect to enrol in the expanded Visa Direct OCT framework, and to the corporate clients of those banks that originate B2C disbursements (insurance carriers, gig-economy platforms, marketplace operators settling with their sellers, money-transfer operators).

The enrolment, the operational requirements, and the new Visa Direct schema apply to the issuing-bank side of the Visa rails — the bank that originates the OCT credit transaction on behalf of its corporate client.

## Related references

- Visa Direct Program Specification v5.0
- VBN Notice 2026-Q1-3251 (initial OCT expansion timeline)
- Visa Risk Manager — OCT signals integration guide

## Action required

Visa member issuing banks interested in participating in the expanded Visa Direct B2C program may contact their Visa Direct account manager to begin enrolment. Participating issuing banks must complete the OCT use-case identifier integration, the sender-side data submission, and the EMVCo recipient-PAN tokenization before originating compliant Visa Direct OCT transactions under the expanded program.
