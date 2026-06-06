# STATUS — 2026-06-06 (morning checkpoint)

> Cold-resume note. Read this before continuing. The two prior context documents
> are **BRIEF.md** (scope, anti-goals, architecture) and **DECISIONS.md**
> (why each load-bearing choice was made). This file is the ephemeral "what's
> done, what's next, what's broken right now."

---

## TL;DR

**Phase 1 (skateboard) is green.** The two-stage Gemini classifier ran
end-to-end on three curated Visa bulletins and **agreed with the hand
labels 3/3** — both mandatory bulletins (CIT/MIT/AFT, 3DS 2.3) classified
as `relevant` with cited surfaces, and the marketing bulletin (Cross-Border
Commerce Program) classified as `not_relevant` with the right reasoning.

Total wall-clock: **~34 seconds** for 3 bulletins (6 Gemini calls). Run
artifact: `outputs/skateboard-hyperswitch-20260606T031402Z.json`.

**One blocker remains: the first git commit / push.** Xcode CLT license is
still not accepted (Karthik to run the command in Terminal.app — see §6 below).

---

## What changed since the last STATUS

### 1. Found and fixed a 7-hour silent hang

The first end-to-end run last night stalled for 7 hours with no progress
output. Diagnosis after the fact: **Gemini 2.5 Pro free-tier limit is 0
requests**. The API returns 429 `RESOURCE_EXHAUSTED` immediately, but the
`retryDelay` hints in the response (`Please retry in 42s.`, `32s`, `22s`…)
appear to drive the google-genai SDK into a multi-hour internal retry loop
when no client-side timeout is set.

**Two fixes shipped together:**

- **Hard timeout + bounded retry on every Gemini call.** `genai.Client` is
  constructed with `HttpOptions(timeout=60_000)`. A `_with_retry` helper
  wraps each call: 3 attempts, exponential backoff (2s → 4s), every
  attempt streams a labeled progress event so you can see exactly which
  stage is in flight and how long it took.
  See: `src/classify/classifier.py:_with_retry`,
  `src/classify/classifier.py:stage1_tag`,
  `src/classify/classifier.py:stage2_relevance`.

- **Stage 2 default switched to Flash.** Both stages now run
  `gemini-2.5-flash` on the free tier. The model is env-overridable via
  `COMPLY_STAGE2_MODEL=gemini-2.5-pro` — a one-line swap the moment billing
  is enabled. See `src/classify/classifier.py:20-24` and
  `DECISIONS.md` (2026-06-06 entry).

A **30s-bounded smoke test** (`scripts/smoke_gemini.py`) verifies the SDK +
key + network path with a single Flash call before the full skateboard runs.
Run it any time the runner feels stuck:

```bash
uv run python scripts/smoke_gemini.py
# expects: [HH:MM:SS] OK in <2s. response: 'ok'
```

### 2. The skateboard now streams live progress

Every run prints a timestamped line per phase, with elapsed time and remaining
count. No more silent multi-hour stalls — if a call is slow, you see it. If
a call dies, you see the exception inside the 60s window. Example from
this morning's run:

```
08:43:28 → [1/3] classifying visa-2026-q1-001 (2026-q1-visa-cit-aft-mandate.md)
08:43:28    stage1: attempt 1/3 sent
08:43:32    stage1: ok in 4.2s
08:43:32    stage2: attempt 1/3 sent
08:43:39    stage2: ok in 7.5s
08:43:39    ✓ done in 11.8s (2 remaining)
```

### 3. Classifier results, this run

| Bulletin | Predicted | Expected | Confidence | Affected surfaces |
| --- | --- | --- | --- | --- |
| `visa-2026-q1-001` (CIT/MIT + AFT mandate) | **relevant** | relevant | 1.00 | authorization_flow, recurring_payments, chargebacks_and_disputes, settlement_and_reconciliation, connector_routing_rules |
| `visa-2026-q1-003` (Cross-Border Commerce — marketing) | **not_relevant** | not_relevant | 1.00 | — |
| `visa-2026-q2-002` (3DS 2.3 protocol update) | **relevant** | relevant | 1.00 | 3ds_authentication, authorization_flow, fraud_signals_and_risk_scoring, chargebacks_and_disputes |

The Stage-2 reasoning quotes specific bulletin language (`"payment
orchestrators handling AFT-eligible transaction flows must..."`) and names
specific profile surfaces — exactly the eval criterion in BRIEF §4. Full
reasoning is in the JSON artifact.

**Sanity check, not validation.** Three bulletins is too small to claim the
precision/recall targets in BRIEF §4 are met. It validates that the
two-stage architecture and prompts work end-to-end and that Flash is good
enough for clear-cut cases. The harder eval — 30+ bulletins, hand-labeled,
including borderline cases — is Phase 2.

---

## State of the codebase

- **Connections verified:** Gemini Flash, Voyage (1024-dim), Supabase auth,
  Langfuse `auth_check` — see `scripts/verify_connections.py`.
- **Tenant config layer:** Pydantic-validated, loads from
  `tenants/hyperswitch/{config.yaml,product_profile.yaml}`. Pipeline
  modules take a `TenantConfig` argument, not hardcoded paths. The
  multi-tenant story is in the code structure already.
- **Classifier:** `src/classify/classifier.py` — two stages, structured
  output via Pydantic + `response_schema`, timeouts + retries + progress
  hooks.
- **Bulletin ingest:** `src/ingest/bulletin.py` parses YAML frontmatter
  conventions documented in `tenants/hyperswitch/bulletins/README.md`
  (sourcing transparency, `synthesized: true` flag).
- **Runner:** `scripts/run_skateboard.py` — full end-to-end with Rich
  table, agreement scoring, JSON artifact under `outputs/`.

---

## Task list (post-Phase-1)

**Done overnight:**

- `[x]` Verify 4 API connections respond
- `[x]` Set up Python project with uv
- `[x]` Scaffold `tenants/hyperswitch/`
- `[x]` Scaffold `src/` module skeleton
- `[x]` Write README skeleton with "Scaling to SaaS" section
- `[x]` Curate 3 public Visa bulletins as markdown
- `[x]` Build two-stage Gemini classifier
- `[x]` Add timeouts + retries + live progress to every Gemini call
- `[x]` Run classifier on Visa bulletins, capture results

**Blocked / pending:**

- `[ ]` **First commit + push to `karthikeyan-smg1/complyagent`** —
  blocked on Xcode CLT license (see §6).

**Next up (Phase 2 — hand-labeled eval, the BRIEF §4 numerical claim):**

- `[ ]` Curate 15-25 more Visa bulletins (mix of mandatory / informational
  / marketing / out-of-scope jurisdiction) — enough to make precision /
  recall meaningful.
- `[ ]` Hand-label them in `tenants/hyperswitch/ground_truth.csv` with
  expected relevance + priority.
- `[ ]` Build `scripts/run_eval.py` — runs classifier over the corpus and
  computes precision / recall / confusion matrix against ground truth.
- `[ ]` Record one run in `outputs/eval-baseline.json` to anchor future
  prompt changes.

---

## 6. Blockers needing your hand

### Xcode license — NOT accepted yet

Last night you said you accepted the license, but the check still says
otherwise:

```
$ sudo xcodebuild -license check
You have not agreed to the Xcode license agreements. Please run
'sudo xcodebuild -license' from within a Terminal window to review and
agree to the Xcode and Apple SDKs license.
```

This blocks `git` (which is fronted by `xcrun`). **Open Terminal.app
(not VS Code, not iTerm) and run:**

```bash
sudo xcodebuild -license
```

Scroll to the bottom of the license text with `space`, type `agree`, hit
return, enter your Mac password. After that:

```bash
cd ~/Documents/Claude/ComplianceAgent
git init && git add -A && git status   # sanity check before committing
```

Once that's clean, ping me and I'll do the first commit + push to
`karthikeyan-smg1/complyagent` in the next session.

### (Reminder) Gemini key hygiene

A Gemini API key was pasted in chat during setup last night, so logs /
transcripts have it. Rotate it in AI Studio when convenient (Get API key
→ delete the old one → create new → update `.env` `GEMINI_API_KEY=`).
Costs <60 seconds and you have nothing standing on the old one.

---

## How to resume in the next session

```bash
cd ~/Documents/Claude/ComplianceAgent
export PATH="$HOME/.local/bin:$PATH"

# 1. Sanity-check the network + SDK path (15s bounded)
uv run python scripts/smoke_gemini.py

# 2. Re-run the skateboard if you want fresh numbers
uv run python scripts/run_skateboard.py hyperswitch

# 3. Inspect the latest artifact
ls -lt outputs/ | head -3
```

If `scripts/smoke_gemini.py` ever takes more than ~5 seconds: the network
is the problem, not the code. Check your wifi / VPN / corporate proxy.

---

## Process lesson for me (Claude)

The 7-hour stall was on me. Every external call from an autonomous run
needs (a) a hard client-side timeout, (b) bounded retries, and (c) a
visible progress line per attempt. I added all three after the fact, but
the right time was *before* I started the long-running run. Going forward
for any process the user can't watch in real time: timeout-bounded,
progress-streaming, and never trust SDK defaults to fail fast.
