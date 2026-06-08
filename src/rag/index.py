"""Local vector index for code retrieval — parquet-backed for portability.

This is a single-machine, file-backed index. Build it once (`scripts/index_codebase.py`)
and `load_index()` to query. ~20MB for a 5K-chunk Hyperswitch index at 1024 dims.
The dashboard never touches this; only the offline agent runner does, after
which the per-bulletin top-k results are baked into the eval JSON.

Stored as a parquet file with columns:
    relative_path, module_path, start_line, end_line, text, embedding (list[float])
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src.rag.chunker import Chunk


@dataclass
class IndexedChunk:
    relative_path: str
    module_path: str
    start_line: int
    end_line: int
    text: str
    score: float  # cosine similarity to a query (only meaningful after retrieve())

    @property
    def line_span(self) -> str:
        return f"{self.relative_path}:{self.start_line}-{self.end_line}"


class CodeIndex:
    """Parquet-backed vector index with cosine retrieval.

    Embeddings are stored as a (N, dim) float32 numpy array alongside a
    pandas DataFrame of metadata. Cosine retrieval is exact (small N).
    """

    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray):
        self._df = df.reset_index(drop=True)
        # Normalize once so retrieval is a single matmul.
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        self._embeddings = (embeddings / norms).astype(np.float32)

    @property
    def n_chunks(self) -> int:
        return len(self._df)

    @property
    def dim(self) -> int:
        return int(self._embeddings.shape[1])

    @classmethod
    def from_chunks_and_vectors(
        cls,
        chunks: Iterable[Chunk],
        vectors: list[list[float]],
    ) -> "CodeIndex":
        chunks_list = list(chunks)
        if len(chunks_list) != len(vectors):
            raise ValueError(
                f"chunk/vector count mismatch: {len(chunks_list)} vs {len(vectors)}"
            )
        df = pd.DataFrame(
            [
                {
                    "relative_path": c.relative_path,
                    "module_path": c.module_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "text": c.text,
                }
                for c in chunks_list
            ]
        )
        emb = np.asarray(vectors, dtype=np.float32)
        return cls(df, emb)

    def retrieve(self, query_embedding: list[float], *, top_k: int = 5) -> list[IndexedChunk]:
        q = np.asarray(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm
        scores = self._embeddings @ q  # cosine similarity (already normalized)
        if top_k >= len(scores):
            top_indices = np.argsort(-scores)
        else:
            # argpartition for top-k, then sort just those for ordering.
            top_indices = np.argpartition(-scores, top_k)[:top_k]
            top_indices = top_indices[np.argsort(-scores[top_indices])]
        results: list[IndexedChunk] = []
        for i in top_indices[:top_k]:
            row = self._df.iloc[int(i)]
            results.append(
                IndexedChunk(
                    relative_path=row["relative_path"],
                    module_path=row["module_path"],
                    start_line=int(row["start_line"]),
                    end_line=int(row["end_line"]),
                    text=row["text"],
                    score=float(scores[int(i)]),
                )
            )
        return results

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Store embeddings as a list[float] column in the parquet — simple,
        # and pandas/pyarrow round-trips it cleanly.
        df = self._df.copy()
        df["embedding"] = [list(row) for row in self._embeddings]
        df.to_parquet(path, compression="zstd")


def load_index(path: Path) -> CodeIndex:
    df = pd.read_parquet(path)
    embeddings = np.asarray([list(e) for e in df["embedding"]], dtype=np.float32)
    df = df.drop(columns=["embedding"])
    return CodeIndex(df, embeddings)


def build_index(chunks: Iterable[Chunk], vectors: list[list[float]]) -> CodeIndex:
    """Convenience constructor."""
    return CodeIndex.from_chunks_and_vectors(chunks, vectors)
