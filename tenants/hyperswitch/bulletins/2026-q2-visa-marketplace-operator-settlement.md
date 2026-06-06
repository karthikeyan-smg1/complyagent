---
id: visa-2026-q2-006
source: Visa Business News (representative)
source_basis: Visa Marketplace Operator Settlement Reporting; merchant aggregator rules
date: 2026-04-22
network: visa
mandatory: true
synthesized: true
expected_relevance: not_relevant
expected_priority: null
---

# Marketplace Operator Settlement Reporting — New Quarterly Filing for Visa-Designated Marketplaces

**Effective date:** 1 July 2026 (first filing window opens 1 October 2026)

## Summary

Visa is introducing a quarterly Marketplace Operator Settlement Report (MOSR) for entities designated as Visa Marketplace Operators (VMOs) under the Marketplace Aggregator Framework. VMOs must file the MOSR with their acquiring bank within 30 days of each calendar quarter end, reporting per-seller funding flows, seller-by-seller authorization volumes, and the marketplace's seller onboarding KYC posture.

A Visa Marketplace Operator is defined under VMO Designation Rules as an entity that:

1. Operates a digital marketplace connecting third-party sellers with cardholders, AND
2. Funds those third-party sellers from a single marketplace-controlled settlement account, AND
3. Holds Marketplace Operator status under the Visa Aggregator Onboarding Program.

## What's required

VMO entities and their acquirers must:

1. Implement seller-level funding ledger tracking that ties each settlement disbursement to specific authorization IDs.
2. Submit the MOSR via the Visa Acquirer Portal as a structured CSV per the schema in Annex C of the VMO Settlement Specification.
3. Maintain seller KYC records (UBO documentation, beneficial-owner sanctions screening, transaction monitoring rule sets) for audit by Visa's Acquirer Risk Standards team.
4. Reconcile MOSR figures against the acquirer's monthly settlement report; variances over 0.5% require a written explanation.

## What this does not change

The MOSR does not change:

- Authorization message formats for individual transactions.
- Chargeback or dispute workflows.
- The interchange or assessment rates applied to underlying transactions.
- 3DS authentication requirements or step-up rules.
- Tokenization or stored-credential handling.

Payment orchestrators that do *not* hold VMO designation — including payment service providers, payment facilitators that do not operate a digital marketplace, and gateway/orchestrator vendors that simply route traffic to acquirers — are out of scope.

## Penalties for non-compliance

Designated VMOs that miss a quarterly MOSR filing will be subject to a USD 25,000 late-filing assessment per the standard Acquirer Compliance Assessment Program. Repeat misses (three consecutive quarters) may trigger a review of VMO designation.

## Related references

- VMO Designation Rules v2.0
- Visa Aggregator Onboarding Program guidelines
- Visa Acquirer Risk Standards, Annex E

## Action required

VMO-designated marketplaces and their acquirers must build the per-seller ledger and CSV export, register the responsible-officer contact with the Visa Acquirer Portal, and file the first MOSR no later than 30 October 2026.
