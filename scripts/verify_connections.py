"""Verify all four service credentials by making a minimal call against each.

Never prints API key values. Exits 0 if all four pass, 1 otherwise.
Run from project root: `uv run python scripts/verify_connections.py`
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

# Make src/ importable when running this script directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _require(*names: str) -> dict[str, str]:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError(f"missing env vars: {', '.join(missing)}")
    return {n: os.environ[n] for n in names}


def check_gemini() -> tuple[bool, str]:
    env = _require("GEMINI_API_KEY")
    from google import genai

    client = genai.Client(api_key=env["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Respond with the single word: ok",
    )
    text = (resp.text or "").strip().lower()
    return True, f"flash responded ({len(text)} chars)"


def check_voyage() -> tuple[bool, str]:
    env = _require("VOYAGE_API_KEY")
    import voyageai

    client = voyageai.Client(api_key=env["VOYAGE_API_KEY"])
    result = client.embed(["ping"], model="voyage-3-large")
    dim = len(result.embeddings[0])
    return True, f"embed ok (dim={dim})"


def check_supabase() -> tuple[bool, str]:
    env = _require("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    from supabase import create_client

    client = create_client(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])
    # Probe with a table that shouldn't exist yet. A "does not exist" reply
    # confirms auth + PostgREST round-trip; an auth error would say otherwise.
    try:
        client.table("_complyagent_probe").select("*").limit(1).execute()
        return True, "round-trip ok (probe table existed?)"
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "does not exist" in msg or "PGRST" in msg or "42P01" in msg:
            return True, "auth ok (no tables yet, expected)"
        raise


def check_langfuse() -> tuple[bool, str]:
    env = _require("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
    from langfuse import Langfuse

    lf = Langfuse(
        public_key=env["LANGFUSE_PUBLIC_KEY"],
        secret_key=env["LANGFUSE_SECRET_KEY"],
        host=env["LANGFUSE_BASE_URL"],
    )
    ok = lf.auth_check()
    return bool(ok), "auth_check ok" if ok else "auth_check returned False"


CHECKS: dict[str, Callable[[], tuple[bool, str]]] = {
    "Gemini 2.5 Flash": check_gemini,
    "Voyage AI":        check_voyage,
    "Supabase":         check_supabase,
    "Langfuse Cloud":   check_langfuse,
}


def main() -> int:
    table = Table(title="Connection verification", show_lines=False)
    table.add_column("Service")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    failures = 0
    for name, fn in CHECKS.items():
        try:
            ok, msg = fn()
            table.add_row(name, "[green]PASS[/green]" if ok else "[red]FAIL[/red]", msg)
            if not ok:
                failures += 1
        except Exception as e:  # noqa: BLE001
            failures += 1
            table.add_row(name, "[red]FAIL[/red]", f"{type(e).__name__}: {e}")

    console.print(table)
    if failures:
        console.print(f"[red]{failures}/{len(CHECKS)} failed[/red]")
        return 1
    console.print(f"[green]{len(CHECKS)}/{len(CHECKS)} passed[/green]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
