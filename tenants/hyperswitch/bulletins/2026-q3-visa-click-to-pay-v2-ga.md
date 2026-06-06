---
id: visa-2026-q3-008
source: Visa Business News (representative)
source_basis: Click to Pay (EMVCo SRC framework) v2.0 General Availability announcement
date: 2026-07-12
network: visa
mandatory: false
synthesized: true
expected_relevance: not_relevant
expected_priority: null
---

# Click to Pay v2.0 — General Availability Across All Visa Markets

**Effective date:** General Availability from 1 September 2026

## Summary

Visa is announcing General Availability of Click to Pay version 2.0, the next major release of the EMVCo Secure Remote Commerce (SRC) checkout standard. Click to Pay 2.0 introduces an improved guest checkout flow, biometric step-up support on web, and enriched merchant branding capabilities. The release is available across all Visa markets starting 1 September 2026.

Click to Pay is an **opt-in consumer checkout experience** that merchants can choose to offer alongside their existing checkout flows. It is not a mandatory rule change and does not replace any existing acceptance pattern.

## What's new in v2.0

For merchants who choose to integrate Click to Pay:

1. **Streamlined guest enrollment** — first-time users can complete a Click to Pay enrollment in three taps without leaving the merchant's checkout page.
2. **Passkey-based authentication** — Click to Pay 2.0 supports the WebAuthn standard for biometric step-up, replacing the v1.0 SMS OTP fallback as the default authentication factor.
3. **Improved merchant branding controls** — merchants can supply a branded card-art tile, merchant logo, and accent colour through the Click to Pay Console.
4. **Subscription-friendly mode** — explicit consent capture for stored-credential setup at first transaction.

## Integration options

Merchants who want to offer Click to Pay have multiple integration paths:

- Embed the Visa-hosted Click to Pay JavaScript widget directly in the checkout page.
- Use a Click-to-Pay-enabled checkout SDK from a participating payment service provider, gateway, or commerce platform.
- Build a custom integration against the SRC Initiator API.

## Position relative to existing checkout flows

Click to Pay does not change:

- The underlying card authorization or clearing flow once the cardholder has selected a card in the Click-to-Pay sheet (the resulting transaction is a standard tokenized Visa authorization).
- Whether the merchant accepts Visa or how Visa transactions are routed.
- Any acceptance rule, mandate, fee schedule, dispute process, or chargeback right.

## Who should consider integrating

This release is most relevant to:

- Direct-to-consumer e-commerce merchants seeking checkout conversion improvements.
- Commerce platforms (Shopify, BigCommerce, Magento) offering merchant-facing checkout pages.
- Payment service providers offering merchant-hosted checkout SDKs.

Headless payment orchestrators that route traffic to acquirers but do not render checkout UIs do not interact with Click to Pay directly; cardholder selection of a Click-to-Pay card occurs upstream in the merchant or commerce-platform layer before the resulting transaction reaches the orchestrator.

## Related references

- EMVCo SRC Specification v2.0
- Click to Pay Merchant Integration Guide v2.0
- VBN Notice 2026-Q2-3104 (Click to Pay v2.0 limited release)

## Action required

Merchants and commerce platforms wishing to offer Click to Pay 2.0 should review the EMVCo SRC v2.0 specification and the Click to Pay Merchant Integration Guide. No action required for parties not adopting the Click to Pay checkout experience.
