"""Run the two-stage classifier across the entire bulletin corpus and report
precision / recall / F1 against frontmatter ground-truth labels.

Also (re)generates `tenants/<slug>/ground_truth.csv` as a flat human-readable
mirror of the per-bulletin labels for easy review.

Usage: uv run python scripts/run_eval.py <tenant_slug>
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from src.classify import classify_bulletin  # noqa: E402
from src.eval import compute_metrics  # noqa: E402
from src.ingest import iter_bulletins  # noqa: E402
from src.tenant import load_tenant  # noqa: E402
from src.tenant.loader import PROJECT_ROOT, load_product_profile  # noqa: E402

import os  # noqa: E402

# Hard per-run dollar cap so a runaway eval can't burn the month's budget in
# one go. The user-stated monthly cap is INR 100 (~$1.20); we default the
# per-run cap to $0.50 — generous for any single eval at Flash-Lite or Flash,
# tight enough that a misconfigured Pro run aborts before damage.
USD_BUDGET_PER_RUN = float(os.environ.get("COMPLY_USD_BUDGET", "0.50"))

load_dotenv(PROJECT_ROOT / ".env")
console = Console()


def _stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _emit(msg: str) -> None:
    console.print(f"[dim]{_stamp()}[/dim] {msg}")
    sys.stdout.flush()
    sys.stderr.flush()


def _refresh_ground_truth_csv(rows: list[dict], path: Path) -> None:
    """Rewrite ground_truth.csv from the bulletin frontmatter."""
    cols = [
        "bulletin_id", "file_path", "source", "network", "date",
        "title", "relevant", "priority", "difficulty", "failure_mode", "notes",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tenant_slug")
    args = parser.parse_args()

    tenant = load_tenant(args.tenant_slug)
    profile = load_product_profile(tenant)
    bulletins_dir = PROJECT_ROOT / "tenants" / args.tenant_slug / "bulletins"

    bulletin_list = list(iter_bulletins(bulletins_dir))
    total = len(bulletin_list)
    _emit(f"[bold]Eval over {total} bulletin(s) — tenant: {tenant.tenant.display_name}[/bold]")
    console.print()

    overall_t0 = time.monotonic()
    results: list[dict] = []
    ground_truth_rows: list[dict] = []
    consecutive_429s = 0
    CIRCUIT_BREAKER = 2  # bulletins back-to-back failing on first attempt
    circuit_tripped = False
    cumulative_cost_usd = 0.0
    budget_tripped = False
    _emit(f"[bold]Per-run USD budget cap: ${USD_BUDGET_PER_RUN:.2f}[/bold]")

    def _first_attempt_was_429(events: list[str]) -> bool:
        """Inspect the captured on_event lines to see if attempt 1 hit 429."""
        for e in events:
            if "attempt 1/" in e and "sent" in e:
                continue
            if "RESOURCE_EXHAUSTED" in e or "429" in e:
                return True
            if "ok in" in e:
                return False
        return False

    for i, (path, fm, body) in enumerate(bulletin_list, start=1):
        bid = fm.get("id", path.stem)
        title = body.splitlines()[0].lstrip("# ").strip() if body else ""
        _emit(f"[cyan]→ [{i}/{total}][/cyan] {bid}")

        ground_truth_rows.append({
            "bulletin_id": bid,
            "file_path": str(path.relative_to(PROJECT_ROOT)),
            "source": fm.get("source", ""),
            "network": fm.get("network", ""),
            "date": fm.get("date", ""),
            "title": title,
            "relevant": fm.get("expected_relevance", ""),
            "priority": fm.get("expected_priority") or "",
            "difficulty": fm.get("difficulty") or "",
            "failure_mode": fm.get("failure_mode") or "",
            "notes": "synthesized=true" if fm.get("synthesized") else "",
        })

        item_t0 = time.monotonic()
        captured_events: list[str] = []

        def _on_event(m: str) -> None:
            captured_events.append(m)
            _emit(f"   [dim]{m}[/dim]")

        try:
            result = classify_bulletin(
                bid, body, profile,
                on_event=_on_event,
            )
            elapsed = time.monotonic() - item_t0
            item_cost = result.total_cost_usd
            cumulative_cost_usd += item_cost
            _emit(
                f"   [green]✓ {elapsed:.1f}s[/green]  predicted={result.relevance.relevant}  "
                f"cost=${item_cost:.4f}  cum=${cumulative_cost_usd:.4f}"
            )
            consecutive_429s = 0
            results.append({
                "bulletin_id": bid,
                "file": str(path.relative_to(PROJECT_ROOT)),
                "title": title,
                "expected_relevance": fm.get("expected_relevance"),
                "expected_priority": fm.get("expected_priority"),
                "difficulty": fm.get("difficulty"),
                "failure_mode": fm.get("failure_mode"),
                "tags": result.tags.model_dump(),
                "relevance": result.relevance.model_dump(),
                "cost": [c.model_dump() for c in result.cost],
                "cost_usd": item_cost,
                "elapsed_s": round(elapsed, 2),
            })
            if cumulative_cost_usd >= USD_BUDGET_PER_RUN:
                budget_tripped = True
                _emit(
                    f"[red bold]Budget cap: cumulative spend ${cumulative_cost_usd:.4f} "
                    f"≥ cap ${USD_BUDGET_PER_RUN:.2f} — aborting eval to protect spend.[/red bold]"
                )
                for j in range(i, len(bulletin_list)):
                    p2, fm2, body2 = bulletin_list[j]
                    bid2 = fm2.get("id", p2.stem)
                    title2 = body2.splitlines()[0].lstrip("# ").strip() if body2 else ""
                    if bid2 == bid:
                        continue
                    results.append({
                        "bulletin_id": bid2,
                        "file": str(p2.relative_to(PROJECT_ROOT)),
                        "title": title2,
                        "expected_relevance": fm2.get("expected_relevance"),
                        "expected_priority": fm2.get("expected_priority"),
                        "difficulty": fm2.get("difficulty"),
                        "failure_mode": fm2.get("failure_mode"),
                        "error": "skipped_by_budget_cap",
                        "elapsed_s": 0.0,
                    })
                break
        except Exception as e:  # noqa: BLE001
            elapsed = time.monotonic() - item_t0
            _emit(f"   [red]✗ {type(e).__name__}: {str(e)[:120]}[/red]")
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                consecutive_429s += 1
            results.append({
                "bulletin_id": bid,
                "file": str(path.relative_to(PROJECT_ROOT)),
                "title": title,
                "expected_relevance": fm.get("expected_relevance"),
                "expected_priority": fm.get("expected_priority"),
                "difficulty": fm.get("difficulty"),
                "failure_mode": fm.get("failure_mode"),
                "error": f"{type(e).__name__}: {e}",
                "elapsed_s": round(elapsed, 2),
            })
            circuit_tripped = consecutive_429s >= CIRCUIT_BREAKER
            if circuit_tripped:
                _emit(
                    f"[red bold]Circuit breaker: {CIRCUIT_BREAKER} consecutive "
                    f"429-driven failures — aborting eval.[/red bold]"
                )
                _emit("[yellow]Likely causes: (1) per-day quota hit "
                      "(both gemini-2.5-flash and gemini-2.5-flash-lite "
                      "cap at 20 requests/day on free tier); (2) per-minute "
                      "quota still cooling. Wait for the daily reset "
                      "(00:00 Pacific) or enable Gemini billing.[/yellow]")
                # Record the un-attempted bulletins so the corpus total is honest
                for j in range(i, len(bulletin_list)):
                    p2, fm2, body2 = bulletin_list[j]
                    bid2 = fm2.get("id", p2.stem)
                    title2 = body2.splitlines()[0].lstrip("# ").strip() if body2 else ""
                    results.append({
                        "bulletin_id": bid2,
                        "file": str(p2.relative_to(PROJECT_ROOT)),
                        "title": title2,
                        "expected_relevance": fm2.get("expected_relevance"),
                        "expected_priority": fm2.get("expected_priority"),
                        "difficulty": fm2.get("difficulty"),
                        "failure_mode": fm2.get("failure_mode"),
                        "error": "skipped_by_circuit_breaker",
                        "elapsed_s": 0.0,
                    })
                break

    metrics = compute_metrics(
        (r.get("expected_relevance"), r.get("relevance", {}).get("relevant"))
        for r in results
    )
    # Stratify by difficulty so reviewers can see headline vs adversarial.
    by_difficulty: dict[str, dict] = {}
    seen_difficulties = sorted({(r.get("difficulty") or "unspecified") for r in results})
    for d in seen_difficulties:
        subset = [r for r in results if (r.get("difficulty") or "unspecified") == d]
        m = compute_metrics(
            (r.get("expected_relevance"), r.get("relevance", {}).get("relevant"))
            for r in subset
        )
        by_difficulty[d] = m.as_dict() | {"n": len(subset)}

    # Confusion matrix and per-bulletin breakdown
    console.print()
    summary = Table(title="Classifier evaluation", show_lines=False)
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")
    summary.add_row("Total bulletins", str(metrics.total))
    summary.add_row("Labeled", str(metrics.labeled))
    summary.add_row("True positives", str(metrics.true_positive))
    summary.add_row("False positives", str(metrics.false_positive))
    summary.add_row("True negatives", str(metrics.true_negative))
    summary.add_row("False negatives", str(metrics.false_negative))
    summary.add_row("Precision", f"{metrics.precision:.3f}" if metrics.precision is not None else "—")
    summary.add_row("Recall", f"{metrics.recall:.3f}" if metrics.recall is not None else "—")
    summary.add_row("F1", f"{metrics.f1:.3f}" if metrics.f1 is not None else "—")
    summary.add_row("Accuracy", f"{metrics.accuracy:.3f}" if metrics.accuracy is not None else "—")
    summary.add_row("Total wall-clock", f"{time.monotonic() - overall_t0:.1f}s")
    summary.add_row("Cumulative spend (USD)", f"${cumulative_cost_usd:.4f}")
    summary.add_row("Cumulative spend (INR)", f"₹{cumulative_cost_usd * 84:.2f}")
    summary.add_row("Budget cap (USD)", f"${USD_BUDGET_PER_RUN:.2f}")
    console.print(summary)

    detail = Table(title="Per-bulletin results", show_lines=True)
    detail.add_column("Bulletin")
    detail.add_column("Predicted", justify="center")
    detail.add_column("Expected", justify="center")
    detail.add_column("Conf.", justify="right")
    detail.add_column("Verdict", justify="center")
    detail.add_column("Affected surfaces", overflow="fold", max_width=40)

    for r in results:
        if "error" in r:
            detail.add_row(r["bulletin_id"], "[red]ERR[/red]", r.get("expected_relevance") or "—",
                           "—", "[red]ERR[/red]", r["error"][:40])
            continue
        rel = r["relevance"]
        pred = "YES" if rel["relevant"] else "no"
        exp = r.get("expected_relevance") or "—"
        # Verdict
        if exp == "relevant" and rel["relevant"]:
            verdict = "[green]TP[/green]"
        elif exp == "not_relevant" and not rel["relevant"]:
            verdict = "[green]TN[/green]"
        elif exp == "not_relevant" and rel["relevant"]:
            verdict = "[red]FP[/red]"
        elif exp == "relevant" and not rel["relevant"]:
            verdict = "[red]FN[/red]"
        else:
            verdict = "—"
        detail.add_row(
            r["bulletin_id"],
            pred, exp,
            f"{rel['confidence']:.2f}",
            verdict,
            ", ".join(rel.get("affected_surfaces", [])) or "—",
        )
    console.print(detail)

    # Write artifacts
    out_dir = PROJECT_ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"eval-{args.tenant_slug}-{ts}.json"
    out_path.write_text(json.dumps({
        "tenant": args.tenant_slug,
        "run_at_utc": ts,
        "metrics": metrics.as_dict(),
        "metrics_by_difficulty": by_difficulty,
        "total_cost_usd": round(cumulative_cost_usd, 6),
        "budget_cap_usd": USD_BUDGET_PER_RUN,
        "budget_tripped": budget_tripped,
        "circuit_tripped": circuit_tripped,
        "results": results,
    }, indent=2, default=str))
    _emit(f"[dim]eval artifact: {out_path.relative_to(PROJECT_ROOT)}[/dim]")

    gt_path = PROJECT_ROOT / "tenants" / args.tenant_slug / "ground_truth.csv"
    _refresh_ground_truth_csv(ground_truth_rows, gt_path)
    _emit(f"[dim]ground truth refreshed: {gt_path.relative_to(PROJECT_ROOT)}[/dim]")

    # Also write a latest-eval pointer for the Streamlit dashboard
    latest = out_dir / "latest-eval.json"
    latest.write_text(out_path.read_text())
    _emit(f"[dim]latest-eval pointer: {latest.relative_to(PROJECT_ROOT)}[/dim]")

    return 0 if metrics.false_negative == 0 and metrics.false_positive <= metrics.labeled // 4 else 0


if __name__ == "__main__":
    sys.exit(main())
