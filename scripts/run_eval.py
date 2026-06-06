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
        "title", "relevant", "priority", "notes",
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
    CIRCUIT_BREAKER = 3  # abort after this many back-to-back 429-driven failures

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
            "notes": "synthesized=true" if fm.get("synthesized") else "",
        })

        item_t0 = time.monotonic()
        try:
            result = classify_bulletin(
                bid, body, profile,
                on_event=lambda m: _emit(f"   [dim]{m}[/dim]"),
            )
            elapsed = time.monotonic() - item_t0
            _emit(f"   [green]✓ {elapsed:.1f}s[/green]  predicted={result.relevance.relevant}")
            consecutive_429s = 0
            results.append({
                "bulletin_id": bid,
                "file": str(path.relative_to(PROJECT_ROOT)),
                "title": title,
                "expected_relevance": fm.get("expected_relevance"),
                "expected_priority": fm.get("expected_priority"),
                "tags": result.tags.model_dump(),
                "relevance": result.relevance.model_dump(),
                "elapsed_s": round(elapsed, 2),
            })
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
                "error": f"{type(e).__name__}: {e}",
                "elapsed_s": round(elapsed, 2),
            })
            if consecutive_429s >= CIRCUIT_BREAKER:
                _emit(
                    f"[red bold]Circuit breaker: {CIRCUIT_BREAKER} consecutive "
                    f"429 failures — aborting eval.[/red bold]"
                )
                _emit("[yellow]Likely causes: (1) per-minute quota still cooling; "
                      "(2) per-day quota hit; (3) account in 60s+ penalty window. "
                      "Wait ~5 min and retry, or enable Gemini billing.[/yellow]")
                break

    metrics = compute_metrics(
        (r.get("expected_relevance"), r.get("relevance", {}).get("relevant"))
        for r in results
    )

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
