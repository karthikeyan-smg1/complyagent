"""15s-bounded smoke test for the Gemini SDK. Fails fast on network stalls.

Run before run_skateboard.py to verify the SDK + key + network path is healthy.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def main() -> int:
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY missing from .env", file=sys.stderr)
        return 1

    print(f"[{time.strftime('%H:%M:%S')}] building client with 15s timeout...", flush=True)
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(timeout=15_000),
    )
    print(f"[{time.strftime('%H:%M:%S')}] sending Flash request...", flush=True)
    t0 = time.monotonic()
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply with exactly the single word: ok",
            config=types.GenerateContentConfig(temperature=0.0),
        )
    except Exception as e:  # noqa: BLE001
        elapsed = time.monotonic() - t0
        print(
            f"[{time.strftime('%H:%M:%S')}] FAILED after {elapsed:.1f}s: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )
        return 2

    elapsed = time.monotonic() - t0
    print(
        f"[{time.strftime('%H:%M:%S')}] OK in {elapsed:.1f}s. "
        f"response: {(resp.text or '').strip()!r}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
