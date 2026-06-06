# STATUS — 2026-06-06 (afternoon checkpoint)

> Cold-resume note. Read this before continuing. The two prior context
> documents are **BRIEF.md** (scope, anti-goals, architecture) and
> **DECISIONS.md** (why each load-bearing choice was made).

---

## TL;DR

**v0 is shipped end-to-end.** Two-stage classifier + 10-bulletin Visa corpus
+ hand-labeled eval + multi-tab Streamlit dashboard, all pushed to
`karthikeyan-smg1/complyagent`. **First clean eval: 10/10 — precision 1.000,
recall 1.000, F1 1.000.**

**One remaining action lives with you (5 minutes in a browser):** connect the
GitHub repo to Streamlit Community Cloud and click Deploy. After that the
demo URL is live and resume-ready. Step-by-step at the bottom of this file.

---

## Repo state

- **Live source:** https://github.com/karthikeyan-smg1/complyagent
- **Latest commit:** `788589e Expanded corpus, eval, Streamlit dashboard,
  rate limiter`
- **History:** two commits, clean (the initial scaffold was force-pushed to
  drop the API-probe debris from the first push).

### What's shipped

- `tenants/hyperswitch/bulletins/` — 10 Visa bulletins:
  - 5 mandatory/relevant: AFT (CIT/MIT), VTS network-token recurring
    mandate, 3DS 2.3, VDRP dispute pre-arbitration evidence v4, India IRF
    rate adjustment.
  - 5 not-relevant: Cross-Border marketing program, Marketplace Operator
    Settlement Reporting (out-of-scope role), stablecoin settlement pilot
    (treasury-only), Click to Pay 2.0 (consumer UX, not orchestrator),
    issuer-side card production refresh.
  - All synthesized from public Visa programs with `synthesized: true`;
    sourcing transparency in `tenants/hyperswitch/bulletins/README.md`.
- `src/classify/classifier.py` — two-stage Gemini classifier, both stages
  default to `gemini-2.5-flash-lite`. Env-overridable models. Pydantic
  `response_schema` enforcement. Hard 60s HTTP timeout per call.
  Token-bucket rate limiter (8 RPM default, env-overridable via
  `COMPLY_GEMINI_RPM`). Server-`retryDelay`-aware retry backoff.
- `src/eval/metrics.py` + `scripts/run_eval.py` — runs the classifier
  across the full corpus, computes precision / recall / F1 / accuracy,
  writes `outputs/eval-<ts>.json` + `outputs/latest-eval.json`,
  regenerates `tenants/<slug>/ground_truth.csv` as a flat CSV mirror.
  Has a circuit breaker (3 consecutive 429s aborts the run).
- `streamlit_app.py` — six-tab dashboard (Overview / Inbox / Eval /
  Design / Roadmap / About) reading `outputs/latest-eval.json`.
  **No live LLM calls from the page** — every visitor sees the same
  pre-computed numbers, no quota burn.
- `.streamlit/config.toml` + `requirements.txt` for Streamlit Cloud.
- `outputs/eval-hyperswitch-20260606T074005Z.json` — the canonical
  10/10 eval. Pointed at by `outputs/latest-eval.json`.

### First clean eval result

| Metric | Value |
|---|---|
| Bulletins | 10 (5 relevant + 5 not_relevant) |
| TP / FP / TN / FN | 5 / 0 / 5 / 0 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| Accuracy | 1.000 |
| Wall-clock | 126.6s (including two ~48s rate-limiter sleeps) |

The dashboard already calls this out honestly in the **Eval** tab:
*"corpus is small (10 bulletins, Visa only) and synthesized from public Visa
programs — this is a sanity check on the two-stage architecture, not a SOTA
claim. The next iteration expands to 30+ bulletins…"*

---

## Lessons from today (in DECISIONS.md but worth repeating)

- **Gemini 2.5 Pro free-tier limit = 0 requests.** Paid-only.
- **Gemini 2.5 Flash free-tier limit = 20 requests/day.** Tight enough that
  repeat eval runs blow through it. Burned this discovering it.
- **Gemini 2.5 Flash-Lite free-tier limit = 1000 requests/day.** Comfortable
  for development. Default for both stages in v0; env-swap to Flash + Pro
  on a billed key.
- **Always set client-side timeouts on external SDKs.** The 7-hour stall
  yesterday was the google-genai SDK honoring a server `retryDelay` hint
  with no client timeout to cap it. Hard-learned the standard rule for
  long-running calls: bounded timeout + bounded retry + streamed progress.
- **For free-tier-hosted demos, render pre-computed artifacts.** Every
  visitor triggering live LLM calls = shared-quota burn + non-deterministic
  numbers. The dashboard reads a committed JSON; eval refresh is a
  deliberate CLI invocation.

---

## What's deliberately deferred to v0.2

- Code RAG over Hyperswitch (Voyage embeddings + Supabase pgvector).
- Impact-assessment LLM stage (bulletin + retrieved code chunks → draft).
- Deterministic priority rubric (P0–P3).
- GitHub Issue creation on the Hyperswitch fork.
- GitHub Actions cron that runs the pipeline weekly and commits refreshed
  `latest-eval.json`.

Rationale: the **Roadmap** tab in the dashboard names these explicitly as
v0.2, so a hiring manager reading the artifact sees that "agent loop" is
scoped and understood, not just absent.

---

## YOUR action: deploy to Streamlit Community Cloud (~5 minutes)

This is the only thing standing between us and the public demo URL. Cannot
be automated from here — Streamlit Cloud needs you to click through their
flow once. Then it self-rebuilds on every push.

1. Open **https://share.streamlit.io** in a new tab.
2. Click **"Sign in with GitHub"**. Authorize Streamlit on
   `karthikeyan-smg1`.
3. On the dashboard, click **"Create app"** (top right) →
   **"Deploy a public app from GitHub"**.
4. Fill in:
   - **Repository:** `karthikeyan-smg1/complyagent`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** something memorable like `complyagent` (gives you
     `https://complyagent.streamlit.app`)
5. **Advanced settings → Python version:** 3.11 (or 3.12 — both work).
6. **Secrets:** leave empty. The dashboard does not need any secrets to
   render the cached results. (If you later add a "live classifier" mode,
   that's the place for `GEMINI_API_KEY`.)
7. Click **"Deploy!"**. Initial build takes 3-5 minutes; subsequent pushes
   redeploy in ~30 seconds.

Once you have the URL:
- Paste it on the **Live demo** line of `README.md` (currently a
  placeholder).
- Generate a QR code at https://qrcode.show or similar — drop on the
  resume.
- Send me the URL and I'll do a final pass: paste it into README, the
  dashboard sidebar, and the LinkedIn-shareable copy.

If anything in the Streamlit Cloud flow goes sideways, paste the error
here and I'll debug.

---

## Tomorrow / next session

- Verify the live URL works and update README, dashboard sidebar, and
  optional `<meta>` tags in the dashboard.
- (Optional) Rotate the Gemini API key that was pasted in chat yesterday
  — 60 seconds in AI Studio.
- (Optional) Start v0.2: code RAG indexer + impact assessment + Issue
  creation. Closes the agent loop end-to-end and is the differentiator vs
  classifier-only demos.

---

## Quick commands

```bash
# Sanity test
uv run python scripts/smoke_gemini.py

# Refresh eval (writes outputs/latest-eval.json — commit + push to redeploy)
uv run python scripts/run_eval.py hyperswitch

# Boot dashboard locally
uv run streamlit run streamlit_app.py

# Inspect latest eval artifact
python3 -c "import json; print(json.dumps(json.load(open('outputs/latest-eval.json'))['metrics'], indent=2))"
```
