---
id: visa-2026-q2-007
source: Visa Business News (representative)
source_basis: Visa Stablecoin Settlement Program expansion (announced via VBN Q2 2026)
date: 2026-05-08
network: visa
mandatory: false
synthesized: true
expected_relevance: not_relevant
expected_priority: null
---

# Visa Stablecoin Settlement Pilot — Expanded Availability for Issuing and Acquiring Bank Treasuries

**Effective date:** Opt-in pilot begins 1 July 2026

## Summary

Visa is expanding its stablecoin settlement pilot — first launched in 2023 with USDC on the Solana network — to a broader group of issuing and acquiring banks. Participating institutions can elect to settle inter-bank obligations arising from Visa transaction activity in USDC, EURC, or PYUSD over Ethereum, Solana, Stellar, or Avalanche networks instead of conventional fiat wire transfers.

This is a **bank-treasury-level settlement option**. It does not change anything about the merchant-side or cardholder-side transaction experience.

## What changes for participating banks

Banks that elect to enroll work directly with Visa Treasury Services to:

1. Provision a settlement wallet on the chosen chain via Visa's regulated digital-asset custody partner.
2. Submit standing settlement instructions designating the wallet as the inbound or outbound settlement endpoint for selected currency obligations.
3. Reconcile end-of-cycle settlement netting against the on-chain transfer hash, which Visa surfaces in the existing BASE II settlement reports as a supplementary reference field.

## What does not change

Explicitly out of scope of this pilot:

- ISO 8583 authorization message format.
- Clearing record (TC) format.
- Cardholder-facing transaction experience, currency, or pricing.
- Merchant-facing transaction experience, settlement timing relative to the merchant's deposit account, or merchant statement format.
- Acquirer-merchant settlement (banks continue to settle with their merchants in fiat per the merchant agreement).
- 3DS authentication, tokenization, dispute, or chargeback flows.
- Payment orchestrator, gateway, or PSP integrations of any kind.

## Eligibility

The pilot is open to Visa member banks holding either Issuer or Acquirer designation in the United States, the European Union, or Singapore who meet the digital-asset operational readiness criteria published in the Visa Treasury Services Operational Manual, Annex F. Enrollment is by invitation; banks may express interest via their Visa account manager.

## Press and ecosystem narrative

This expansion is part of Visa's broader strategy to modernize global money movement and reduce treasury operational friction for member banks. It is **not** a customer-facing product, a merchant offering, or a payment method to be supported by acquirers, payment service providers, or payment orchestrators.

## Related references

- Visa Treasury Services Operational Manual, Annex F (Digital Asset Settlement)
- VBN Notice 2025-Q4-2902 (USDC settlement Phase-1 results)
- Visa Cross-Border Solutions whitepaper, Section 8

## Action required

For Visa member banks invited to participate: contact your Visa Treasury Services representative to begin enrollment. **For all other parties — acquirers not invited, payment service providers, gateways, payment orchestrators, merchants, and cardholders — no action is required.**
