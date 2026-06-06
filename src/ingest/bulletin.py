"""Load bulletin markdown files with YAML frontmatter.

Frontmatter convention: `---\n<yaml>\n---\n<body>`. Frontmatter carries id,
source, date, network, mandatory, synthesized, expected_relevance (for
informal sanity), expected_priority. Body is the bulletin text fed to the
classifier.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import yaml


def load_bulletin(path: Path) -> tuple[dict, str]:
    """Parse a bulletin .md file. Returns (frontmatter_dict, body_text)."""
    text = path.read_text()
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            fm = yaml.safe_load(text[4:end]) or {}
            body = text[end + 5:].strip()
            return fm, body
    return {}, text


def iter_bulletins(directory: Path) -> Iterator[tuple[Path, dict, str]]:
    """Yield (path, frontmatter, body) for every .md bulletin in directory, sorted by filename."""
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        fm, body = load_bulletin(path)
        yield path, fm, body
