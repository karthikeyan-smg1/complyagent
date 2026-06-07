---
id: visa-2026-q3-013
source: Visa Business News (representative)
source_basis: Visa BASE II clearing endpoint TLS / address migration
date: 2026-07-25
network: visa
mandatory: true
synthesized: true
difficulty: adversarial
failure_mode: surface_overlap
expected_relevance: not_relevant
expected_priority: null
---

# BASE II Clearing Endpoint — Mandatory Migration to New TLS Address Window

**Effective date:** Migration window opens 1 September 2026; legacy endpoint sunsets 31 March 2027

## Summary

Visa is migrating the BASE II clearing endpoint — the secure file transfer destination where settlement files (TC 05, 06, 07 clearing records) are exchanged between Visa and direct-connected institutions — to a new TLS 1.3-only address. The legacy endpoint at `bii.visa.com:5000` will be sunset on 31 March 2027.

This is an **infrastructure migration on Visa's clearing-network side**. It governs how directly-connected institutions exchange clearing files with Visa. It does not change clearing record content, format, or the acceptance- and authorization-side handling that produces those records.

## Who must migrate

BASE II is a direct connection between an institution and Visa's clearing network. The institutions that hold a BASE II credential, and therefore must perform the endpoint migration, are:

- **Direct-connected acquiring banks** — banks that submit their merchants' clearing records to Visa directly via BASE II.
- **Direct-connected issuing banks** — banks that consume Visa-side clearing records for their cardholder accounts.
- **Direct-connected processors** — third-party processors (e.g., FIS, Fiserv, Worldpay, TSYS, Visa DPS) that operate a BASE II connection on behalf of an acquiring or issuing bank.

These institutions must:

1. Update their BASE II client configuration to point at the new TLS 1.3 endpoint.
2. Provision new TLS client certificates issued via the Visa Certificate Authority before the legacy endpoint sunset.
3. Validate end-to-end clearing-file submission against the new endpoint during the migration window.

## What does not change

The endpoint migration does not change:

- ISO 8583 authorization message format.
- Clearing record (TC 05, 06, 07) content or schema.
- The authorization, settlement, or chargeback business logic that produces clearing records.
- 3DS authentication, tokenization, or stored-credential handling at point of sale.
- Any acceptance-side processing that runs upstream of the BASE II handoff.

The migration is a connection-layer change, not a business-rule or message-format change.

## Related references

- BASE II Connectivity Specification v4.1
- Visa Certificate Authority — Endpoint Migration Procedures
- VBN Notice 2026-Q2-3310 (initial migration timeline)

## Action required

Direct-connected acquirers, issuers, and their direct-connected processors must complete the BASE II endpoint migration before 31 March 2027 to maintain their clearing-record exchange with Visa.
