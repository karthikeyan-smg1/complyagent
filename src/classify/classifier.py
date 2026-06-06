"""Two-stage Gemini classifier — the riskiest-assumption test (BRIEF §4).

Stage 1 (Gemini 2.5 Flash) tags the bulletin against a payments taxonomy.
Stage 2 (Gemini 2.5 Pro) given the tags + bulletin + product profile, judges
whether the bulletin requires code or behavior changes in the target codebase.

Both stages use Gemini structured output (response_schema) to enforce JSON
matching Pydantic models below — no prompt-jailbreaking or post-hoc parsing.

Every Gemini call is bounded by a hard HTTP timeout and retried with
exponential backoff. Without this, a network stall (WiFi sleep, transient
proxy, dropped TLS) silently hangs the runner.
"""
from __future__ import annotations

import os
import time
from typing import Callable, Literal, TypeVar

import yaml
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Stage 2 default is Flash (not Pro): Gemini 2.5 Pro free-tier limit is 0
# requests — the API returns 429 immediately. Swap to "gemini-2.5-pro" via env
# the moment a billed key is wired up; Pro is the correct judgment model.
STAGE1_MODEL = os.environ.get("COMPLY_STAGE1_MODEL", "gemini-2.5-flash")
STAGE2_MODEL = os.environ.get("COMPLY_STAGE2_MODEL", "gemini-2.5-flash")

DEFAULT_TIMEOUT_MS = 60_000  # 60s per call — generous for Pro, fails fast on stall
DEFAULT_MAX_ATTEMPTS = 3
RETRY_BASE_SECONDS = 2.0

T = TypeVar("T")


class Stage1Tags(BaseModel):
    network: Literal["visa", "mastercard", "rupay", "amex", "discover", "other"]
    topic: Literal[
        "authorization", "3ds", "tokenization", "mandate", "refund",
        "chargeback", "settlement", "fraud", "pci", "kyc",
        "interchange", "reporting", "other",
    ]
    action_type: Literal[
        "regulatory_change", "operational_notice", "product_launch",
        "rate_change", "deprecation", "marketing",
    ]
    effective_date: str | None = Field(
        default=None,
        description="ISO 8601 date if a clear effective date is stated, else null.",
    )
    mandatory: bool = Field(
        description="True only if compliance action is required; false if optional/informational/marketing.",
    )
    summary: str = Field(description="One sentence describing what the bulletin says.")


class Stage2Result(BaseModel):
    relevant: bool = Field(
        description="True if the bulletin requires the target product to change behavior in a surface it supports.",
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the relevance judgment, 0.0 to 1.0.",
    )
    reasoning: str = Field(
        description="2-3 sentences citing specific bulletin language and specific product surfaces.",
    )
    affected_surfaces: list[str] = Field(
        default_factory=list,
        description="Surfaces from the product profile this bulletin affects. Pick only from the profile's surfaces list.",
    )


class ClassificationResult(BaseModel):
    bulletin_id: str
    tags: Stage1Tags
    relevance: Stage2Result


STAGE1_SYSTEM = """You are a payments-domain classifier tagging regulatory and operational bulletins from card networks and central banks.

Tag the bulletin precisely against the schema. Choose the closest enum value; do not invent new ones.

Critical: `mandatory` is TRUE only when the bulletin clearly requires compliance action — for example, a mandate with an effective date, a rule change with a penalty for non-compliance, or a protocol upgrade with a deprecation deadline. Marketing announcements, opt-in promotional programs, and informational product news are NOT mandatory.

Keep the `summary` to one sentence."""


STAGE2_SYSTEM = """You are a payments-domain relevance classifier. Given a regulatory bulletin and a target product's profile, decide whether the bulletin requires code or behavior changes in that product.

The product profile lists the rails, networks, jurisdictions, payment methods, and surfaces the product actually supports.

A bulletin is RELEVANT (relevant=true) if it requires the product to change behavior in a surface it already supports.

A bulletin is NOT relevant (relevant=false) if it concerns:
- surfaces the product does not support,
- jurisdictions outside the product's scope,
- non-regulatory marketing or optional promotional programs,
- areas listed in the product's `out_of_scope`.

Ground your `reasoning` in specific language from the bulletin AND specific surface names from the product profile. Two to three sentences. Be conservative: when in doubt, mark relevant=true with lower confidence and explain the uncertainty.

For `affected_surfaces`, pick only from the product profile's `surfaces:` list. Do not invent surface names."""


def _client(timeout_ms: int = DEFAULT_TIMEOUT_MS) -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )


def _with_retry(
    fn: Callable[[], T],
    *,
    label: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    on_event: Callable[[str], None] | None = None,
) -> T:
    """Run fn with bounded retries. on_event receives short progress strings."""
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        if on_event:
            on_event(f"{label}: attempt {attempt}/{max_attempts} sent")
        t0 = time.monotonic()
        try:
            out = fn()
            if on_event:
                on_event(f"{label}: ok in {time.monotonic() - t0:.1f}s")
            return out
        except Exception as e:  # noqa: BLE001
            last_err = e
            elapsed = time.monotonic() - t0
            if on_event:
                on_event(
                    f"{label}: {type(e).__name__} after {elapsed:.1f}s — {str(e)[:120]}"
                )
            if attempt == max_attempts:
                break
            backoff = RETRY_BASE_SECONDS * (2 ** (attempt - 1))
            if on_event:
                on_event(f"{label}: backing off {backoff:.1f}s before retry")
            time.sleep(backoff)
    assert last_err is not None
    raise last_err


def stage1_tag(
    bulletin_text: str,
    *,
    client: genai.Client | None = None,
    on_event: Callable[[str], None] | None = None,
) -> Stage1Tags:
    c = client or _client()

    def call() -> Stage1Tags:
        resp = c.models.generate_content(
            model=STAGE1_MODEL,
            contents=bulletin_text,
            config=types.GenerateContentConfig(
                system_instruction=STAGE1_SYSTEM,
                response_mime_type="application/json",
                response_schema=Stage1Tags,
                temperature=0.0,
            ),
        )
        if resp.parsed is None:
            raise RuntimeError(f"stage1: parsing failed. Raw text: {resp.text!r}")
        return resp.parsed

    return _with_retry(call, label="stage1", on_event=on_event)


def stage2_relevance(
    bulletin_text: str,
    tags: Stage1Tags,
    product_profile: dict,
    *,
    client: genai.Client | None = None,
    on_event: Callable[[str], None] | None = None,
) -> Stage2Result:
    c = client or _client()
    profile_yaml = yaml.safe_dump(product_profile, sort_keys=False)
    tags_json = tags.model_dump_json(indent=2)

    user_content = (
        "# Bulletin tags (Stage 1 output)\n"
        f"{tags_json}\n\n"
        "# Target product profile\n"
        f"```yaml\n{profile_yaml}```\n\n"
        "# Bulletin text\n"
        f"{bulletin_text}\n"
    )

    def call() -> Stage2Result:
        resp = c.models.generate_content(
            model=STAGE2_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=STAGE2_SYSTEM,
                response_mime_type="application/json",
                response_schema=Stage2Result,
                temperature=0.0,
            ),
        )
        if resp.parsed is None:
            raise RuntimeError(f"stage2: parsing failed. Raw text: {resp.text!r}")
        return resp.parsed

    return _with_retry(call, label="stage2", on_event=on_event)


def classify_bulletin(
    bulletin_id: str,
    bulletin_text: str,
    product_profile: dict,
    *,
    client: genai.Client | None = None,
    on_event: Callable[[str], None] | None = None,
) -> ClassificationResult:
    c = client or _client()
    tags = stage1_tag(bulletin_text, client=c, on_event=on_event)
    relevance = stage2_relevance(
        bulletin_text, tags, product_profile, client=c, on_event=on_event
    )
    return ClassificationResult(bulletin_id=bulletin_id, tags=tags, relevance=relevance)
