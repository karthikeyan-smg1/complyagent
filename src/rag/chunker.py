"""Walk a codebase and chunk source files for embedding.

Design choices:
- Per-file chunking when the file fits in a window; sliding windows when not.
  Per-file preserves the most context with minimal complexity and matches how
  payments engineers actually think about modules.
- Window size = 400 lines, stride = 320 (20% overlap). Voyage code-3 accepts
  32K tokens per chunk; a 400-line Rust file is ~3-5K tokens, well inside.
- Vendored, generated, and dependency directories are filtered out.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

LINES_PER_CHUNK = 400
STRIDE = 320  # 20% overlap

# Languages to index. Extend per-tenant if needed.
DEFAULT_EXTENSIONS = (".rs",)

# Directories to skip when walking a Rust workspace. These are either vendored,
# generated, or otherwise noise for relevance retrieval.
SKIP_DIRS = frozenset({
    "target", "vendor", "node_modules", ".git", "dist", "build",
    ".cargo", ".idea", ".vscode", ".github", "tests",
    "examples", "benches", "docs", "scripts", "migrations",
})

# File patterns to skip even when in an indexable directory.
SKIP_FILE_SUFFIXES = (".lock", ".toml.lock", ".min.js")


@dataclass(frozen=True)
class Chunk:
    """One chunk of source code with enough metadata to cite back to the file."""
    relative_path: str       # e.g., "crates/router/src/connector/visa.rs"
    module_path: str         # human-readable module, e.g., "router::connector::visa"
    start_line: int          # 1-indexed
    end_line: int            # 1-indexed inclusive
    text: str                # the actual chunk body

    @property
    def line_span(self) -> str:
        return f"{self.relative_path}:{self.start_line}-{self.end_line}"


def _is_skipped_dir(part: str) -> bool:
    return part in SKIP_DIRS or part.startswith(".")


def _module_path_from_relative(relative_path: str) -> str:
    """Derive a Rust-ish module path from a file path.

    `crates/router/src/connector/visa.rs` -> `router::connector::visa`
    `crates/router/src/main.rs`            -> `router`
    """
    p = Path(relative_path)
    parts = list(p.parts)
    # Drop the "crates/<crate>/src/" prefix common in Hyperswitch and similar
    # Rust workspaces. Keep the crate name as the first module segment.
    if len(parts) >= 3 and parts[0] == "crates" and parts[2] == "src":
        crate = parts[1]
        rest = parts[3:]
    elif "src" in parts:
        idx = parts.index("src")
        crate = parts[idx - 1] if idx > 0 else ""
        rest = parts[idx + 1:]
    else:
        crate = parts[0] if parts else ""
        rest = parts[1:]

    rest_no_ext = [Path(r).stem if i == len(rest) - 1 else r for i, r in enumerate(rest)]
    # Drop trailing "mod" or "lib" / "main" so they collapse into the parent.
    cleaned: list[str] = []
    for r in rest_no_ext:
        if r in ("mod", "lib", "main"):
            continue
        cleaned.append(r)
    segments = [s for s in ([crate] + cleaned) if s]
    return "::".join(segments)


def _chunk_lines(
    relative_path: str, lines: list[str],
) -> Iterator[Chunk]:
    """Slide a window of LINES_PER_CHUNK over the file. One emit per window.

    Files <= LINES_PER_CHUNK become a single chunk.
    """
    module_path = _module_path_from_relative(relative_path)
    n = len(lines)
    if n == 0:
        return
    if n <= LINES_PER_CHUNK:
        yield Chunk(
            relative_path=relative_path,
            module_path=module_path,
            start_line=1,
            end_line=n,
            text="".join(lines),
        )
        return

    start = 0
    while start < n:
        end = min(start + LINES_PER_CHUNK, n)
        yield Chunk(
            relative_path=relative_path,
            module_path=module_path,
            start_line=start + 1,
            end_line=end,
            text="".join(lines[start:end]),
        )
        if end == n:
            break
        start += STRIDE


def walk_and_chunk(
    root: Path,
    *,
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS,
    skip_dirs: frozenset[str] = SKIP_DIRS,
) -> Iterator[Chunk]:
    """Yield Chunk objects for every indexable file under root."""
    root = root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        # Skip if any path part is in the skip list.
        rel = path.relative_to(root)
        if any(_is_skipped_dir(p) for p in rel.parts[:-1]):
            continue
        if path.name.endswith(SKIP_FILE_SUFFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # Skip empty or near-empty files.
        if len(text) < 50:
            continue
        lines = text.splitlines(keepends=True)
        for chunk in _chunk_lines(str(rel), lines):
            yield chunk
