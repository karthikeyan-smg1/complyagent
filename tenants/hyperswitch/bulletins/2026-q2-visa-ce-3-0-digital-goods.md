---
id: visa-2026-q2-014
source: Visa Business News (representative)
source_basis: Visa Compelling Evidence 3.0 (CE 3.0) expansion to in-app digital-goods category
date: 2026-06-02
network: visa
mandatory: false
synthesized: true
difficulty: adversarial
failure_mode: optional_but_operationally_required
expected_relevance: relevant
expected_priority: P2
---

# Visa Compelling Evidence 3.0 — Expansion to In-App Digital Goods and Subscription-Tier Disputes

**Effective date:** 1 September 2026 (CE 3.0 protection available from this date for in-app digital-goods disputes)

## Summary

Visa is expanding the Compelling Evidence 3.0 (CE 3.0) dispute defense framework to cover **in-app digital-goods purchases** and **subscription-tier change disputes** under reason codes 10.4 (Other Fraud — Card-Absent) and 13.1 (Merchandise / Services Not Received). This expansion gives merchants a structured evidence pattern they can present to qualify for CE 3.0 representment protection on this category of disputes.

CE 3.0 is **opt-in dispute protection**. A merchant that does not present CE 3.0 evidence continues to face disputes under the standard pre-arbitration rules. However, for merchants operating in the in-app digital-goods or subscription category, the operational reality is that without CE 3.0 protection, dispute win rates on these reason codes drop sharply — historical data from CE 2.0 categories suggests an 18-22 percentage-point delta in merchant favor where CE 3.0 evidence is presented vs. not.

## What CE 3.0 evidence looks like for in-app digital goods

To qualify for CE 3.0 protection on an in-app digital-goods or subscription dispute, the merchant must present, in the structured Visa Evidence Pack v4 envelope, the following four signal classes for at least two prior undisputed transactions from the same cardholder:

1. **Matching device identifier.** Device ID, advertising ID, or app-installation-instance ID present at both the disputed transaction and at least two prior undisputed ones.
2. **Matching IP address.** IP address (or IP /24 prefix for IPv4, IP /48 prefix for IPv6) present at both.
3. **Matching account identifier.** In-app account ID, login email hash, or merchant-side user ID present at both.
4. **Matching purchase or session signal.** Either (a) a prior undisputed purchase of the same digital-goods SKU or subscription tier, OR (b) a meaningful in-app session on the merchant's platform within 24 hours of the disputed transaction.

Each signal must be carried in the structured `compelling_evidence_3_0_fields` block of the Visa Evidence Pack v4 envelope (introduced in the VDRP Pre-Arbitration Evidence Format update earlier this year — see VBN 2026-Q1-2210).

## Who this is relevant to

This expansion is directly operationally relevant to anyone in the chargeback-defense path for in-app digital-goods or subscription merchants. To present CE 3.0 evidence, the pre-arbitration response pipeline must be extended to populate the four signal classes — device ID, IP, account identifier, prior-purchase or session signal — alongside the existing Visa Evidence Pack v4 transaction context. This requires:

1. Surfacing the device ID and merchant-side account identifier from the merchant's checkout context into the chargeback response, where today most pipelines carry only authorization-time data.
2. Retaining the per-user transaction history (prior undisputed transactions from the same cardholder) for a sufficient window (at least 540 days from the original transaction) to support the "two prior undisputed transactions" requirement.
3. Emitting the new `compelling_evidence_3_0_fields` block in the Visa Evidence Pack v4 envelope per dispute submitted under reason code 10.4 or 13.1.

Without this update, in-app digital-goods and subscription merchants will continue to face the higher (pre-CE-3.0) dispute loss rate. There is no rule penalty for not adopting CE 3.0, but the dispute economics make it operationally required for merchants in this category — and therefore for whichever party operates the chargeback lifecycle on their behalf.

## What this does not change

CE 3.0 is an evidence pattern, not a new rule. This expansion does not change:

- Authorization or clearing message format.
- The pre-arbitration response window (still 30 days from dispute notification).
- The Visa Evidence Pack v4 schema introduced in Q1 2026 (CE 3.0 fields are an existing block in that schema, now applicable to a broader dispute category).
- The chargeback liability shift rules.
- Tokenization, 3DS, or fraud-monitoring requirements.

## Related references

- Visa Compelling Evidence 3.0 Implementation Guide v2.1
- Visa Evidence Pack v4 Specification
- VBN Notice 2026-Q1-2210 (VDRP Pre-Arbitration Evidence Format v4)

## Action required

Whichever entity operates the pre-arbitration response pipeline for merchants in the in-app digital-goods or subscription category should extend its evidence-packet generation to populate the four CE 3.0 signal classes for the in-app dispute pattern, to ensure those merchants qualify for the higher CE 3.0 dispute win rates from 1 September 2026.
