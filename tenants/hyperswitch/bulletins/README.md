# Bulletins corpus — sourcing note

The bulletins in this directory are **representative**, not verbatim. Visa's actual operational and regulatory bulletins (Visa Business News, VOLs, OIRs) are sent through network-internal channels to acquirers, issuers, and processors — they are not publicly redistributable.

For this prototype, each bulletin is composed from publicly documented Visa programs and rules — CIT/MIT framework, 3D Secure 2.x, Visa Account Updater, Click to Pay, Cross-Border Commerce, etc. — and written in the format and tone that a real Visa Business News notice would take. Every bulletin file's YAML frontmatter sets `synthesized: true` and lists the public sources the content draws from.

This is a deliberate choice for the v0 portfolio prototype. The goal is to test whether the classifier can discriminate regulatory-mandatory bulletins (which require code changes) from operational notices and marketing announcements (which do not). That hypothesis is testable on representative content; using verbatim network bulletins would require a real acquirer relationship.

**For a production deployment**, the ingestion layer would consume actual Visa Business News feeds via an authorized acquirer/issuer connection — see [README.md → Scaling to multi-tenant SaaS](../../../README.md#scaling-to-multi-tenant-saas).
