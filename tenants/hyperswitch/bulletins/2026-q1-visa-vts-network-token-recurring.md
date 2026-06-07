---
id: visa-2026-q1-002
source: Visa Business News (representative)
source_basis: Visa Token Service (VTS) and stored-credential framework; PSD2 Article 4(35)
date: 2026-02-10
network: visa
mandatory: true
synthesized: true
difficulty: clear
expected_relevance: relevant
expected_priority: P0
---

# Visa Token Service — Mandatory Network Tokenization for Stored Recurring Credentials

**Effective date:** 1 April 2027 (with a phased acquirer migration starting Q3 2026)

## Summary

Visa is moving all stored credentials for recurring and unscheduled cardholder-initiated transactions onto the Visa Token Service (VTS). After the effective date, acquirers and payment orchestrators submitting subsequent transactions in a recurring series using a stored Primary Account Number (PAN) without a corresponding network token will receive a hard decline (response code `R20` — *stored credential requires network token*).

This applies to all card-on-file flows on Visa rails — subscriptions, account top-ups, installment plans, wallet reloads, in-app purchase MIT transactions, and merchant-initiated retries of failed authorizations.

## Acquirer and orchestrator requirements

By the effective date, acquirers and orchestrators must:

1. **Provision a network token** for every stored Visa PAN via the VTS Token Provisioning API before the first MIT transaction is submitted. Tokens must be requested with the correct Token Requestor ID (TRID) for the merchant.
2. **Submit the network token (DPAN) in Field 2** of the ISO 8583 authorization request for all subsequent MIT transactions. The original PAN must not be re-submitted after initial tokenization.
3. **Pass the cryptogram (TAVV)** in Field 55 for each MIT transaction. The cryptogram must be generated per transaction via the VTS Cryptogram Service.
4. **Maintain token lifecycle handlers** for the lifecycle events surfaced via VTS webhook notifications: `token_suspended`, `token_resumed`, `token_deleted`, `pan_updated`, `expiry_updated`. PAN updates and expiry changes must be reflected in stored credential records without cardholder re-entry.
5. **Stop accepting raw PAN-on-file** for new merchant onboarding from 1 January 2027.

## Cardholder-initiated transactions

CIT transactions (one-time purchases initiated by the cardholder in real time) are out of scope for this mandate and may continue to use either the PAN or a network token at the merchant's discretion.

## Penalties for non-compliance

After the effective date, non-token MIT authorization attempts will:

- Receive response code `R20` and be declined at the network.
- Be excluded from Visa Compelling Evidence 3.0 (CE 3.0) chargeback dispute evidence.
- Count toward the merchant's MIT Authorization Quality Index (MAQI); merchants below threshold may face acquirer-passed assessments under the Visa Acquirer Monitoring Program.

## Testing window

VTS sandbox migration support is available now via the Visa Developer Portal. Visa is offering a complimentary VTS Migration Readiness Review for the top 200 acquirers and orchestrators by transaction volume; orchestrators should contact their Visa account manager to enrol.

## Related references

- Visa Core Rules, Section 5.6 (Stored Credential Transactions)
- Visa Token Service Specification v3.2
- VBN Notice 2025-Q3-1842 (initial VTS migration timeline)

## Action required

Payment orchestrators with merchants running recurring billing on Visa rails must implement VTS tokenization across the full stored-credential lifecycle — provisioning, cryptogram retrieval, token lifecycle webhooks, and MIT submission — well in advance of 1 April 2027.
