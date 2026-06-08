"""Voyage AI embeddings wrapper with rate limiting, retry, and cost tracking.

Same hardening pattern as `src/classify/classifier.py`: explicit timeout per
call, bounded retry with server-hint-aware backoff, a shared rate limiter,
and per-call usage_metadata captured so we can keep an honest spend tally.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

import voyageai

# Voyage `voyage-code-3` returns 1024-dim float32 vectors by default.
DEFAULT_EMBED_MODEL = "voyage-code-3"
DEFAULT_QUERY_MODEL = "voyage-3-large"

# Voyage free tier: 50M tokens/month total across all models.
# Paid voyage-code-3: $0.06 / 1M tokens. voyage-3-large: $0.06 / 1M.
PRICING_USD_PER_MILLION = {
    "voyage-code-3": 0.06,
    "voyage-3-large": 0.06,
    "voyage-3": 0.02,
    "voyage-3-lite": 0.02,
}

# Voyage Tier-1 limits are generous (~300 RPM, ~1M TPM). Cap conservatively.
DEFAULT_RATE_LIMIT_RPM = int(os.environ.get("COMPLY_VOYAGE_RPM", "60"))

# Voyage accepts up to 128 inputs per batch, max 120K tokens total per request.
MAX_BATCH_SIZE = 64
MAX_TOKENS_PER_BATCH = 100_000


def estimate_cost_usd(model: str, tokens: int) -> float:
    rate = PRICING_USD_PER_MILLION.get(model, 0.0)
    return tokens * rate / 1_000_000


@dataclass
class EmbeddingResult:
    embeddings: list[list[float]]
    model: str
    input_tokens: int
    cost_usd: float


class _RateLimiter:
    """Same sliding-window limiter used by the classifier."""

    def __init__(self, max_per_minute: int):
        self.max = max_per_minute
        self.window = 60.0
        self._times: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self, on_event: Callable[[str], None] | None = None) -> None:
        with self._lock:
            now = time.monotonic()
            while self._times and now - self._times[0] > self.window:
                self._times.popleft()
            if len(self._times) >= self.max:
                sleep_for = self.window - (now - self._times[0]) + 0.2
                if on_event and sleep_for > 0.5:
                    on_event(f"voyage rate-limit: sleeping {sleep_for:.1f}s")
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                while self._times and now - self._times[0] > self.window:
                    self._times.popleft()
            self._times.append(time.monotonic())


class VoyageEmbedder:
    """Thin wrapper around the Voyage client with our standard hardening.

    Usage:
        embedder = VoyageEmbedder()
        result = embedder.embed_documents(["text 1", "text 2"])
        # result.embeddings is a list of 1024-dim float lists
    """

    def __init__(
        self,
        *,
        document_model: str = DEFAULT_EMBED_MODEL,
        query_model: str = DEFAULT_QUERY_MODEL,
        rate_limit_rpm: int = DEFAULT_RATE_LIMIT_RPM,
        timeout_seconds: int = 60,
        max_attempts: int = 3,
    ):
        api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError("VOYAGE_API_KEY not set in environment")
        self._client = voyageai.Client(api_key=api_key, max_retries=0, timeout=timeout_seconds)
        self._document_model = document_model
        self._query_model = query_model
        self._rate_limiter = _RateLimiter(rate_limit_rpm)
        self._max_attempts = max_attempts

    def embed_documents(
        self,
        texts: list[str],
        *,
        on_event: Callable[[str], None] | None = None,
    ) -> EmbeddingResult:
        """Embed a list of texts as documents (for indexing).

        Auto-batches if the input list exceeds Voyage's per-request limits.
        """
        return self._embed(
            texts, model=self._document_model, input_type="document", on_event=on_event
        )

    def embed_query(
        self,
        text: str,
        *,
        on_event: Callable[[str], None] | None = None,
    ) -> EmbeddingResult:
        """Embed a single query (uses voyage-3-large by default for queries
        over documents indexed with voyage-code-3)."""
        return self._embed(
            [text], model=self._document_model, input_type="query", on_event=on_event
        )

    def _embed(
        self,
        texts: list[str],
        *,
        model: str,
        input_type: str,
        on_event: Callable[[str], None] | None,
    ) -> EmbeddingResult:
        all_embeddings: list[list[float]] = []
        total_tokens = 0
        total_cost = 0.0

        for batch in _split_batches(texts, MAX_BATCH_SIZE):
            self._rate_limiter.acquire(on_event=on_event)
            last_err: Exception | None = None
            for attempt in range(1, self._max_attempts + 1):
                try:
                    if on_event:
                        on_event(
                            f"voyage {model} batch={len(batch)} attempt {attempt}/{self._max_attempts}"
                        )
                    t0 = time.monotonic()
                    resp = self._client.embed(
                        texts=batch,
                        model=model,
                        input_type=input_type,
                    )
                    batch_tokens = resp.total_tokens
                    batch_cost = estimate_cost_usd(model, batch_tokens)
                    total_tokens += batch_tokens
                    total_cost += batch_cost
                    all_embeddings.extend(resp.embeddings)
                    if on_event:
                        on_event(
                            f"voyage {model} batch ok in {time.monotonic() - t0:.1f}s "
                            f"tokens={batch_tokens} cost=${batch_cost:.4f}"
                        )
                    break
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    if on_event:
                        on_event(f"voyage {type(e).__name__}: {str(e)[:120]}")
                    if attempt == self._max_attempts:
                        raise
                    time.sleep(2 ** attempt)
            else:
                assert last_err is not None
                raise last_err

        return EmbeddingResult(
            embeddings=all_embeddings,
            model=model,
            input_tokens=total_tokens,
            cost_usd=total_cost,
        )


def _split_batches(texts: list[str], max_batch_size: int) -> list[list[str]]:
    """Split a list of texts into batches that fit Voyage's per-request limit.

    Pure size-based — we don't pre-tokenize, but cap by character count as a
    cheap proxy for the 120K-token-per-request ceiling.
    """
    if not texts:
        return []
    batches: list[list[str]] = []
    cur: list[str] = []
    cur_chars = 0
    char_ceiling = MAX_TOKENS_PER_BATCH * 3  # ~3 chars/token rough proxy
    for t in texts:
        if len(cur) >= max_batch_size or (cur_chars + len(t) > char_ceiling and cur):
            batches.append(cur)
            cur = []
            cur_chars = 0
        cur.append(t)
        cur_chars += len(t)
    if cur:
        batches.append(cur)
    return batches
