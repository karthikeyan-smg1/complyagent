---
id: visa-2026-q1-001
source: Visa Business News (representative)
source_basis: Visa CIT/MIT framework, AFT (MCC 6012/6051) acquirer rules
date: 2026-01-15
network: visa
mandatory: true
synthesized: true
expected_relevance: relevant
expected_priority: P1
---

# Visa CIT/MIT Indicator Update — Mandatory Transaction Type Reporting for Account Funding Transactions

**Effective date:** 1 October 2026

## Summary

Visa is updating the Cardholder-Initiated Transaction (CIT) and Merchant-Initiated Transaction (MIT) framework to require additional sub-type indicators on Account Funding Transactions (AFT). All acquirers processing AFT transactions on Visa rails must populate the new CIT/MIT indicator field with the correct sub-type code for each transaction submitted for authorization and clearing.

This change applies to all transactions identified by AFT-eligible Merchant Category Codes (MCCs), including but not limited to MCC 6012 (financial institutions — merchandise and services), MCC 6051 (non-financial institutions — foreign currency, money orders, scrip, and travelers cheques), and MCC 4829 (wire transfer money orders).

## Acquirer requirements

Acquirers must, by the effective date:

1. **Populate the CIT/MIT indicator** in the authorization request (Field 60.8) with one of:
   - `C01` — CIT, cardholder present
   - `C02` — CIT, cardholder not present, recurring
   - `C03` — CIT, cardholder not present, first-time
   - `M01` — MIT, scheduled (subsequent transaction in a recurring series)
   - `M02` — MIT, unscheduled (account top-up, automatic reload)
2. **Pass the AFT-specific sub-type indicator** in Field 63.3 identifying the funding purpose (wallet load, person-to-person transfer, prepaid reload, debt repayment).
3. **Surface the indicator in clearing records** (TC 05, 06, 07 messages) using the same sub-type code as the corresponding authorization.
4. **Reject downstream transactions** that arrive without a valid CIT/MIT + AFT sub-type pair after the effective date — these will receive Visa response code `R65` and a non-compliance assessment.

## Issuer-side considerations

Issuers are encouraged to use the new sub-type indicator for transaction risk scoring and authorization decisioning, but this is not mandated in the first cycle. A subsequent bulletin in Q3 2026 will address issuer mandatory handling.

## Penalties for non-compliance

Beginning 1 November 2026, transactions missing the required indicator pair will be subject to a non-compliance assessment of USD 0.025 per transaction, billed via the standard Visa Compliance Assessment process. Repeat non-compliance over a 90-day window may result in escalation per the Visa Core Rules Section 1.10.

## Testing window

Visa is providing a sandbox-only testing window from 1 May 2026 through 31 August 2026 via Visa Acceptance Testing Services (VATS). Acquirers are strongly encouraged to validate end-to-end CIT/MIT + AFT flag handling before the production cutover.

## Related references

- Visa Core Rules, Section 5.4 (Transaction Type Identification)
- Visa Acquirer Risk Standards, Annex C (Account Funding Programs)
- VBN Notice 2025-Q4-2186 (initial AFT framework announcement)

## Action required

Acquirers, gateways, and payment orchestrators handling AFT-eligible transaction flows must implement the indicator population across authorization, clearing, and chargeback retrieval paths before 1 October 2026.
