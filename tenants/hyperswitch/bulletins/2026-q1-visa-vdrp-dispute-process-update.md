---
id: visa-2026-q1-004
source: Visa Business News (representative)
source_basis: Visa Dispute Monitoring Program (VDMP) and Visa Dispute Resolution Process (VDRP) rules
date: 2026-03-05
network: visa
mandatory: true
synthesized: true
difficulty: clear
expected_relevance: relevant
expected_priority: P1
---

# Visa Dispute Resolution Process — Pre-Arbitration Evidence Format Update

**Effective date:** 1 July 2026

## Summary

Visa is updating the evidence-format requirements for pre-arbitration disputes filed under Visa Dispute Resolution Process (VDRP) reason codes 10.4 (Other Fraud — Card-Absent Environment) and 13.1 (Merchandise / Services Not Received). Acquirers and gateways representing merchants in dispute responses must submit evidence packets conforming to the new Visa Evidence Pack v4 schema for any dispute initiated on or after the effective date.

## What changes

The current PDF-only evidence channel is being replaced with a structured JSON envelope plus referenced artifact attachments. Evidence packets must include:

1. **`transaction_context`** — the full ISO 8583 authorization metadata (response code, AVS, CVV2 result, 3DS authentication outcome, network token cryptogram verification) for the disputed authorization.
2. **`fulfilment_evidence`** — for reason code 13.1: shipment carrier, tracking number, delivery confirmation timestamp, and the delivery address last-4 matching the cardholder billing address. For reason code 10.4: device fingerprint, IP geolocation, login session timestamp, and behavioural risk score from the merchant's fraud system.
3. **`stored_credential_indicators`** — for any MIT chain disputes: CIT/MIT chain reference, original CIT authorization ID, MIT sequence number.
4. **`compelling_evidence_3_0_fields`** — the four CE 3.0 markers (matching IP across prior undisputed transactions, matching device ID, matching delivery address, matching cardholder telephone) where the merchant claims CE 3.0 protection.

The structured fields are validated by the Visa Resolve Online (VROL) intake API and must be machine-extractable; freeform PDF narratives no longer count as primary evidence.

## Acquirer and orchestrator requirements

Acquirers and orchestrators participating in dispute response on behalf of merchants must:

1. Generate Visa Evidence Pack v4 JSON envelopes during the 30-day pre-arbitration response window.
2. Persist the data points listed in §`transaction_context` and §`fulfilment_evidence` for at least 18 months from the original authorization, so they can be retrieved during the response window.
3. Update VROL API integration to use the new `/disputes/{id}/evidence` endpoint and reject the legacy `/disputes/{id}/upload` endpoint (deprecated 1 October 2026).

## Issuer requirements

Issuers will be required to use the structured fields when evaluating dispute responses, and may not refuse a representment solely because the legacy PDF format is absent.

## Penalties for non-compliance

Pre-arbitration responses submitted in the legacy format after the effective date will be auto-rejected by VROL and the dispute will progress to arbitration with no merchant evidence on file.

## Related references

- Visa Core Rules, Section 11 (Dispute Resolution)
- Visa Compelling Evidence 3.0 Implementation Guide
- VROL API Specification v6.1

## Action required

Payment orchestrators with chargeback-handling integrations must update their dispute response pipeline to emit the Evidence Pack v4 JSON envelope, persist the required transaction context, and migrate from the legacy VROL upload endpoint before 1 July 2026.
