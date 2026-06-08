"""Stage 3 — impact assessment.

Given (bulletin + Stage 1/2 outputs + retrieved code chunks + product profile),
the LLM produces a structured impact assessment: which files must change,
what the change looks like at a high level, and the engineering effort
estimate. Same hardening pattern as the classifier — structured output via
Pydantic, hard timeout, server-hint-aware retry, cost tracking.
"""
from __future__ import annotations

import os
from typing import Callable, Literal

import yaml
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.classify.classifier import (
    DEFAULT_TIMEOUT_MS,
    CostEntry,
    _with_retry,
    estimate_cost_usd,
)
from src.classify.classifier import Stage1Tags, Stage2Result  # noqa: F401  (re-export-friendly)
from src.rag.index import IndexedChunk


STAGE3_MODEL = os.environ.get("COMPLY_STAGE3_MODEL", "gemini-2.5-flash-lite")


class AffectedFile(BaseModel):
    path: str = Field(description="Relative path of the file as cited in the retrieved chunks.")
    line_range: str = Field(
        default="",
        description="Approximate line range from the retrieved chunk (e.g., '150-200'). Empty if unknown.",
    )
    rationale: str = Field(
        description="One sentence on why this file is affected by the bulletin.",
    )


class ImpactAssessment(BaseModel):
    impact_summary: str = Field(
        description="2-3 sentence summary of how the bulletin lands on this codebase.",
    )
    affected_files: list[AffectedFile] = Field(
        default_factory=list,
        description="Files most likely affected, derived only from the retrieved code chunks. "
                    "Do not invent paths not present in the retrieved set.",
    )
    suggested_change: str = Field(
        description="High-level outline of the engineering change required. "
                    "Concrete enough to file as a ticket; not a full implementation.",
    )
    estimated_effort: Literal["small", "medium", "large"] = Field(
        description="small = a few hours of work; medium = a few days; large = multi-week.",
    )


STAGE3_SYSTEM = """You are a senior payments engineer reviewing a regulatory bulletin against a specific codebase's source files.

You receive:
1. The bulletin text.
2. The Stage 1 tags (network, topic, action_type, etc.) and Stage 2 relevance reasoning.
3. A set of top-k retrieved code chunks from the target codebase, each labeled with its file path and line range.
4. The target product profile.

Produce a structured impact assessment:

- `impact_summary`: 2-3 sentences naming what changes in the codebase and why.
- `affected_files`: cite ONLY files that appear in the retrieved chunks. Do not invent paths. Each entry should pick the most relevant file paths from the retrieved set, with a one-sentence rationale tying the bulletin requirement to the file's role.
- `suggested_change`: a concrete, engineering-grade outline of the work — message-field changes, new event handlers, new validation, new storage requirements, etc. Avoid generic phrasing like "update the relevant code."
- `estimated_effort`: small (hours), medium (days), or large (multi-week). Weight by surface count, message-format changes, and persistence changes.

Be specific. Cite bulletin language and code-chunk excerpts where useful. If retrieved chunks don't include the obvious affected file, note that in `impact_summary` (the index may need expansion) rather than inventing a path."""


def _client(timeout_ms: int = DEFAULT_TIMEOUT_MS) -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))


def _format_chunks(chunks: list[IndexedChunk]) -> str:
    blocks: list[str] = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(
            f"### Chunk {i} — `{c.line_span}` (cosine score {c.score:.3f}, module `{c.module_path}`)\n"
            f"```rust\n{c.text}\n```\n"
        )
    return "\n".join(blocks)


def assess_impact(
    bulletin_text: str,
    stage1_tags: dict,
    stage2_relevance: dict,
    retrieved_chunks: list[IndexedChunk],
    product_profile: dict,
    *,
    client: genai.Client | None = None,
    on_event: Callable[[str], None] | None = None,
) -> tuple[ImpactAssessment, CostEntry]:
    """Run Stage 3. Returns the assessment + a CostEntry."""
    c = client or _client()
    profile_yaml = yaml.safe_dump(product_profile, sort_keys=False)
    captured: dict = {}

    user_content = (
        "# Bulletin\n"
        f"{bulletin_text}\n\n"
        "# Stage 1 tags\n"
        f"```json\n{stage1_tags}\n```\n\n"
        "# Stage 2 reasoning\n"
        f"{stage2_relevance.get('reasoning', '')}\n"
        f"affected_surfaces (from Stage 2): {stage2_relevance.get('affected_surfaces', [])}\n\n"
        "# Retrieved code chunks (top-k from the target codebase)\n"
        f"{_format_chunks(retrieved_chunks)}\n\n"
        "# Target product profile\n"
        f"```yaml\n{profile_yaml}```\n"
    )

    def call() -> ImpactAssessment:
        resp = c.models.generate_content(
            model=STAGE3_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=STAGE3_SYSTEM,
                response_mime_type="application/json",
                response_schema=ImpactAssessment,
                temperature=0.0,
            ),
        )
        if resp.parsed is None:
            raise RuntimeError(f"stage3: parsing failed. Raw text: {resp.text!r}")
        u = resp.usage_metadata
        captured["in"] = getattr(u, "prompt_token_count", 0) or 0
        captured["out"] = getattr(u, "candidates_token_count", 0) or 0
        return resp.parsed

    parsed = _with_retry(call, label="stage3", on_event=on_event)
    entry = CostEntry(
        stage="stage3",
        model=STAGE3_MODEL,
        input_tokens=captured.get("in", 0),
        output_tokens=captured.get("out", 0),
        cost_usd=estimate_cost_usd(STAGE3_MODEL, captured.get("in", 0), captured.get("out", 0)),
    )
    return parsed, entry
