---
id: visa-2026-q2-002
source: Visa Business News (representative)
source_basis: EMV 3DS 2.3 specification, Visa Secure program rules, PSD2 SCA exemption flags
date: 2026-04-02
network: visa
mandatory: true
synthesized: true
difficulty: clear
expected_relevance: relevant
expected_priority: P0
---

# Visa Secure — Mandatory Support for EMV 3DS 2.3 Authentication Indicators

**Effective date:** 15 October 2026 (advisory window opens 1 July 2026)

## Summary

Visa Secure is updating the supported EMV 3-D Secure protocol version to 2.3 across the Visa Directory Server (Visa DS). All merchants, payment service providers, gateways, and acquirers participating in Visa Secure authentication flows must support the EMV 3DS 2.3 message format and the expanded set of authentication exemption indicators by the effective date.

EMV 3DS 2.2 will continue to be accepted by the Visa DS through 31 March 2027 to provide a migration window, after which all authentication traffic must arrive in 2.3 format.

## What changes in 2.3

1. **Expanded device data fields.** The AReq message adds 14 new optional fields for device/browser fingerprinting, supporting more granular risk-based authentication and frictionless flow decisions.
2. **New SCA exemption indicators.** A standardised set of exemption codes is introduced, covering:
   - Low-Value Transaction (LVT) — under EUR 30
   - Trusted Beneficiary (whitelisted by issuer)
   - Recurring Payment (with prior cardholder authentication on first instance)
   - Secure Corporate Payment (B2B with dedicated payment processes)
   - Transaction Risk Analysis (TRA) — issued by acquirer with fraud-rate evidence
   - Delegated Authentication (issuer delegates to a qualified merchant/PSP)
3. **Expanded `acsRefNumber` and `acsTransID` formats.** Length and character set expanded — implementations parsing or storing these IDs must accept the new format without truncation.
4. **Mandatory `messageExtension` support** for issuer-defined data. Merchants must propagate unchanged.
5. **3RI (3DS Requestor Initiated) extension.** Required for merchant-initiated authentication outside the cardholder's checkout flow (e.g., delayed authorization, deferred-shipment scenarios).

## Acceptance-side (merchant / PSP / gateway) requirements

By the effective date, the acceptance side must:

1. **Send AReq in 2.3 format** with all mandatory fields populated.
2. **Receive and handle ARes / RReq / CReq / CRes** in 2.3 format including the new exemption indicators.
3. **Propagate Cardholder Authentication Verification Value (CAVV)** received in the ARes/RReq message in the subsequent authorization request without modification.
4. **Honor exemption requests** signalled by the issuer and adapt the merchant flow accordingly (skip step-up challenge).
5. **Log and surface** authentication outcome codes to the merchant for reconciliation and dispute defense.

## Liability and chargeback implications

Transactions correctly authenticated under 2.3 with a valid CAVV continue to receive Visa Secure liability shift protection (chargeback reason code 10.5 will be invalid for the issuer). Transactions that fail authentication or are not attempted but would have been eligible may forfeit liability shift after the effective date.

## Testing

Visa DS 2.3 test endpoints are available immediately. Visa strongly recommends end-to-end testing using both browser-flow and app-flow simulators provided through the Visa Developer Center.

## Related references

- EMV Co specification: EMV 3DS 2.3.1 (October 2022, with 2025 amendments)
- Visa Secure Program Rules, Section 4 (Protocol Versioning and Migration)
- PSD2 / RTS on Strong Customer Authentication (EU)

## Action required

All Visa Secure participants — merchants, PSPs, payment orchestrators, gateways, and acquirers — must implement 2.3 protocol support before the effective date. Authentication flows must continue to function correctly during the 2.2 / 2.3 dual-acceptance window from 1 July 2026 through 31 March 2027.
