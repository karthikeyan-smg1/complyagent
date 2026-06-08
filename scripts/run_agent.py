"""End-to-end agent pipeline — closes the loop from bulletin to GitHub Issue.

For every bulletin in a tenant's corpus:
  Stage 1 (tag) → Stage 2 (relevance)
  if relevant:
      RAG (embed query → top-k code chunks)
      Stage 3 (impact assessment, grounded in retrieved chunks)
      Priority rubric (deterministic)
      GitHub Issue (dedupe by bulletin_id marker)

Writes the agent's full output to outputs/agent-<tenant>-<ts>.json and
refreshes outputs/latest-eval.json so the Streamlit dashboard surfaces the
new fields.

Usage:
    uv run python scripts/run_agent.py <tenant_slug> [--no-issues] [--top-k 5]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402
from rich.console import Console  # noqa: E402

from src.classify import classify_bulletin  # noqa: E402
from src.eval import compute_metrics  # noqa: E402
from src.github_issue import create_or_update_issue, render_issue_body  # noqa: E402
from src.impact import assess_impact  # noqa: E402
from src.ingest import iter_bulletins  # noqa: E402
from src.priority import score_priority  # noqa: E402
from src.rag import VoyageEmbedder, load_index  # noqa: E402
from src.tenant import load_tenant  # noqa: E402
from src.tenant.loader import PROJECT_ROOT, load_product_profile  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")
console = Console()

INDEX_DIR = Path.home() / ".complyagent"
USD_BUDGET_PER_RUN = float(os.environ.get("COMPLY_AGENT_USD_BUDGET", "1.00"))


def _stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _emit(msg: str) -> None:
    console.print(f"[dim]{_stamp()}[/dim] {msg}")
    sys.stdout.flush()
    sys.stderr.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tenant_slug")
    parser.add_argument("--top-k", type=int, default=6, help="chunks to retrieve per bulletin")
    parser.add_argument("--no-issues", action="store_true",
                        help="Skip GitHub Issue creation (dry-run the loop)")
    parser.add_argument("--only-bulletin",
                        help="Run for a single bulletin_id (useful for testing)")
    args = parser.parse_args()

    tenant = load_tenant(args.tenant_slug)
    profile = load_product_profile(tenant)
    bulletins_dir = PROJECT_ROOT / "tenants" / args.tenant_slug / "bulletins"
    bulletins = list(iter_bulletins(bulletins_dir))
    if args.only_bulletin:
        bulletins = [(p, fm, body) for p, fm, body in bulletins
                     if fm.get("id") == args.only_bulletin]
        if not bulletins:
            console.print(f"[red]no bulletin found with id {args.only_bulletin}[/red]")
            return 1

    # Load the local code index
    index_path = INDEX_DIR / f"index-{args.tenant_slug}.parquet"
    if not index_path.exists():
        console.print(
            f"[red]No code index at {index_path}. "
            f"Run scripts/index_codebase.py {args.tenant_slug} <codebase_path> first.[/red]"
        )
        return 1
    _emit(f"Loading code index from {index_path}")
    index = load_index(index_path)
    _emit(f"Index: n_chunks={index.n_chunks}  dim={index.dim}")

    embedder = VoyageEmbedder()

    _emit(f"[bold]Agent run — {len(bulletins)} bulletin(s) — tenant {args.tenant_slug}[/bold]")
    _emit(f"USD budget cap: ${USD_BUDGET_PER_RUN:.2f}  ·  issues_enabled={not args.no_issues}")

    overall_t0 = time.monotonic()
    results: list[dict] = []
    cumulative_cost = 0.0
    n_relevant = 0
    n_issues_created = 0
    n_issues_existing = 0

    github_repo = (
        tenant.issue_tracker.github.repo if tenant.issue_tracker.github else None
    )
    if not args.no_issues and not github_repo:
        _emit("[yellow]No github repo configured in tenant config — issue creation skipped.[/yellow]")

    for i, (path, fm, body) in enumerate(bulletins, start=1):
        bid = fm.get("id", path.stem)
        title = body.splitlines()[0].lstrip("# ").strip() if body else ""
        _emit(f"[cyan]→ [{i}/{len(bulletins)}][/cyan] {bid}  ({title[:60]})")
        item_t0 = time.monotonic()
        item_cost = 0.0
        item_result: dict = {
            "bulletin_id": bid,
            "file": str(path.relative_to(PROJECT_ROOT)),
            "title": title,
            "expected_relevance": fm.get("expected_relevance"),
            "expected_priority": fm.get("expected_priority"),
            "difficulty": fm.get("difficulty"),
            "failure_mode": fm.get("failure_mode"),
        }

        try:
            classified = classify_bulletin(
                bid, body, profile,
                on_event=lambda m: _emit(f"   [dim]{m}[/dim]"),
            )
            classify_cost = classified.total_cost_usd
            cumulative_cost += classify_cost
            item_cost += classify_cost
            item_result["tags"] = classified.tags.model_dump()
            item_result["relevance"] = classified.relevance.model_dump()
            item_result["cost"] = [c.model_dump() for c in classified.cost]

            if classified.relevance.relevant:
                n_relevant += 1
                # Build a retrieval query: relevance reasoning + affected surfaces +
                # network/topic — concrete enough to surface code that actually deals
                # with these payment surfaces.
                query = (
                    f"{classified.tags.network} {classified.tags.topic} "
                    f"{classified.tags.action_type} — "
                    f"{classified.relevance.reasoning}  "
                    f"surfaces: {', '.join(classified.relevance.affected_surfaces)}"
                )
                _emit(f"   [dim]retrieval: embedding query[/dim]")
                emb_result = embedder.embed_query(query)
                cumulative_cost += emb_result.cost_usd
                item_cost += emb_result.cost_usd

                retrieved = index.retrieve(
                    emb_result.embeddings[0], top_k=args.top_k
                )
                _emit(
                    f"   [dim]retrieved {len(retrieved)} chunks "
                    f"({', '.join(c.line_span for c in retrieved[:3])}...)[/dim]"
                )
                item_result["retrieved_chunks"] = [
                    {
                        "path": c.relative_path,
                        "module_path": c.module_path,
                        "start_line": c.start_line,
                        "end_line": c.end_line,
                        "line_span": c.line_span,
                        "score": c.score,
                    }
                    for c in retrieved
                ]

                # Stage 3 — impact assessment
                impact, impact_cost = assess_impact(
                    body,
                    classified.tags.model_dump(),
                    classified.relevance.model_dump(),
                    retrieved,
                    profile,
                    on_event=lambda m: _emit(f"   [dim]{m}[/dim]"),
                )
                cumulative_cost += impact_cost.cost_usd
                item_cost += impact_cost.cost_usd
                item_result["impact"] = impact.model_dump()

                # Priority rubric
                priority = score_priority(
                    mandatory=classified.tags.mandatory,
                    effective_date_str=classified.tags.effective_date,
                    confidence=classified.relevance.confidence,
                    affected_file_count=len(impact.affected_files),
                    estimated_effort=impact.estimated_effort,
                )
                item_result["priority"] = {
                    "priority": priority.priority,
                    "rationale": priority.rationale,
                    "factors": priority.factors,
                }

                # GitHub Issue (optional)
                if not args.no_issues and github_repo:
                    issue_title = f"[ComplyAgent] {bid}: {title[:120]}"
                    body_md = render_issue_body(
                        bulletin_id=bid,
                        bulletin_title=title,
                        bulletin_source=fm.get("source", "—"),
                        bulletin_date=str(fm.get("date", "—")),
                        stage1_tags=classified.tags.model_dump(),
                        stage2_relevance=classified.relevance.model_dump(),
                        impact=impact.model_dump(),
                        priority={
                            "priority": priority.priority,
                            "rationale": priority.rationale,
                        },
                        bulletin_file=item_result["file"],
                    )
                    try:
                        issue = create_or_update_issue(
                            repo=github_repo,
                            bulletin_id=bid,
                            bulletin_title=title,
                            title=issue_title,
                            body=body_md,
                            priority=priority.priority,
                        )
                        item_result["issue"] = {
                            "url": issue.issue_url,
                            "number": issue.issue_number,
                            "created": issue.created,
                            "repo": issue.repo,
                        }
                        if issue.created:
                            n_issues_created += 1
                            _emit(f"   [green]✓ filed issue #{issue.issue_number}: {issue.issue_url}[/green]")
                        else:
                            n_issues_existing += 1
                            _emit(f"   [yellow]= existing issue #{issue.issue_number}: {issue.issue_url}[/yellow]")
                    except Exception as e:  # noqa: BLE001
                        _emit(f"   [red]issue create failed: {type(e).__name__}: {str(e)[:200]}[/red]")
                        item_result["issue_error"] = f"{type(e).__name__}: {e}"

            elapsed = time.monotonic() - item_t0
            _emit(
                f"   [green]✓ done {elapsed:.1f}s[/green]  cost=${item_cost:.4f}  "
                f"cum=${cumulative_cost:.4f} (~₹{cumulative_cost*84:.2f})"
            )
            item_result["elapsed_s"] = round(elapsed, 2)
            item_result["cost_usd"] = round(item_cost, 6)
            results.append(item_result)

            if cumulative_cost >= USD_BUDGET_PER_RUN:
                _emit(
                    f"[red bold]Budget cap reached (${USD_BUDGET_PER_RUN:.2f}) — "
                    f"aborting agent run.[/red bold]"
                )
                # Mark un-processed bulletins as skipped
                for j in range(i, len(bulletins)):
                    p2, fm2, body2 = bulletins[j]
                    if (p2, fm2, body2) == (path, fm, body):
                        continue
                    results.append({
                        "bulletin_id": fm2.get("id", p2.stem),
                        "file": str(p2.relative_to(PROJECT_ROOT)),
                        "title": body2.splitlines()[0].lstrip("# ").strip() if body2 else "",
                        "expected_relevance": fm2.get("expected_relevance"),
                        "difficulty": fm2.get("difficulty"),
                        "failure_mode": fm2.get("failure_mode"),
                        "error": "skipped_by_budget_cap",
                    })
                break

        except Exception as e:  # noqa: BLE001
            elapsed = time.monotonic() - item_t0
            _emit(f"   [red]✗ {type(e).__name__}: {str(e)[:200]}[/red]")
            item_result["error"] = f"{type(e).__name__}: {e}"
            item_result["elapsed_s"] = round(elapsed, 2)
            results.append(item_result)

    # Metrics + stratification (same as before)
    metrics = compute_metrics(
        (r.get("expected_relevance"), r.get("relevance", {}).get("relevant"))
        for r in results
    )
    by_difficulty: dict[str, dict] = {}
    for d in sorted({(r.get("difficulty") or "unspecified") for r in results}):
        subset = [r for r in results if (r.get("difficulty") or "unspecified") == d]
        sm = compute_metrics(
            (r.get("expected_relevance"), r.get("relevance", {}).get("relevant"))
            for r in subset
        )
        by_difficulty[d] = sm.as_dict() | {"n": len(subset)}

    # Write artifacts
    out_dir = PROJECT_ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = {
        "tenant": args.tenant_slug,
        "run_at_utc": ts,
        "metrics": metrics.as_dict(),
        "metrics_by_difficulty": by_difficulty,
        "total_cost_usd": round(cumulative_cost, 6),
        "budget_cap_usd": USD_BUDGET_PER_RUN,
        "n_relevant": n_relevant,
        "n_issues_created": n_issues_created,
        "n_issues_existing": n_issues_existing,
        "wall_clock_s": round(time.monotonic() - overall_t0, 1),
        "results": results,
    }
    out_path = out_dir / f"agent-{args.tenant_slug}-{ts}.json"
    out_path.write_text(json.dumps(artifact, indent=2, default=str))
    (out_dir / "latest-eval.json").write_text(json.dumps(artifact, indent=2, default=str))
    _emit(f"[dim]agent artifact: {out_path.relative_to(PROJECT_ROOT)}[/dim]")
    _emit(f"[bold]Wall-clock: {artifact['wall_clock_s']}s  ·  total cost: "
          f"${cumulative_cost:.4f} (~₹{cumulative_cost*84:.2f})[/bold]")
    _emit(f"[bold]Relevant bulletins: {n_relevant}  ·  issues filed: "
          f"{n_issues_created} (existing: {n_issues_existing})[/bold]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
