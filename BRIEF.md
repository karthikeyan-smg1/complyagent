# ComplyAgent — Project Brief

> **Purpose of this document:** Single source of truth for Claude Code. Reference at the start of every session with: *"Read BRIEF.md, then we'll continue from where we left off."*

---

## 1. What we're building

**ComplyAgent** is a repo-connected AI agent that:

1. Monitors regulatory and compliance notifications from payment networks (Visa, Mastercard, Rupay), central banks (RBI, Fed, ECB), and clearing systems (NACH, SEPA, ACH)
2. Classifies whether each notification affects a target payments codebase
3. Reads the connected codebase (via GitHub) and identifies which files/functions are impacted
4. Generates a draft GitHub Issue with a priority score, source citations, code references, and a recommended action

**Target codebase for the prototype:** [Hyperswitch](https://github.com/juspay/hyperswitch) — Juspay's open-source payments orchestrator (Apache 2.0, 40k+ stars, Rust). Chosen because it's reputable, payments-domain-relevant, and the PM building this previously worked at Juspay on the Card Payments Platform.

**Why this exists:** Large payments platforms manually triage thousands of regulatory bulletins per year. Most are irrelevant. The relevant ones often slip through. This agent triages, scores, and routes — saving compliance analyst time and reducing risk of missed mandates.

---

## 2. Who this is for

- **Primary user (in the demo):** A staff engineer or compliance lead at a payments platform
- **Real audience for this prototype:** Hiring managers and senior PM interviewers evaluating Karthik's product+technical depth

This is a **portfolio prototype**, not a production system. Decisions favor demonstrating product thinking and shipping speed over scale or enterprise readiness.

---

## 3. PM context (who is building this and why)

- **Karthik Subramaniam** — Senior PM at Zuora (Platform Monetisation & Integrations), based in Bengaluru
- Previously at **Juspay** (Card Payments Platform), **Twid** (Developer Experience), **LatentView** (Data Products)
- IIM Calcutta PGDM, B.Tech EEE from Amrita
- Building this to demonstrate hands-on AI agent + payments domain depth for senior PM roles

---

## 4. Riskiest assumption (Phase 1 must prove)

> An LLM, given a payments product profile and a regulatory bulletin, can classify relevance to a specific codebase with >85% precision and >80% recall against a human-labeled ground truth.

If this fails, nothing else matters. Prove this first with 30 hand-labeled bulletins before building anything else.

---

## 5. Scope

### In scope for v0
- 30+ hand-curated regulatory bulletins (**Visa only for v0 skateboard + eval — see DECISIONS.md 2026-06-06**) stored as PDFs/markdown under `tenants/<slug>/bulletins/`. Architecture is multi-network; other networks are a config + corpus extension, not a code change.
- Two-stage LLM classifier (tagging + relevance reasoning)
- Code RAG over Hyperswitch repo
- Priority scoring rubric (Python module, deterministic)
- Auto-generated GitHub Issues on a fork of Hyperswitch
- Public Streamlit dashboard at a Railway URL
- Eval harness with precision/recall on the hand-labeled set
- **Tenant-shaped single-tenant architecture:** all company-specific config (target repo, product profile, regulatory scope, issue tracker, schedule, notifications) lives in `tenants/<slug>/config.yaml`. The pipeline is parameterized over tenant config. Single tenant in v0 (Hyperswitch). README explains the SaaS extension path. See DECISIONS.md 2026-06-05.

### Explicitly out of scope for v0
- Live scrapers for card network portals (use static curated documents)
- Real-time webhook ingestion
- Multi-tenant support
- Auth on the dashboard
- Auto-merge of PRs (only auto-create Issues)
- Production-grade observability
- Code changes / patches (only flagging + draft impact assessment)

---

## 6. Architecture

### Hosting & infra (all free tiers)
- **Code hosting:** GitHub (public repo)
- **App hosting:** Streamlit Community Cloud (free, GitHub-deploy, supports secrets)
- **Scheduled runs:** GitHub Actions cron (unlimited minutes on public repos)
- **Database + vector store:** Supabase (Postgres + pgvector) — 500 MB DB, pauses after 1 week idle (weekly ping workflow mitigates)
- **LLM API:** Google Gemini — `gemini-2.5-flash` for both stages on the free tier (Gemini 2.5 Pro is paid-only; see DECISIONS.md 2026-06-06). Stage-2 model is env-overridable (`COMPLY_STAGE2_MODEL`) — swap to `gemini-2.5-pro` the moment billing is wired up.
- **Embeddings:** Voyage AI (`voyage-code-3` for code, `voyage-3-large` for documents)
- **Observability:** Langfuse Cloud (free tier, 50k observations/month)
- **Secrets:** Streamlit Cloud secrets (app runtime) + GitHub Actions secrets (cron runtime); `.env.example` in repo, never `.env`

### Component layout
```
complyagent/
├── BRIEF.md                          # this file
├── README.md                         # public-facing, includes demo link + Loom
├── pyproject.toml                    # uv-managed Python deps
├── .env.example                      # template, no secrets
├── data/
│   ├── bulletins/                    # hand-curated regulatory documents (PDF/MD)
│   └── ground_truth.csv              # hand-labeled relevance for eval
├── src/
│   ├── ingest/                       # load bulletins, extract text, chunk
│   ├── classify/                     # two-stage LLM classifier
│   ├── retrieve/                     # code RAG over Hyperswitch
│   ├── assess/                       # impact assessment generation
│   ├── prioritize/                   # deterministic priority rubric
│   ├── github_issue/                 # GitHub Issue creation
│   ├── eval/                         # precision/recall harness
│   └── dashboard/                    # Streamlit app
├── scripts/
│   ├── index_hyperswitch.py          # one-time: clone + index Hyperswitch
│   └── run_pipeline.py               # end-to-end run for one bulletin
├── tests/                            # pytest, focused on classifier + rubric
└── product_profile.yaml              # description of the target codebase's payment surface
```

### Data flow
```
Bulletin (PDF/MD)
   ↓ extract & chunk
Stage 1: Gemini 2.5 Flash tagging  →  taxonomy labels
   ↓
Stage 2: Gemini 2.5 Flash relevance → {relevant, confidence, reasoning}
         (env-swappable to 2.5 Pro on billed key)
   ↓ (if relevant)
Code RAG: Voyage embeddings + pgvector  →  top-k code chunks from Hyperswitch
   ↓
Gemini 2.5 Flash impact assessment  →  draft analysis + affected files
   ↓
Priority rubric (Python)  →  {P0..P3}
   ↓
GitHub Issue created on fork of Hyperswitch
```

---

## 7. Build sequence

Each phase produces a working artifact. Do not move on until current phase is shippable.

- **Phase 0 — Framing & setup** (2h): repo created, Hyperswitch forked, Supabase project, Railway account, accounts authenticated via Claude Code
- **Phase 1 — Skateboard** (4h): one Python script that takes a PDF, calls Claude, prints relevance. Local only. No hosting.
- **Phase 2 — Eval** (3h): 30 hand-labeled bulletins, precision/recall numbers, written-up results
- **Phase 3 — Code RAG** (4h): Hyperswitch indexed in Supabase pgvector, retrieval working, impact assessment generation
- **Phase 4 — Host** (3h): Streamlit dashboard live on Railway, public URL, all secrets in env vars
- **Phase 5 — GitHub integration** (2h): auto-create Issues on Hyperswitch fork
- **Phase 6 — Package** (2h): README, Loom demo, LinkedIn post, resume update

**Total: ~20 hours across two weekends.**

---

## 8. Decisions made (do not relitigate)

| Decision | Choice | Why |
|---|---|---|
| Target codebase | Hyperswitch (Juspay) | Domain credibility for Karthik, large reputable repo, payments-relevant |
| Hosting | Streamlit Cloud (app) + GitHub Actions (cron) + Supabase (DB) | All strictly free tiers — see DECISIONS.md 2026-06-05 (zero-cost stack) |
| LLM | Gemini 2.5 Flash (both stages on free tier; Pro for Stage-2 when billed) | Zero cost on free tier; Pro 2.5 free-tier limit is 0, so Flash runs both stages by default. 1M+ context window passes full bulletins without aggressive chunking — see DECISIONS.md 2026-06-05 + 2026-06-06 |
| Scheduler | GitHub Actions cron | Free on public repos; in-repo, version-controlled YAML demos cleanly |
| Embeddings | Voyage AI | Code-specific model, generous free tier |
| Language | Python 3.11 | Fastest path; PM is technical enough to read/modify |
| Dependency manager | `uv` | Fastest, modern, simpler than poetry |
| Vector store | Supabase pgvector | One vendor for DB + vectors |
| Observability | Langfuse Cloud free tier | Real LLM tracing without local setup |
| UI | Streamlit | PM demo speed > production polish |
| License of our agent | MIT | Permissive, doesn't matter much for portfolio |
| Tenant model | Single-tenant config-shaped like a tenant | Tells the SaaS extension story without the auth/billing tax — see DECISIONS.md 2026-06-05 |

---

## 9. Working agreement with Claude Code

Karthik is a **senior PM, not an engineer**. The way to work with him:

1. **Explain before doing.** Before running any non-trivial command or making any non-trivial code change, explain what you're about to do and why in 1–3 sentences. Wait for confirmation on first-time-ever actions; proceed without asking on repeats.
2. **One step at a time, especially early on.** Don't batch 10 commands. Show the result of step 1 before moving to step 2.
3. **Teach the mental model, not just the syntax.** When introducing a new tool (uv, Railway CLI, Supabase migrations), give a 2-sentence "what this is and why we're using it" before the command.
4. **Default to free / open-source.** Never suggest a paid service without flagging it and asking.
5. **Never commit secrets.** Use `.env`, `.gitignore`, Railway env vars. Set up `.gitignore` correctly from the first commit.
6. **Small commits, descriptive messages.** Each commit should be a logical unit Karthik can later reference in interviews.
7. **Update this BRIEF.md when scope or decisions change.** This file is the project memory.
8. **Maintain a `DECISIONS.md` log** with date-stamped decisions and the reasoning. Interview gold.
9. **Maintain a `LEARNINGS.md` log** — Karthik writes 2–3 sentences after each session on what he learned. Claude Code prompts for this at session end.
10. **If a step would take >30 minutes of Karthik's attention, propose breaking it up.** Two-hour focused sessions are the working unit.

---

## 10. Definition of "done" for the prototype

The prototype ships when all are true:

- [ ] Public URL where anyone can paste a regulatory bulletin and see classification + code analysis
- [ ] Eval results documented: precision/recall on 30+ labeled examples, with confusion matrix
- [ ] At least 3 auto-generated GitHub Issues live on a public Hyperswitch fork
- [ ] README explains: problem, approach, architecture, eval, demo link, limitations
- [ ] 3-minute Loom walkthrough recorded
- [ ] Resume bullet updated to reflect the actual built artifact
- [ ] LinkedIn post drafted

---

## 11. Stretch goals (only after "done")

- Live RSS ingestion from at least one source (RBI is easiest — public RSS)
- Confidence-based auto-approve threshold
- Slack notification when a new high-priority Issue is created
- Comparison eval: Claude vs. Llama via Groq on the same test set (great interview material)
- Auto-generated PR draft (not merge) for trivial mandates like fee table updates

---

## 12. Anti-goals (things explicitly not worth doing)

- Making this production-grade
- Supporting languages other than what Hyperswitch uses (Rust)
- Building a custom UI framework — Streamlit is fine
- Optimizing LLM cost below where it already is — free tiers are sufficient
- Adding auth, billing, or multi-tenancy
- Writing comprehensive tests for everything; test the classifier and rubric, skip UI tests
