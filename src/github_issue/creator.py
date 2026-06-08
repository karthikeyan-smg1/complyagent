"""Create GitHub Issues on the tenant's target repo fork.

Behavior:
- Dedupe by a marker line in the body: `<!-- complyagent:bulletin_id=<id> -->`.
  Before creating, list existing issues (open + closed) and skip if one with
  that marker already exists. Logs the existing URL.
- Title convention: `[ComplyAgent] <bulletin_id>: <bulletin title (truncated)>`
- Labels: `compliance`, `complyagent-auto`, and the priority (`P0`..`P3`).
  Missing labels are created best-effort.

The Issues:Write GitHub token is read from GITHUB_TOKEN env. The tenant config
provides `issue_tracker.github.repo` (e.g., `karthikeyan-smg1/hyperswitch`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


GITHUB_API = "https://api.github.com"
TIMEOUT_SECONDS = 30


@dataclass
class GitHubIssueResult:
    bulletin_id: str
    repo: str
    issue_url: str
    issue_number: int
    created: bool  # True if a new issue was filed, False if an existing one was found


def _headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set in environment")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _marker(bulletin_id: str) -> str:
    return f"<!-- complyagent:bulletin_id={bulletin_id} -->"


def _ensure_label(repo: str, name: str, color: str, description: str) -> None:
    """Best-effort label creation — no-op if it already exists or perms missing."""
    try:
        r = requests.post(
            f"{GITHUB_API}/repos/{repo}/labels",
            headers=_headers(),
            json={"name": name, "color": color, "description": description},
            timeout=TIMEOUT_SECONDS,
        )
        # 201 created, 422 already exists, 403 perms — all fine to ignore.
        return
    except requests.RequestException:
        return


def _find_existing_issue(repo: str, bulletin_id: str) -> dict[str, Any] | None:
    """Look for an issue whose body contains the bulletin marker."""
    marker = _marker(bulletin_id)
    # Search closed + open via the search API (issues body included).
    q = f'repo:{repo} type:issue in:body "{marker}"'
    try:
        r = requests.get(
            f"{GITHUB_API}/search/issues",
            headers=_headers(),
            params={"q": q, "per_page": 1},
            timeout=TIMEOUT_SECONDS,
        )
        if r.status_code != 200:
            return None
        items = r.json().get("items", [])
        return items[0] if items else None
    except requests.RequestException:
        return None


PRIORITY_COLORS = {
    "P0": "B60205",  # red
    "P1": "D93F0B",  # orange-red
    "P2": "FBCA04",  # amber
    "P3": "0E8A16",  # green
}


def render_issue_body(
    *,
    bulletin_id: str,
    bulletin_title: str,
    bulletin_source: str,
    bulletin_date: str,
    stage1_tags: dict,
    stage2_relevance: dict,
    impact: dict,
    priority: dict,
    bulletin_file: str | None = None,
) -> str:
    """Compose the issue body in a payments-engineer-friendly format."""
    surfaces = ", ".join(stage2_relevance.get("affected_surfaces") or []) or "—"
    affected_files = impact.get("affected_files") or []
    files_block = (
        "\n".join(
            f"- **`{f['path']}`**"
            + (f" (lines `{f.get('line_range', '')}`)" if f.get("line_range") else "")
            + (f" — {f.get('rationale', '')}" if f.get("rationale") else "")
            for f in affected_files
        )
        or "_(none cited — retrieval did not surface obvious files; may need broader corpus or larger top-k.)_"
    )

    return f"""## Summary
{impact.get("impact_summary", "—")}

## Why this matters
**Bulletin:** {bulletin_title}
**Source:** {bulletin_source} · {bulletin_date}
**Network · topic · action:** `{stage1_tags.get("network", "—")}` · `{stage1_tags.get("topic", "—")}` · `{stage1_tags.get("action_type", "—")}`
**Effective date:** `{stage1_tags.get("effective_date", "—")}` · **Mandatory:** `{stage1_tags.get("mandatory", False)}`

**Relevance classifier reasoning (Stage 2):**
{stage2_relevance.get("reasoning", "—")}

**Surfaces affected (from product profile):** {surfaces}

## Affected files (retrieval-grounded)
{files_block}

## Suggested change
{impact.get("suggested_change", "—")}

**Estimated effort:** `{impact.get("estimated_effort", "—")}`

## Priority rationale (deterministic rubric)
**`{priority.get("priority", "—")}`** — {priority.get("rationale", "")}

---

_Filed by [ComplyAgent](https://github.com/karthikeyan-smg1/complyagent) — a repo-connected compliance agent for payments codebases. Source bulletin:_ `{bulletin_file or bulletin_id}`

{_marker(bulletin_id)}
"""


def create_or_update_issue(
    *,
    repo: str,
    bulletin_id: str,
    bulletin_title: str,
    title: str,
    body: str,
    priority: str,
) -> GitHubIssueResult:
    """Create the issue (or return the URL of the existing one if found)."""
    existing = _find_existing_issue(repo, bulletin_id)
    if existing:
        return GitHubIssueResult(
            bulletin_id=bulletin_id,
            repo=repo,
            issue_url=existing["html_url"],
            issue_number=existing["number"],
            created=False,
        )

    # Best-effort label creation
    _ensure_label(repo, "compliance", "5319E7", "Regulatory / compliance work")
    _ensure_label(repo, "complyagent-auto", "C2E0C6", "Filed by ComplyAgent")
    if priority in PRIORITY_COLORS:
        _ensure_label(repo, priority, PRIORITY_COLORS[priority], f"Priority {priority}")

    labels = ["compliance", "complyagent-auto"]
    if priority in PRIORITY_COLORS:
        labels.append(priority)

    r = requests.post(
        f"{GITHUB_API}/repos/{repo}/issues",
        headers=_headers(),
        json={"title": title, "body": body, "labels": labels},
        timeout=TIMEOUT_SECONDS,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(
            f"GitHub issue creation failed: HTTP {r.status_code} {r.text[:400]}"
        )
    payload = r.json()
    return GitHubIssueResult(
        bulletin_id=bulletin_id,
        repo=repo,
        issue_url=payload["html_url"],
        issue_number=payload["number"],
        created=True,
    )
