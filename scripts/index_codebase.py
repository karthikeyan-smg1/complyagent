"""Index a codebase for retrieval — walk it, chunk it, embed it, save it.

Usage:
    uv run python scripts/index_codebase.py <tenant_slug> <codebase_path>

Example:
    uv run python scripts/index_codebase.py hyperswitch ~/code/hyperswitch

Outputs the parquet index at ~/.complyagent/index-<tenant>.parquet
(gitignored; only the demo machine needs the embeddings).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402
from rich.console import Console  # noqa: E402

from src.rag import VoyageEmbedder, walk_and_chunk  # noqa: E402
from src.rag.index import CodeIndex  # noqa: E402
from src.tenant.loader import PROJECT_ROOT  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")
console = Console()


INDEX_DIR = Path.home() / ".complyagent"
USD_BUDGET_CAP = float(os.environ.get("COMPLY_INDEX_USD_BUDGET", "1.00"))
EMBED_BATCH = 64


def _emit(msg: str) -> None:
    console.print(f"[dim]{time.strftime('%H:%M:%S')}[/dim] {msg}")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tenant_slug")
    parser.add_argument("codebase_path", type=Path)
    parser.add_argument("--dry-run", action="store_true",
                        help="Walk + chunk but do not call Voyage (token estimate only)")
    args = parser.parse_args()

    if not args.codebase_path.exists():
        console.print(f"[red]codebase path does not exist: {args.codebase_path}[/red]")
        return 1

    _emit(f"[bold]Indexing {args.tenant_slug} from {args.codebase_path}[/bold]")
    _emit(f"USD budget cap: ${USD_BUDGET_CAP:.2f}")

    # 1. Chunk
    chunks = list(walk_and_chunk(args.codebase_path))
    total_chars = sum(len(c.text) for c in chunks)
    est_tokens = int(total_chars / 3.5)
    est_cost = est_tokens * 0.06 / 1_000_000
    _emit(
        f"Chunked: {len(chunks)} chunks from "
        f"{len({c.relative_path for c in chunks})} files. "
        f"~{est_tokens:,} tokens. ~estimated cost: ${est_cost:.4f} "
        f"(~₹{est_cost * 84:.2f})"
    )
    if est_cost > USD_BUDGET_CAP:
        _emit(
            f"[red bold]estimated cost ${est_cost:.4f} > cap ${USD_BUDGET_CAP:.2f} — "
            f"aborting before any Voyage call.[/red bold]"
        )
        _emit("[yellow]Raise the cap with COMPLY_INDEX_USD_BUDGET=$X if intentional.[/yellow]")
        return 2
    if args.dry_run:
        _emit("[yellow]--dry-run: no embeddings will be created.[/yellow]")
        return 0

    # 2. Embed in batches with running cost
    embedder = VoyageEmbedder()
    all_vectors: list[list[float]] = []
    total_tokens = 0
    total_cost = 0.0
    n_batches = (len(chunks) + EMBED_BATCH - 1) // EMBED_BATCH

    for batch_idx, start in enumerate(range(0, len(chunks), EMBED_BATCH), start=1):
        batch = chunks[start: start + EMBED_BATCH]
        texts = [c.text for c in batch]
        t0 = time.monotonic()
        result = embedder.embed_documents(texts, on_event=lambda m: None)
        all_vectors.extend(result.embeddings)
        total_tokens += result.input_tokens
        total_cost += result.cost_usd
        _emit(
            f"  batch {batch_idx}/{n_batches} ({len(batch)} chunks) "
            f"in {time.monotonic()-t0:.1f}s   "
            f"tokens={result.input_tokens:,}  "
            f"cost=${result.cost_usd:.4f}  "
            f"cum=${total_cost:.4f} (~₹{total_cost*84:.2f})"
        )
        if total_cost >= USD_BUDGET_CAP:
            _emit(
                f"[red bold]Budget cap reached — aborting at chunk "
                f"{start + len(batch)}/{len(chunks)}. Partial index NOT saved.[/red bold]"
            )
            return 3

    # 3. Build + save index
    index = CodeIndex.from_chunks_and_vectors(chunks, all_vectors)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INDEX_DIR / f"index-{args.tenant_slug}.parquet"
    index.save(out_path)
    size_mb = out_path.stat().st_size / 1024 / 1024
    _emit(f"[green]Index saved: {out_path} ({size_mb:.1f} MB)[/green]")
    _emit(
        f"[bold]Index stats:[/bold] "
        f"n_chunks={index.n_chunks}  dim={index.dim}  "
        f"tokens={total_tokens:,}  cost=${total_cost:.4f} (~₹{total_cost*84:.2f})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
