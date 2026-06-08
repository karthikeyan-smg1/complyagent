"""Deterministic priority rubric.

LLMs are not used here on purpose. The priority decision is the kind of
output a hiring manager will scrutinize ("why is this P0 and not P1?") —
deterministic, code-grounded, and auditable beats a model's judgement.

Inputs are the structured Stage-1/2/3 outputs the agent has already produced.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

Priority = Literal["P0", "P1", "P2", "P3"]


@dataclass
class PriorityScore:
    priority: Priority
    rationale: str
    factors: dict[str, str | int | bool | None]


def _parse_effective_date(s: str | None) -> date | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _days_until(d: date | None, today: date) -> int | None:
    if d is None:
        return None
    return (d - today).days


def score_priority(
    *,
    mandatory: bool,
    effective_date_str: str | None,
    confidence: float,
    affected_file_count: int,
    estimated_effort: Literal["small", "medium", "large"],
    today: date | None = None,
) -> PriorityScore:
    """Score a bulletin's priority deterministically.

    Rules — in this order:

      1. Not mandatory  → P3.
      2. Mandatory AND effective ≤ 60 days  → P0.
      3. Mandatory AND effective ≤ 180 days  → P1.
      4. Mandatory AND effective > 180 days OR unknown → P2.

    Effort and affected-file count nudge the rating up one level when high.
    Confidence < 0.6 nudges down one level (don't escalate uncertain calls).
    """
    today = today or date.today()
    effective_date = _parse_effective_date(effective_date_str)
    days = _days_until(effective_date, today)

    if not mandatory:
        return PriorityScore(
            priority="P3",
            rationale=(
                "Bulletin is not mandatory (`mandatory=false` from Stage 1 tagging) — "
                "no compliance penalty for non-action. Filed as P3 for visibility only."
            ),
            factors={
                "mandatory": False,
                "effective_date": effective_date_str,
                "confidence": confidence,
                "affected_file_count": affected_file_count,
                "estimated_effort": estimated_effort,
            },
        )

    # mandatory branch
    if days is not None and days <= 60:
        base: Priority = "P0"
    elif days is not None and days <= 180:
        base = "P1"
    else:
        base = "P2"

    # Escalate one level when the change spans many files OR is large effort
    escalate = (affected_file_count >= 5) or (estimated_effort == "large")
    # De-escalate one level when Stage-2 confidence is low — we don't want to
    # ship a P0 ticket if the model is hedging.
    de_escalate = confidence is not None and confidence < 0.6

    order: list[Priority] = ["P0", "P1", "P2", "P3"]
    idx = order.index(base)
    if escalate:
        idx = max(0, idx - 1)
    if de_escalate:
        idx = min(len(order) - 1, idx + 1)
    final = order[idx]

    parts = [
        f"Mandatory bulletin with effective date `{effective_date_str or 'unknown'}`"
        + (f" ({days} days out)." if days is not None else " (no parseable date)."),
        f"Base = {base}.",
    ]
    if escalate:
        parts.append(
            "Escalated one level because affected_file_count ≥ 5 or "
            "estimated_effort = large."
        )
    if de_escalate:
        parts.append(
            f"De-escalated one level because Stage-2 confidence ({confidence:.2f}) < 0.6."
        )
    parts.append(f"Final: {final}.")

    return PriorityScore(
        priority=final,
        rationale=" ".join(parts),
        factors={
            "mandatory": True,
            "effective_date": effective_date_str,
            "days_until_effective": days,
            "confidence": confidence,
            "affected_file_count": affected_file_count,
            "estimated_effort": estimated_effort,
            "base_before_modifiers": base,
        },
    )
