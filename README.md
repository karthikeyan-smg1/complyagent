# ComplyAgent

> Repo-connected AI compliance agent for payments codebases. Triages regulatory bulletins from card networks and central banks, identifies which code paths are affected, and drafts impact assessments — turning a manual triage queue into a ranked, code-linked work list.

**Live demo:** _(deploying to Streamlit Community Cloud — link will replace this line once the deploy completes)_

**Status:** Portfolio prototype, v0 shipped. Two-stage classifier runs end-to-end on a curated Visa bulletin corpus with first-cut eval results in [`outputs/latest-eval.json`](outputs/latest-eval.json). Code-RAG + impact assessment + GitHub Issue automation is the v0.2 milestone (see the Roadmap tab in the demo).

---

## The problem

Large payments platforms receive thousands of regulatory bulletins per year — from Visa, Mastercard, RuPay, RBI, the Fed, ECB, ACH, SEPA, and others. Most are not relevant to a given codebase. The ones that are often surface late, leading to scrambled compliance work near regulator deadlines.

ComplyAgent triages this queue. For each bulletin it (1) classifies relevance to the connected codebase, (2) identifies the specific files and functions affected, (3) scores priority, and (4) files a draft GitHub Issue. Compliance leads review ranked work instead of raw inboxes.

## What v0 does

Single tenant (a fork of [Hyperswitch](https://github.com/juspay/hyperswitch)), single card network (Visa — [why](DECISIONS.md#2026-06-06--narrow-v0-bulletin-corpus-to-visa-only)):

1. Ingest hand-curated regulatory bulletins (markdown + YAML frontmatter) from `tenants/hyperswitch/bulletins/` — 10 Visa bulletins shipped, mixed across relevant / not-relevant.
2. **Stage 1 classification** — Gemini 2.5 Flash-Lite tags each bulletin against a payments taxonomy via Pydantic `response_schema` (enforced JSON, no jailbreak surface).
3. **Stage 2 classification** — Gemini 2.5 Flash-Lite judges relevance to the codebase given a product profile, returning `{relevant, confidence, reasoning, affected_surfaces}`.
4. **Eval** — `scripts/run_eval.py` reports precision / recall / F1 against frontmatter ground truth and refreshes `outputs/latest-eval.json` for the dashboard.

Both Gemini models are env-overridable — `COMPLY_STAGE1_MODEL=gemini-2.5-flash` and `COMPLY_STAGE2_MODEL=gemini-2.5-pro` for billed-key production (see [DECISIONS.md 2026-06-06](DECISIONS.md)).

**v0.2 (next milestone, not yet shipped):**

5. **Code RAG** — Voyage `voyage-code-3` embeddings + Supabase pgvector retrieve the top-k affected code chunks from Hyperswitch.
6. **Impact assessment** — drafts a per-bulletin analysis naming the affected files and a recommended action.
7. **Priority** — a deterministic Python rubric assigns P0–P3.
8. **GitHub Issue** — a draft Issue is filed on the connected fork.

## Architecture

```
Bulletin → Stage 1 (Flash-Lite, tagging) → Stage 2 (Flash-Lite, relevance)
       ↓ (if relevant)  [v0.2]
   Code RAG (Voyage + pgvector over Hyperswitch)
       ↓
   Impact assessment → Priority rubric → GitHub Issue
```

Full data flow: [BRIEF.md §6](BRIEF.md#6-architecture). All-free zero-cost stack — see [DECISIONS.md 2026-06-06 (zero-cost stack)](DECISIONS.md) for tradeoffs.

| Layer | Tool |
|---|---|
| LLM | Google Gemini 2.5 Flash-Lite (default; Flash + Pro env-swap for billed keys) |
| Embeddings (v0.2) | Voyage AI `voyage-code-3`, `voyage-3-large` |
| Vector store + DB (v0.2) | Supabase Postgres + pgvector |
| App hosting | Streamlit Community Cloud |
| Scheduler (v0.2) | GitHub Actions cron |
| Observability | Langfuse Cloud |

## Eval

**Riskiest assumption** ([BRIEF §4](BRIEF.md#4-riskiest-assumption-phase-1-must-prove)): an LLM, given a product profile and a regulatory bulletin, can classify relevance to a specific payments codebase at **>85% precision and >80% recall** against a human-labeled ground truth.

**First clean run (10 bulletins, Visa-only):** precision 1.000, recall 1.000, F1 1.000, accuracy 1.000 (5 TP / 0 FP / 5 TN / 0 FN). Wall-clock 126s. See `outputs/latest-eval.json` and the **Eval** tab of the dashboard.

Honest caveat: the v0 corpus is small (10 bulletins) and synthesized from public Visa programs. This is a sanity check on the architecture, not a SOTA claim. v0.2 expands to 30+ bulletins with borderline cases where calibration matters.

## Run locally

```bash
git clone https://github.com/karthikeyan-smg1/complyagent.git
cd complyagent
cp .env.example .env             # at minimum, set GEMINI_API_KEY
uv sync                          # creates .venv, installs deps

# Verify the network/auth path is healthy (15s bounded)
uv run python scripts/smoke_gemini.py

# Run the eval over the curated bulletin corpus
uv run python scripts/run_eval.py hyperswitch

# Boot the dashboard
uv run streamlit run streamlit_app.py
```

Accounts needed for v0: Google AI Studio (Gemini) — the rest (Voyage, Supabase, Langfuse) are v0.2 dependencies, listed in `.env.example` but not required for the current shipped slice.

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
