---
id: visa-2026-q2-012
source: Visa Business News (representative)
source_basis: Visa Account Updater (VAU) service v3.0 specification refresh
date: 2026-05-20
network: visa
mandatory: true
synthesized: true
difficulty: adversarial
failure_mode: wording_trap
expected_relevance: relevant
expected_priority: P1
---

# Visa Account Updater v3.0 — Required Migration for Card-on-File Refresh Subscribers

**Effective date:** 1 October 2026 (legacy v2 endpoints deprecate 31 December 2026)

## Summary

The Visa Account Updater (VAU) service — used to refresh stored Visa Primary Account Numbers (PANs) when a card is reissued, the expiry changes, or the cardholder is migrated to a new BIN — is moving to v3.0. The v3.0 release introduces a structured-change-event webhook channel, replaces the legacy batch-pull model with a streaming push pattern, and adds explicit support for network-token (DPAN) refresh events.

Acquiring banks that subscribe their merchants to VAU must migrate their VAU integration to the v3.0 specification before the legacy v2 deprecation date.

## What changes

The v3.0 specification:

1. **Webhook channel (new).** Account update events are pushed to a subscriber-supplied HTTPS endpoint instead of pulled in nightly batches. Subscribers must implement endpoint authentication using the supplied VAU webhook signing keys and acknowledge receipt within 30 seconds of delivery.
2. **Event-typed payloads.** Each event carries an event type (`pan_update`, `expiry_update`, `bin_migration`, `card_closure`, `network_token_pan_link_update`) and the structured before/after values.
3. **Network-token (DPAN) refresh.** Where the original stored credential was a network token rather than a raw PAN, the v3.0 event carries the corresponding DPAN refresh information (cryptogram regeneration trigger, new TRID assignment).
4. **Acknowledgement and replay.** Subscribers must acknowledge each delivered event; missed events are replayed for up to 7 days through the v3.0 replay endpoint.

## Who must act

The VAU service is offered to **acquiring banks** (and to certain large merchant aggregators with direct VAU subscriptions). Acquirers in turn typically integrate VAU on behalf of their merchants — passing the refreshed PAN or DPAN data back to whichever system maintains the merchant's card-on-file vault.

In practice, the entity that integrates with VAU on the acquirer's behalf is usually:

- The acquirer's own internal vault, OR
- A merchant-facing **payment service provider, gateway, or payment orchestrator** that maintains the canonical card-on-file record for the merchant's recurring-billing or stored-credential flows.

The bulletin language uses "acquirer" throughout because the acquiring bank is the formal VAU subscriber under Visa's program rules. However, any entity that operationally consumes VAU output to refresh stored credentials in a merchant's card-on-file ledger is functionally an integration party and must update its VAU consumer to v3.0 by the deadline. This includes payment service providers and orchestrators that operate the stored-credential refresh path for their merchant clients on behalf of the acquirer.

## What integration parties must do

By the effective date, VAU integration parties must:

1. Implement the v3.0 webhook receiver (HTTPS, signed payloads, 30-second ACK SLA).
2. Map all five v3.0 event types into the stored-credential ledger update path.
3. Add DPAN refresh handling for stored network tokens, including triggering cryptogram regeneration via VTS where needed.
4. Decommission the legacy v2 nightly-batch consumer by 31 December 2026.

## Penalty for non-migration

After 31 December 2026, the v2 endpoint will return HTTP 410 Gone. Stored credentials will silently go stale, leading to elevated MIT authorization failure rates on stale stored PANs/DPANs. Visa will surface affected acquirer accounts on the monthly Acquirer Quality Index report; sustained stale-credential rates may trigger Acquirer Compliance Assessment action.

## Related references

- Visa Account Updater Service Specification v3.0
- Visa Token Service — DPAN Refresh Trigger Specification v3.2
- VBN Notice 2025-Q4-3105 (initial VAU v3.0 announcement)

## Action required

VAU integration parties — acquirers and the merchant-facing card-on-file operators acting on their behalf — must migrate to the v3.0 webhook integration and decommission the legacy v2 consumer before 31 December 2026.
