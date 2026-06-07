---
id: visa-2026-q3-015
source: Visa Business News (representative)
source_basis: UK post-Brexit Strong Customer Authentication divergence (FCA Handbook PS25/9 alignment)
date: 2026-09-03
network: visa
mandatory: true
synthesized: true
difficulty: adversarial
failure_mode: jurisdiction_edge_and_issuer_language
expected_relevance: relevant
expected_priority: P1
---

# UK Strong Customer Authentication — Implementation of Post-Brexit FCA Exemption Divergence

**Effective date:** 1 January 2027 (transition window from 1 October 2026)

## Summary

Following the UK Financial Conduct Authority's PS25/9 policy statement formalizing the UK Strong Customer Authentication (SCA) regime post-Brexit divergence from EU PSD2, Visa is publishing the corresponding implementation guidance for UK-region Visa transactions. The UK SCA regime introduces three exemption categories that differ materially from the EU PSD2/PSR2 baseline: a UK-specific low-value exemption threshold, a UK-specific Transaction Risk Analysis (TRA) score band, and the new UK-specific merchant-initiated remote-commerce (MIRC) exemption.

This bulletin sets out **how Visa issuers will be required to evaluate and respond to authentication-exemption flags carried on UK-region card-not-present authorization requests** under the new regime.

## What changes for UK-region transactions

For Visa card-not-present transactions where the cardholder's issuer is UK-domiciled, from the effective date:

1. **Exemption flag schema (Field 34, sub-field 3) is extended** with two new exemption codes: `UK-LV` (UK low-value exemption — threshold £45 / 5 cumulative / £150 cumulative) and `UK-MIRC` (UK merchant-initiated remote-commerce exemption).
2. **Issuer step-up handling.** UK issuers must evaluate the `UK-LV` and `UK-MIRC` flags per the FCA PS25/9 rules and may not unconditionally step up authentication where the flag is correctly populated. Where the issuer steps up despite a valid exemption, the transaction's fraud-loss liability remains with the issuer, not the merchant.
3. **TRA exemption ceiling.** The UK-specific TRA exemption ceiling rises to £500 (vs the EU's €500), with a UK-region cumulative monthly TRA exemption cap of £1,250 per cardholder.
4. **EU-region cards transacting on UK merchants.** For an EU-region card transacting at a UK merchant, the EU PSD2/PSR2 exemption schema continues to apply (issuer is EU; the EU regime governs). For a UK-region card transacting at an EU merchant, the EU PSD2/PSR2 exemption schema applies (issuer is EU-affected because UK card with EU merchant — but issuer is UK; the UK regime governs the issuer's evaluation, while the EU PSR2 acquirer-side rules continue to apply at the merchant location).

## The framing in this bulletin

The bulletin is primarily directed at **Visa issuers** — it describes how issuers must evaluate the new UK exemption flags and how the issuer-side step-up logic interacts with the FCA rules. The word "issuer" appears throughout.

However, the merchant-side acceptance flow on UK-region transactions must surface and populate the new exemption flags correctly. The acquiring bank, payment service provider, payment gateway, or payment orchestrator routing UK-region card-not-present authorizations:

- Must extend its authentication-exemption flagging logic to emit the new `UK-LV` and `UK-MIRC` codes when the conditions are met.
- Must update its 3DS authentication request construction to surface the UK exemption schema correctly to the issuer.
- Must reflect the new TRA exemption thresholds in its fraud-rule engine where TRA exemptions are claimed merchant-side.
- Must update its authorization-flow handling to distinguish UK-region from EU-region transactions correctly when populating exemption flags.

Without these merchant-side changes, UK-region transactions will be flagged as ineligible for the new UK exemptions, and the merchant will see elevated 3DS step-up rates and the resulting checkout friction.

## What does not change

For non-UK-region transactions, the EU PSD2/PSR2 regime continues unchanged. The Visa global authentication schema, the EMV 3DS protocol, the network token service, and the chargeback liability shift rules are unchanged. No change to message format outside Field 34, sub-field 3.

## Related references

- FCA Policy Statement PS25/9 (UK Strong Customer Authentication, post-Brexit)
- Visa Authentication Best Practices — UK Region Addendum v1.0
- EMV 3DS 2.3 Specification (current 3DS protocol — see VBN 2026-Q2-3104)

## Action required

Acquirers, payment service providers, payment gateways, and payment orchestrators that handle UK-region card-not-present authorization traffic must implement the new UK exemption schema, the UK TRA exemption ceiling, and the UK-vs-EU region routing logic before 1 January 2027.
