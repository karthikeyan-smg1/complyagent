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

**Constraint driver.** Karthikeyan set a hard zero-cost target for the entire prototype lifecycle. Two BRIEF choices broke this: (a) the Claude Code subscription does not extend API access to a deployed Streamlit app — that requires a separate pay-as-you-go Anthropic API key; (b) Railway no longer offers a perpetual free tier (trial credit only). Both had to move.

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

**Reasoning.** Karthikeyan's call: "Run it for Visa only. I will understand it and simply extend to others." Three reasons this is the right move:

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

---

## 2026-06-06 — Default both stages to `gemini-2.5-flash-lite` (Flash free-tier daily limit is 20)

**Decision.** Stage 1 and Stage 2 both default to `gemini-2.5-flash-lite`. Both are env-overridable via `COMPLY_STAGE1_MODEL` / `COMPLY_STAGE2_MODEL` for billed-key production deployments (`gemini-2.5-flash` for Stage 1, `gemini-2.5-pro` for Stage 2).

**Why this changed (again).** The previous entry switched Stage 2 from Pro → Flash on the assumption that Flash daily limits were ~250 requests. A second eval run today hit immediate 429s after the first 8 successful calls. The Gemini server then surfaced the actual limit: `quotaValue: '20'` for `gemini-2.5-flash` on the free tier. Twenty Flash requests per day is not enough for repeated eval runs (10 bulletins × 2 stages × N iterations).

**What Flash-Lite gives up.** Stage 2 quality on borderline bulletins. Flash-Lite is a smaller distillation; for clear-cut bulletins (a stablecoin pilot that explicitly says "no action required for orchestrators", a CIT/MIT mandate with explicit acquirer obligations) it judges correctly, but on the harder borderline cases where the bulletin language is ambiguous, Flash and Pro materially outperform.

**Why it's still the right v0 default.** Three reasons. (1) The free-tier constraint is what we have — Pro is paid-only, Flash is 20/day. Flash-Lite has 1000/day. (2) The two-stage architecture and prompt engineering are the load-bearing decisions; model choice is a one-line env swap. (3) The dashboard renders pre-computed `outputs/latest-eval.json` rather than calling the LLM live, so a hiring-manager visiting the demo URL doesn't burn any quota — meaning the model that matters in production is the env-set one for the cron, not the static-page one.

**Eval baseline.** First clean end-to-end run on 10 bulletins: precision 1.000, recall 1.000, F1 1.000, accuracy 1.000 (5 TP / 0 FP / 5 TN / 0 FN). Wall-clock 126s including two ~48s rate-limiter sleeps. The dashboard surfaces this honestly with a "the corpus is small and synthesized — this is a sanity check, not a SOTA claim" caveat.

**Secondary improvements in the same patch.**

- **Client-side rate limiter** (8 RPM default, env-overridable via `COMPLY_GEMINI_RPM`) — token-bucket-ish; tracks request timestamps in a 60s sliding window and blocks before the next call when at cap. Prevents bursting past per-minute quotas.
- **Server-hint-aware retry backoff** — when a 429 carries a `retryDelay` hint, we honor it (instead of exponential backoff). Server delays of 22-60s are common when the free-tier daily window is partially depleted.
- **Circuit breaker** in `run_eval.py` — three consecutive 429-driven failures abort the run instead of burning 4 minutes × N bulletins on retry.

**Anti-goal.** No automatic model fallback. If the configured Stage-2 model 429s, we surface the error and stop; we don't silently swap to a smaller model mid-run. Surprises in observability are worse than constraints.

---

## 2026-06-06 — Streamlit dashboard renders pre-computed eval, no live LLM calls

**Decision.** The Streamlit dashboard reads `outputs/latest-eval.json` (committed to the repo) and renders the most recent classification + eval results. There is no "Run classifier" button. Live re-classification is a deliberate CLI invocation (`uv run python scripts/run_eval.py <tenant>`) that refreshes the committed artifact, which is then redeployed via the standard git push → Streamlit Cloud auto-rebuild.

**Why.** Three forcing functions: (1) Gemini free-tier daily quota is 20 Flash + 1000 Flash-Lite — every visitor triggering live calls burns the shared quota in minutes. (2) Streamlit Cloud's shared environment doesn't support per-visitor API key isolation. (3) Live calls would make the headline precision/recall numbers non-deterministic; a hiring manager seeing different numbers on each refresh would lose trust in the eval.

**What this rules out.** The "let me classify this bulletin in real time" demo. We trade away that bit of interactivity for: deterministic numbers, free-tier-safe public hosting, and a clear separation between *what the agent produced* (artifact) and *how to operate it* (CLI).

**Alternative considered.** Per-visitor secrets via Streamlit Cloud's user-supplied secrets pattern (visitor pastes their own key). Rejected — adds friction at the top of the demo funnel and the audience is hiring managers, not power users.

**Implication for the next iteration.** The GitHub Actions cron (Roadmap §1) is the eval-refresh mechanism. Each cron run = new bulletins ingested → classifier re-run → `latest-eval.json` committed → Streamlit Cloud redeploys automatically. Dashboard freshness is bounded by cron interval, not by visitor interaction.

---

## 2026-06-07 — Stratified eval corpus: 10 clear + 6 adversarial bulletins

**Decision.** Expand the eval corpus to 16 bulletins, split into two strata: `clear` (10 — bulletins whose body explicitly states applicability) and `adversarial` (6 — designed around specific named failure modes). Every bulletin's frontmatter carries `difficulty` and, where adversarial, `failure_mode`. The eval reports overall + per-stratum precision / recall / F1, and the dashboard surfaces both.

**Why.** The first 10-bulletin run hit precision 1.000 and recall 1.000. A senior reviewer immediately and correctly flagged that as suspicious: the bulletins I authored mostly said things like *"no action required for orchestrators"* in plain English. The classifier wasn't reasoning about relevance — it was extracting an explicit assertion. A perfect score on a corpus where the answer is in the body proves nothing.

**The six adversarial bulletins target named failure modes.** Each is realistic-sounding, sourced to a plausible public Visa program, and engineered to test one specific reasoning failure:

| # | Bulletin | Failure mode tested | Expected label |
|---|---|---|---|
| visa-2026-q2-011 | Visa Direct B2C push-payments expansion | `surface_overlap` — mentions tokens/3DS/authorization surfaces Hyperswitch has, but is opt-in for issuer banks doing OCT | not_relevant |
| visa-2026-q2-012 | Visa Account Updater v3.0 | `wording_trap` — bulletin says "acquirers" throughout, but the operational integration party is the merchant-side card-on-file operator (i.e., Hyperswitch) | relevant |
| visa-2026-q3-013 | BASE II clearing endpoint TLS migration | `surface_overlap` — mentions "settlement" surface but is pure infrastructure for direct-connected acquirers; orchestrators never touch BASE II | not_relevant |
| visa-2026-q2-014 | CE 3.0 expansion to in-app digital goods | `optional_but_operationally_required` — formally opt-in, no rule penalty, but the dispute-win-rate math makes it mandatory in practice for orchestrators handling chargebacks for in-app merchants | relevant |
| visa-2026-q3-015 | UK SCA post-Brexit divergence | `jurisdiction_edge_and_issuer_language` — UK is in Hyperswitch's jurisdiction list, but the bulletin frames the rule as issuer-side; acceptance-side must still surface new exemption flags | relevant |
| visa-2026-q3-016 | Decline reason code granularity v2 | `surface_mention_but_no_required_change` — explicitly mentions authorization_flow, but the bulletin is unambiguous that consumption is optional with zero penalty for not consuming | not_relevant |

**How the dashboard will read this.** The Eval tab surfaces both the overall row *and* a "Stratified by difficulty" row, with a caption explicitly directing the reviewer: *"the adversarial row is the one that matters."* If the classifier hits 100% on the clear cohort and (say) 67% on adversarial, the headline number drops to ~88% — which is more honest than a misleading 1.000.

**What this rules out.** Cooking the corpus to a target accuracy number. If the classifier turns out to be worse than 80% on the adversarial cohort, that's the result; the dashboard surfaces it and the failure modes go on the roadmap as prompt-engineering or model-upgrade targets.

**Anti-goal.** No retroactive "expected_relevance" relabeling after running the classifier. Labels are set at bulletin-authoring time, in frontmatter, in version control. The eval reports what the model produced against what was labeled — full stop. If the classifier disagrees and the model is right, that's a label bug, surfaced via DECISIONS.md as a separate entry — not by quietly editing the frontmatter.

---

## 2026-06-07 — Cost tracking + per-run USD budget guard; billing enabled

**Decision.** Every Gemini call records `prompt_token_count` and `candidates_token_count` from the response's `usage_metadata`; the classifier converts these to a USD estimate using a model-keyed list-price table (`PRICING_USD_PER_MILLION` in `src/classify/classifier.py`). Per-bulletin and per-run costs are written to the eval JSON and displayed in the dashboard. The eval script enforces a **hard per-run USD cap** (`COMPLY_USD_BUDGET`, default $0.50) and aborts mid-run if the cumulative spend reaches the cap.

**Why.** Karthikeyan enabled Gemini billing to lift the 20-RPD free-tier cap, with a stated **monthly budget of INR 100** (~$1.20). Without instrumentation, a misconfigured model swap (e.g., Pro for both stages) could burn the monthly budget in a single eval — Pro is 12× the per-token cost of Flash-Lite. Cost tracking + a per-run cap turn that risk into an aborted run, not a billing surprise.

**Default cap rationale.** A Flash-Lite full eval (16 bulletins × 2 stages, ~150K tokens) costs ~$0.02. Flash costs ~$0.06. Pro-on-Stage-2 costs ~$0.15. The $0.50 default leaves 3× headroom for the most expensive Pro run while hard-stopping any runaway.

**First post-billing run.** 16 bulletins classified end-to-end in 63 seconds at a total cost of **$0.0053 (~₹0.44)** — 0.4% of the monthly budget. The full 100% precision / recall result was preserved.

**A separate honesty caveat surfaced during this run.** Even my "adversarial" bulletins still contain explicit phrases like "such as payment orchestrators" or "No action is required for payment orchestrators" in the body. The classifier sometimes finds the answer in the body rather than reasoning about it. The eval tab now calls this out directly; the rigorous next iteration needs either real Visa bulletins or a re-writer that strips out role-mentions while preserving operational signal.

**What the budget guard does not do.** It does not enforce a *monthly* spend cap — that would require persistent state (e.g., a `~/.complyagent/spend-log.json` file). For a single-user prototype with a 30-second eval that costs ₹0.44, the per-run cap is sufficient. If multiple processes / cron-driven evals start sharing the same key, the monthly cap belongs in a wrapper or a separate spend-budgeter.

**Anti-goal.** No automatic cost-saving model downgrade. If Stage-2 is configured to Pro and the run would exceed the cap, the run aborts — it does not silently swap to Flash-Lite. Surprises in eval reproducibility are worse than constraints.

---

## 2026-06-07 — Tightened adversarial bulletins: stripped role-mentions, model still 6/6

**Decision.** Rewrite the 6 adversarial bulletins to remove every explicit *payment orchestrator / PSP / payment service provider / gateway* mention while preserving the operational signal (message-format references, surface vocabulary, rule structure). Re-run the eval. Surface whatever happens honestly — including a failure if the model breaks.

**Why.** The previous eval result (16/16, precision and recall 1.000) was suspicious. Reading the per-bulletin reasoning revealed the classifier was citing phrases like "such as payment orchestrators" or "No action is required for payment orchestrators" — phrases I (the bulletin author) had unconsciously left in. The model was reading the answer, not reasoning to it. A perfect score on an eval where I gave away the answer is meaningless.

**The rewrites.** Every adversarial bulletin now uses operationally-defined phrasing for the responsible party instead of role-names. Examples:

- Visa Account Updater: *"any entity that holds the canonical stored-credential record for a merchant operating recurring billing or mandate-based card-on-file flows on Visa rails"* (instead of "acquirers and payment orchestrators").
- UK SCA: *"the party that constructs and emits the UK-region card-not-present authorization request — whichever system holds the authentication-exemption flagging logic"* (instead of "acquirers, payment service providers, payment gateways, and payment orchestrators").
- BASE II: removed the explicit "out of scope for payment orchestrators" callout entirely; left only "direct-connected acquiring banks, issuing banks, and processors must migrate."
- Visa Direct B2C: removed the "no action required for merchant-side parties — acquirers, gateways, PSPs, orchestrators" enumeration; the bulletin now only specifies what issuing banks must do.

A grep across all 6 adversarial bulletins now returns **zero matches** for `orchestrator|PSP|payment service provider|gateway`. The model has no keyword shortcut left.

**Result.** On the tightened set, the classifier still classified all 6 adversarial bulletins correctly (3 relevant + 3 not-relevant, all matching the hand-labels). The per-bulletin reasoning is qualitatively different from the first run: instead of citing role-names, it cites *profile surface names* and connects them to specific operational changes in the bulletin. Examples:

- Account Updater (relevant): *"The product profile supports `tokenization_and_network_tokens` and `recurring_payments` surfaces, which are directly impacted by the need to handle updated network tokens and refresh stored credentials."*
- BASE II (not_relevant): *"The product profile does not indicate direct connectivity to Visa's clearing network... The affected surface `settlement_and_reconciliation` is not directly impacted as the product does not appear to be a direct-connected institution."*
- Visa Direct B2C (not_relevant): *"The target product, Hyperswitch, is an orchestrator that handles transactions at the merchant acceptance flow, not on the issuing bank side."*

This is the reasoning chain the two-stage architecture is supposed to demonstrate: read the bulletin, read the product profile, decide whether the operational changes apply to surfaces the product supports.

**What this still does not prove.** A 6-bulletin adversarial cohort is too small to claim a calibrated model. Confidence is saturated at 1.00 on every call — there is no spread to suggest the model is differentiating its certainty. No cross-network test has been run (a Visa-tuned classifier applied to a Mastercard or RBI bulletin may confabulate). These remain on the roadmap.

**Cost.** Full 16-bulletin re-eval after the rewrites cost **$0.0052 (~₹0.44)** — same as the previous run. Cumulative spend today on the project remains under $0.02 (~₹2). Hard per-run cap at $0.50 protected us throughout.
