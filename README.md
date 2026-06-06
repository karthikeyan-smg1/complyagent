# ComplyAgent

> Repo-connected AI compliance agent for payments codebases. Triages regulatory bulletins from card networks and central banks, identifies which code paths are affected, and drafts impact assessments — turning a manual triage queue into a ranked, code-linked work list.

**Status:** Portfolio prototype in development. Live demo, eval results, and Loom walkthrough land here as the build progresses (see [BRIEF.md §7](BRIEF.md#7-build-sequence) for the build sequence).

---

## The problem

Large payments platforms receive thousands of regulatory bulletins per year — from Visa, Mastercard, RuPay, RBI, the Fed, ECB, ACH, SEPA, and others. Most are not relevant to a given codebase. The ones that are often surface late, leading to scrambled compliance work near regulator deadlines.

ComplyAgent triages this queue. For each bulletin it (1) classifies relevance to the connected codebase, (2) identifies the specific files and functions affected, (3) scores priority, and (4) files a draft GitHub Issue. Compliance leads review ranked work instead of raw inboxes.

## What v0 does

Single tenant (a fork of [Hyperswitch](https://github.com/juspay/hyperswitch)), single card network (Visa — [why](DECISIONS.md#2026-06-06--narrow-v0-bulletin-corpus-to-visa-only)):

1. Ingest hand-curated regulatory bulletins (PDF / markdown) from `tenants/hyperswitch/bulletins/`.
2. **Stage 1 classification** — Gemini 2.5 Flash tags each bulletin against a payments taxonomy.
3. **Stage 2 classification** — Gemini 2.5 Pro judges relevance to the codebase given a product profile, returning `{relevant, confidence, reasoning}`.
4. **Code RAG** — Voyage `voyage-code-3` embeddings + Supabase pgvector retrieve the top-k affected code chunks from Hyperswitch.
5. **Impact assessment** — Gemini 2.5 Pro drafts a per-bulletin analysis naming the affected files and a recommended action.
6. **Priority** — a deterministic Python rubric assigns P0–P3.
7. **GitHub Issue** — a draft Issue is filed on the connected fork.

## Architecture

```
Bulletin → Stage 1 (Flash, tagging) → Stage 2 (Pro, relevance)
       ↓ (if relevant)
   Code RAG (Voyage + pgvector over Hyperswitch)
       ↓
   Impact assessment (Pro) → Priority rubric → GitHub Issue
```

Full data flow: [BRIEF.md §6](BRIEF.md#6-architecture). All-free zero-cost stack — see [DECISIONS.md 2026-06-06 (zero-cost stack)](DECISIONS.md) for tradeoffs.

| Layer | Tool |
|---|---|
| LLM | Google Gemini 2.5 Pro + Flash |
| Embeddings | Voyage AI `voyage-code-3`, `voyage-3-large` |
| Vector store + DB | Supabase Postgres + pgvector |
| App hosting | Streamlit Community Cloud |
| Scheduler | GitHub Actions cron |
| Observability | Langfuse Cloud |

## Eval

**Riskiest assumption** ([BRIEF §4](BRIEF.md#4-riskiest-assumption-phase-1-must-prove)): an LLM, given a product profile and a regulatory bulletin, can classify relevance to a specific payments codebase at **>85% precision and >80% recall** against a human-labeled ground truth. If this fails, nothing else matters.

Phase 2 will report precision, recall, and a confusion matrix against the labeled set in `tenants/hyperswitch/ground_truth.csv`. Visa-only for v0 ([why](DECISIONS.md#2026-06-06--narrow-v0-bulletin-corpus-to-visa-only)).

## Run locally

```bash
git clone https://github.com/karthikeyan-smg1/complyagent.git
cd complyagent
cp .env.example .env             # fill in your API keys
uv sync                          # creates .venv, installs deps
uv run python scripts/verify_connections.py
uv run python scripts/run_skateboard.py hyperswitch
```

Accounts needed (all free tiers): Google AI Studio (Gemini), Voyage AI, Supabase, Langfuse Cloud, GitHub. See `.env.example` for the exact keys.

## Scaling to multi-tenant SaaS

ComplyAgent v0 is single-tenant by config, multi-tenant by design. Every company-specific setting lives in `tenants/<slug>/config.yaml`; the pipeline reads tenant config rather than hardcoded constants. To go from prototype to SaaS, the extension points are:

| What changes | v0 (this repo) | v1 (SaaS) |
|---|---|---|
| Repo connection | Cloned locally for indexing | **GitHub App** with per-install access + webhooks |
| Jira integration | Disabled in config | **Atlassian OAuth2** per tenant; project + issue type from config |
| Tenant isolation | One config file per directory | **Supabase RLS** keyed on `tenant_id`; per-tenant schema namespacing |
| Secrets per tenant | None (single deployment env) | **Vault** (Supabase Vault or app-level KMS); per-tenant API tokens |
| Scheduling | GitHub Actions cron, single tenant | Scheduler iterates the `tenants` table; cron per tenant from config |
| Auth | None (single user, no UI auth) | **OAuth** (Clerk or Supabase Auth); org + role-based access |
| Onboarding | `mkdir tenants/<slug>` + `config.yaml` | Web UI: GitHub App install → product profile wizard → Jira connect |
| Billing | N/A | Usage-based (bulletins processed × LLM calls); Stripe |

To add another card network to v0 *today*: drop bulletins under `tenants/<slug>/bulletins/`, re-run the eval. No code or prompt changes — the classifier is network-agnostic.

## Limitations and anti-goals

Deliberately not in scope for v0 — these would be the wrong things to build first ([BRIEF §5](BRIEF.md#5-scope), [§12](BRIEF.md#12-anti-goals)):

- No real multi-tenancy, auth, billing, or OAuth
- No live regulatory bulletin scraping (hand-curated corpus only)
- No auto-merge of PRs (only Issue creation)
- No production observability beyond Langfuse free tier
- No tests beyond the classifier and priority rubric

## About

Built by Karthikeyan Subramaniam as a portfolio prototype demonstrating AI-agent and payments-domain product depth. Senior PM at Zuora, previously at Juspay (Card Payments Platform).

License: MIT.
