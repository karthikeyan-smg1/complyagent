---
id: visa-2026-q2-009
source: Visa Business News (representative)
source_basis: Visa India Interchange Reimbursement Fee schedule update
date: 2026-04-30
network: visa
mandatory: true
synthesized: true
difficulty: clear
expected_relevance: relevant
expected_priority: P2
---

# India Domestic Interchange Reimbursement Fee — Rate Adjustment for Card-Not-Present Consumer Credit Transactions

**Effective date:** 1 July 2026

## Summary

Visa is adjusting the domestic Interchange Reimbursement Fee (IRF) schedule for India-domiciled card-not-present (CNP) consumer credit transactions. The new schedule introduces a tiered MCC-based structure, replacing the flat-rate CNP consumer credit fee that has been in place since the 2022 RBI-aligned IRF revision.

This is a **fee schedule adjustment**, not a rule change. Acquirers, gateways, and payment orchestrators that calculate or pass on interchange fees in any form must update fee calculation tables and merchant statements to reflect the new schedule.

## Rate changes

The single flat rate of 1.45% per CNP consumer credit transaction is replaced with the following tiered MCC schedule:

| MCC band | Examples | New IRF |
| --- | --- | --- |
| Essential services | 4900 (utilities), 8062 (hospitals), 8211 (education) | 0.85% |
| Standard retail | 5411 (grocery), 5651 (apparel), 5732 (electronics) | 1.45% (unchanged) |
| Travel and hospitality | 4511 (airlines), 7011 (lodging), 4722 (travel agencies) | 1.75% |
| High-risk merchant categories | 7995 (gambling), 5933 (pawnshops), select MCCs per Annex G | 2.10% |

The full MCC-to-band mapping is published in the Visa India IRF Schedule v2026.2 (Annex A).

## What is required

Acquirers, gateways, and orchestrators that compute or display interchange fees must, by the effective date:

1. Load the v2026.2 MCC-to-IRF mapping into the fee calculation engine. The current flat 1.45% lookup must not remain in use for India domestic CNP consumer credit traffic after 1 July 2026.
2. Reflect the new tier in merchant fee statements for the August 2026 billing cycle.
3. For acquirers that pass interchange through to merchants on a cost-plus basis: ensure merchant-statement IRF lines correctly identify the MCC band applied per transaction.
4. For acquirers that bundle interchange into a blended merchant rate: re-evaluate blended-rate margins; no action is required on per-transaction calculation, but margin assumptions may shift.

## What does not change

This schedule update does not change:

- Authorization or clearing message formats.
- The chargeback or dispute process.
- 3DS authentication requirements.
- Stored-credential or tokenization handling.
- Card-present consumer credit IRF (covered separately under MDR Schedule M).
- Cross-border IRF (covered separately under Cross-Border IRF Schedule X).

## Related references

- Visa India IRF Schedule v2026.2
- Visa Acquirer Pricing Guide, Section 6 (India domestic)
- RBI Master Direction on Card Transactions (DPSS.CO.PD No. 1064 / 2022)

## Action required

Acquirers, gateways, and orchestrators that calculate or display interchange fees for India domestic CNP consumer credit transactions must load the new MCC-to-IRF mapping and update merchant statements before 1 July 2026.
