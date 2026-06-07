---
id: visa-2026-q3-010
source: Visa Business News (representative)
source_basis: Visa Issuer Personalization Standards refresh; card-production vendor program
date: 2026-08-18
network: visa
mandatory: true
synthesized: true
difficulty: clear
expected_relevance: not_relevant
expected_priority: null
---

# Issuer Card Production Standards — Personalization File Format Refresh and Certified Vendor List Update

**Effective date:** 1 December 2026 (with backwards-compatible parallel run from 1 October 2026)

## Summary

Visa is publishing version 7.0 of the Issuer Card Production Personalization File Specification, used by issuing banks and their card-production vendors to instruct physical and virtual card personalization. The v7.0 specification introduces an updated EMV personalization profile, adds support for the latest contactless application identifiers (AIDs), and refreshes the Visa-certified card-production vendor list.

This bulletin is directed at **issuing banks and their certified card-production vendors**. It governs how a card is physically (or virtually) manufactured and provisioned with cardholder data before being shipped or downloaded to the cardholder.

## What's in scope of this bulletin

- Issuing banks operating in-house card-production facilities.
- Visa-certified card-production vendors (Thales / Gemalto, Giesecke+Devrient, IDEMIA, CPI Card Group, Perfect Plastic Printing, and others listed in Annex A of the Issuer Personalization Standards Manual).
- Issuer IT teams responsible for personalization-bureau integration.
- Mobile wallet provisioning systems that consume issuer-side personalization output to provision tokens into Apple Pay, Google Pay, and Samsung Pay.

## What's explicitly out of scope

- Acquirer-side processing of any transaction type.
- Authorization, clearing, or settlement message handling.
- Payment service providers, payment facilitators, gateways, and payment orchestrators in their merchant-side capacity.
- Merchant-side card acceptance, including card-present terminal certification (covered separately under the Visa Terminal Configuration Standards).
- Cardholder-side application behaviour after card delivery (covered separately under the Visa Cardholder Experience Standards).
- Dispute, chargeback, fraud monitoring, or compliance assessments.

## What's required (for in-scope parties)

In-scope issuing banks and their card-production vendors must:

1. Adopt the v7.0 personalization file schema for all new card-production jobs initiated after 1 December 2026.
2. Update the EMV profile reference in personalization scripts to point at the Visa v7.0 profile.
3. Re-certify the card-production line with Visa per the Production Line Re-Certification process.
4. Update the issuer-bureau handoff protocol to use the new file envelope.

## Related references

- Visa Issuer Personalization Standards Manual v7.0
- Visa Certified Card-Production Vendor List Q3 2026
- EMV CPS (Common Personalization Specification) v1.1

## Action required

Issuing banks and their card-production vendors must coordinate the migration to the v7.0 personalization file format and re-certify their production lines before the parallel-run window closes on 30 November 2026. **No action is required for any party operating in the merchant-side acceptance, acquiring, or payment orchestration capacity.**
