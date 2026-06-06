"""Run the Phase 1 skateboard end-to-end for one tenant.

Loads tenant config, iterates curated bulletins under tenants/<slug>/bulletins/,
runs the two-stage Gemini classifier on each, prints results, and writes a
JSON summary to outputs/. Compares classifier output against the
`expected_relevance` frontmatter field as an informal sanity check.

Usage:  uv run python scripts/run_skateboard.py <tenant_slug>
Example: uv run python scripts/run_skateboard.py hyperswitch
"""
from __future__ import annotations

import argparse
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
from src.ingest import iter_bulletins  # noqa: E402
from src.tenant import load_tenant  # noqa: E402
from src.tenant.loader import PROJECT_ROOT, load_product_profile  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")
console = Console()


def _stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _emit(msg: str) -> None:
    console.print(f"[dim]{_stamp()}[/dim] {msg}")
    # Force flush so progress survives terminal buffering / nohup / tee.
    sys.stdout.flush()
    sys.stderr.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tenant_slug")
    args = parser.parse_args()

    tenant = load_tenant(args.tenant_slug)
    profile = load_product_profile(tenant)

    bulletins_dir = PROJECT_ROOT / "tenants" / args.tenant_slug / "bulletins"
    if not bulletins_dir.exists():
        console.print(f"[red]No bulletins directory at {bulletins_dir}[/red]")
        return 1

    console.print(f"[bold]Tenant:[/bold] {tenant.tenant.display_name}")
    console.print(f"[bold]Codebase:[/bold] {tenant.codebase.repo}")
    console.print(f"[bold]Bulletins:[/bold] {bulletins_dir.relative_to(PROJECT_ROOT)}")

    bulletin_list = list(iter_bulletins(bulletins_dir))
    total = len(bulletin_list)
    _emit(f"[bold]Found {total} bulletin(s) to classify[/bold]")
    console.print()

    overall_t0 = time.monotonic()
    results: list[dict] = []
    for i, (path, frontmatter, body) in enumerate(bulletin_list, start=1):
        bulletin_id = frontmatter.get("id", path.stem)
        _emit(
            f"[cyan]→ [{i}/{total}][/cyan] classifying [bold]{bulletin_id}[/bold] "
            f"({path.name})"
        )
        item_t0 = time.monotonic()
        try:
            result = classify_bulletin(
                bulletin_id,
                body,
                profile,
                on_event=lambda m: _emit(f"   [dim]{m}[/dim]"),
            )
        except Exception as e:  # noqa: BLE001
            _emit(f"   [red]✗ error: {type(e).__name__}: {e}[/red]")
            results.append({
                "bulletin_id": bulletin_id,
                "file": str(path.relative_to(PROJECT_ROOT)),
                "error": f"{type(e).__name__}: {e}",
            })
            continue

        _emit(
            f"   [green]✓ done in {time.monotonic() - item_t0:.1f}s[/green] "
            f"({total - i} remaining)"
        )
        results.append({
            "bulletin_id": bulletin_id,
            "file": str(path.relative_to(PROJECT_ROOT)),
            "expected_relevance": frontmatter.get("expected_relevance"),
            "expected_priority": frontmatter.get("expected_priority"),
            "tags": result.tags.model_dump(),
            "relevance": result.relevance.model_dump(),
        })

    _emit(f"[bold]All bulletins processed in {time.monotonic() - overall_t0:.1f}s[/bold]")

    # Render summary table
    table = Table(title="Skateboard results", show_lines=True)
    table.add_column("Bulletin")
    table.add_column("Network/Topic/Action", overflow="fold")
    table.add_column("Mandatory", justify="center")
    table.add_column("Predicted", justify="center")
    table.add_column("Expected", justify="center")
    table.add_column("Conf.", justify="right")
    table.add_column("Affected surfaces", overflow="fold", max_width=40)

    matches = 0
    labeled = 0
    for r in results:
        if "error" in r:
            table.add_row(r["bulletin_id"], "—", "—", "[red]ERR[/red]", "—", "—", r["error"][:40])
            continue
        tags = r["tags"]
        rel = r["relevance"]
        pred = "[green]YES[/green]" if rel["relevant"] else "[yellow]no[/yellow]"
        exp_str = r.get("expected_relevance") or "—"
        if r.get("expected_relevance") in ("relevant", "not_relevant"):
            labeled += 1
            if (r["expected_relevance"] == "relevant") == rel["relevant"]:
                matches += 1
                exp_str = f"[green]{exp_str}[/green]"
            else:
                exp_str = f"[red]{exp_str}[/red]"
        table.add_row(
            r["bulletin_id"],
            f"{tags['network']}/{tags['topic']}/{tags['action_type']}",
            "yes" if tags["mandatory"] else "no",
            pred,
            exp_str,
            f"{rel['confidence']:.2f}",
            ", ".join(rel["affected_surfaces"]) or "—",
        )

    console.print()
    console.print(table)

    # Print reasoning for each
    console.print("\n[bold]Reasoning[/bold]")
    for r in results:
        if "error" in r:
            continue
        console.print(f"\n[cyan]{r['bulletin_id']}[/cyan]: {r['relevance']['reasoning']}")

    if labeled:
        console.print(
            f"\n[bold]Agreement with frontmatter expected_relevance:[/bold] {matches}/{labeled}"
        )

    out_dir = PROJECT_ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"skateboard-{args.tenant_slug}-{ts}.json"
    out_path.write_text(json.dumps({
        "tenant": args.tenant_slug,
        "run_at_utc": ts,
        "agreement_with_expected": f"{matches}/{labeled}" if labeled else None,
        "results": results,
    }, indent=2))
    console.print(f"\n[dim]results: {out_path.relative_to(PROJECT_ROOT)}[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
