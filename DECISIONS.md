# Decisions Log

> **Purpose:** Date-stamped record of significant scope, technical, and product decisions for ComplyAgent. Each entry captures the decision, the reasoning, the alternatives considered, and what was deliberately left out. Optimized for being referenceable in interviews and by future-self.

---

## 2026-06-05 — Tenant-shaped single-tenant prototype

**Decision.** Build the v0 prototype as single-tenant against Hyperswitch, but structure all company-specific configuration — target repo, product profile, regulatory scope, schedule, issue tracker, notification channels — as a per-tenant `config.yaml` under `tenants/<slug>/`. The pipeline reads tenant config rather than hardcoded constants. Real multi-tenancy (auth, RLS, billing, GitHub App install flow, Atlassian OAuth, per-tenant secrets vault) stays explicitly out of scope for v0 and is documented as a "Scaling to SaaS" section in the README with named extension points.

**Audience driver.** Hiring managers evaluating senior PM candidates. They need to see the product thinking — "I designed for tenancy from day one" — without needing to see a working SaaS. The artifact has to tell a credible extension story while staying shippable in two weekends.

**Alternatives considered.**

1. **Pure portfolio script (BRIEF baseline).** Fastest (~20h). Tells a thinner product story; doesn't differentiate from other AI-agent portfolio projects on the market. The hand-labeled eval and code-RAG over Hyperswitch are strong, but the surrounding narrative reads as "I built a demo," not "I scoped a product."
2. **Full SaaS prototype.** GitHub App, Atlassian OAuth, multi-tenant DB with RLS, secrets vault, billing surface, install/onboarding flow. ~60–80h. Wrong artifact for the audience — hiring managers will skim the README and the Loom; they won't poke OAuth flows. Time spent on auth and billing is invisible in interviews.
3. **Chosen: tenant-shaped single-tenant.** ~3h above BRIEF baseline (~23h total). Adds a `tenants/<slug>/` directory, a tenant config schema, a config loader, and a "Scaling to SaaS" README section. Tells the full "designed for SaaS" story in code structure and docs without building the auth/billing tax.

**What stays an anti-goal (BRIEF §5 unchanged).** No auth, no billing, no live OAuth, no per-tenant secrets vault, no real multi-tenancy. The README will explicitly call these out as v1 SaaS scope with a recommended approach for each (GitHub App for repo connection, Atlassian OAuth2 for Jira, Supabase RLS for isolation, Supabase Vault or app-level KMS for secrets). Naming the omissions is the point — it shows the omission is deliberate, not accidental.

**What changes in scope.**

- New `tenants/hyperswitch/` directory holds `config.yaml`, `product_profile.yaml`, `ground_truth.csv`, and `bulletins/`. The previous `data/` location is retired.
- Pipeline modules (`ingest`, `classify`, `retrieve`, `assess`, `prioritize`, `github_issue`) accept a `tenant: TenantConfig` argument instead of reading hardcoded paths.
- New `src/tenant/` module with Pydantic models for config validation and a loader.
- Streamlit dashboard surfaces a "Tenant: Hyperswitch (demo)" selector with one option — UI affordance for the multi-tenant story.
- README gets a "Scaling to multi-tenant SaaS" section with the extension-point table.

**How this gets evaluated in interviews.** Expected question: *"Walk me through how you'd onboard a second company to this."* Answer in two parts. (a) In the prototype: drop `tenants/<slug>/config.yaml`, run `index_tenant.py <slug>`, the pipeline picks it up unchanged — demonstrate live in the demo. (b) For a real paying customer: GitHub App install instead of cloned repo, Atlassian OAuth instead of a GitHub Issues target, Supabase RLS keyed on `tenant_id`, vault for tokens, scheduler row per tenant. Show the README section that already names each of these. The answer is the artifact, not improvisation.

---

## 2026-06-05 — Zero-cost stack: Gemini for LLM, Streamlit Cloud + GitHub Actions for hosting

**Decision.** Replace BRIEF's original Claude (Anthropic API) with Google Gemini — `gemini-2.5-pro` for the relevance and impact-assessment stages, `gemini-2.5-flash` for Stage-1 tagging. Replace BRIEF's original Railway hosting with Streamlit Community Cloud (dashboard) and GitHub Actions cron (scheduled assessment runs). Supabase, Voyage AI, and Langfuse Cloud stay as-is — all on free tiers.

**Constraint driver.** Karthik set a hard zero-cost target for the entire prototype lifecycle. Two BRIEF choices broke this: (a) the Claude Code subscription does not extend API access to a deployed Streamlit app — that requires a separate pay-as-you-go Anthropic API key; (b) Railway no longer offers a perpetual free tier (trial credit only). Both had to move.

**Alternatives considered.**

1. **Keep Claude with a small paid budget ($5–20 across project lifetime).** Best raw accuracy on long-doc reasoning. Rejected because the zero-cost constraint is explicit and the accuracy gap is not large enough to warrant breaking it.
2. **Groq Llama 3.3 70B.** Fastest free option, very generous rate limits. Rejected for the reasoning stage because Llama 3.3 underperforms Gemini 2.5 Pro on long-context regulatory text. Held in reserve as a fallback if Gemini rate limits become blocking during the eval.
3. **Render / Fly.io for app hosting.** Both have free tiers. Rejected because Streamlit Community Cloud is purpose-built for Streamlit, deploys directly from GitHub, and matches BRIEF's "demo speed > production polish" stance.
4. **External cron services (cron-job.org, EasyCron).** Rejected because GitHub Actions cron is in-repo, version-controlled, and demos as a clean YAML file — better interview artifact.

**Accuracy tradeoff acknowledged.** Gemini 2.5 Pro on long-doc regulatory reasoning is competitive with but not equal to Claude Sonnet 4.6. The mitigation is the 1M+ context window: full bulletins go in without aggressive chunking, which closes most of the gap. The eval (BRIEF §4 riskiest assumption) will surface any residual gap quantitatively — the precision/recall targets (>85% / >80%) do not change based on the model swap.

**Implications.**

- BRIEF §6 hosting list and data-flow diagram updated to reference Gemini and the new hosting layout.
- BRIEF §8 decisions table updated for Hosting and LLM rows; Scheduler row added.
- New `.github/workflows/weekly-assessment.yml` will be the scheduler artifact (per-tenant cron loops over `tenants/`).
- Secrets move from Railway env vars to Streamlit Cloud secrets + GitHub Actions repository secrets.

**Free-tier risks named in the README (so hiring managers see the awareness, not the surprise).**

- Gemini Pro free-tier rate limits may tighten. Fallback: Flash for both stages, with an accuracy note in the eval write-up.
- Supabase free projects pause after 1 week idle. Mitigation: a weekly GitHub Action that pings the database — one cron line, called out as a deliberate design choice.
- Streamlit Cloud cold-starts after idle (~30s on first visit). Acceptable for demo; flagged in Loom script ("real product would have an always-on tier").
- Voyage free-tier indexing credits are one-time; sufficient for Hyperswitch's ~2M code tokens, but a second tenant's index would need a fresh approach (documented in the "Scaling to SaaS" section).

---

## 2026-06-06 — Narrow v0 bulletin corpus to Visa only

**Decision.** Phase 1 skateboard and Phase 2 eval are scoped to Visa bulletins only. Mastercard, RBI, and other sources are deferred until after the skateboard proves the riskiest assumption (BRIEF §4). The architecture stays generic — tenant config still lists all card networks, classifier prompts reference "card network" generically, code RAG is network-agnostic. Only the *curated corpus* narrows.

**Reasoning.** Karthik's call: "Run it for Visa only. I will understand it and simply extend to others." Three reasons this is the right move:

1. **Riskiest assumption is network-agnostic.** Whether an LLM can classify regulatory-bulletin relevance to a codebase doesn't change with the issuing network. One network's corpus is sufficient to test the hypothesis.
2. **Faster sourcing.** Curating 30 Visa bulletins from one source is meaningfully easier than splitting effort across three networks with different document formats.
3. **Stronger interview narrative.** "I designed for extensibility and proved the pattern on one network — adding Mastercard is a `mkdir` and a corpus drop, no code changes" is a sharper story than "I tested on three networks and the corpus is shallow on each."

**What stays generic.**
- `regulatory_scope.card_networks` in tenant config lists `[visa, mastercard, rupay]` — v0 doesn't know it's Visa-only.
- Classifier prompts reference "card network" generically.
- Code RAG over Hyperswitch is network-agnostic by construction.

**What narrows for v0.**
- `tenants/hyperswitch/bulletins/` contains only Visa-sourced documents.
- BRIEF §4 precision/recall targets (>85% / >80%) measured against Visa-only ground truth.
- Phase 2 hand-labeled `ground_truth.csv` covers Visa only.

**Extension recipe (will be documented in README "Scaling to SaaS" section).** *"To add Mastercard coverage: drop bulletins under `tenants/<slug>/bulletins/`, re-run eval. No code or prompt changes."*

---

## 2026-06-06 — Stage-2 model = Gemini 2.5 Flash (Pro free tier is 0)

**Decision.** Stage 2 (relevance judgment) uses `gemini-2.5-flash` by default, not `gemini-2.5-pro`. Both stages run on Flash. The model is env-configurable (`COMPLY_STAGE2_MODEL`) so a billed key can swap to Pro in one line.

**Why this changed.** The 2026-06-05 decision specified Pro for Stage 2 on the assumption that Gemini 2.5 Pro was available on the free tier. It is not. The Generative Language API returns 429 `RESOURCE_EXHAUSTED` immediately for `gemini-2.5-pro` with `limit: 0` on free-tier projects — the model is paid-tier only. Discovered when the first end-to-end skateboard run hit 429 on every Stage 2 call.

**What this costs.** Stage-2 quality. Pro is the better judge for nuanced relevance calls — borderline bulletins, jurisdictional edge cases, novel surfaces. Flash is good enough for the three curated Visa bulletins (3/3 agreement with hand labels on first run) but the gap will show when the corpus grows and bulletins get harder.

**Mitigation.** (a) Keep `COMPLY_STAGE2_MODEL` env-overridable — the moment billing is enabled, swap to Pro with no code change. (b) Track Stage-2 confidence in the JSON output; the eval can flag low-confidence Flash calls for Pro re-judgment as a future "tiered model" pattern. (c) The two-stage architecture itself is the load-bearing decision — model choice is a swap, not a rewrite.

**Secondary fix in the same patch.** Every Gemini call now has a hard 60s HTTP timeout via `HttpOptions(timeout=60_000)` and a 3-attempt retry with exponential backoff. The first skateboard run hung for 7 hours because the original code passed no timeout, and the google-genai SDK appears to honor server-side `retryDelay` hints on 429s — turning a "Pro is paid-only" error into a silent multi-hour stall. Every Gemini-touching path now fails fast.

**Anti-goal.** No silent fallbacks ("if Pro 429s, fall back to Flash"). The model in use is explicit per-run via env, recorded in run output. Surprises are worse than constraints.
