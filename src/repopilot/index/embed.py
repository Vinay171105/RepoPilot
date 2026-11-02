"""Embedders. `st` = sentence-transformers (open model, recommended).
`hash` = dependency-free hashing embedder: works offline and in tests, weaker quality."""
from __future__ import annotations

import math
import re
import zlib
from functools import lru_cache

import numpy as np

from ..config import Settings

_TOKEN = re.compile(r"[A-Za-z][a-z0-9]+|[A-Z]+(?![a-z])|\d+")
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def _stem(t: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[: -len(suf)]
    return t


class HashEmbedder:
    backend = "hash"
    model = "hashing-512"
    dim = 512

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        counts: dict[str, int] = {}
        for t in _TOKEN.findall(text):
            t = _stem(t.lower())
            counts[t] = counts.get(t, 0) + 1
        for tok, c in counts.items():
            h = zlib.crc32(tok.encode())
            sign = 1.0 if (h >> 31) & 1 else -1.0
            v[h % self.dim] += sign * (1.0 + math.log(c))
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vec(t) for t in texts]) if texts else np.zeros((0, self.dim), dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self._vec(text)


class STEmbedder:
    backend = "st"

    def __init__(self, model: str):
        from sentence_transformers import SentenceTransformer  # lazy: heavy import

        self.model = model
        self._m = SentenceTransformer(model)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self._m.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=len(texts) > 200),
            dtype=np.float32,
        )

    def embed_query(self, text: str) -> np.ndarray:
        prefix = BGE_QUERY_PREFIX if "bge" in self.model.lower() else ""
        return np.asarray(self._m.encode([prefix + text], normalize_embeddings=True)[0], dtype=np.float32)


@lru_cache(maxsize=4)
def _st(model: str) -> STEmbedder:
    return STEmbedder(model)


def _have_st() -> bool:
    try:
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False


def get_embedder(settings: Settings, backend: str | None = None, model: str | None = None):
    backend = backend or settings.embed_backend
    model = model or settings.embed_model
    if backend == "auto":
        backend = "st" if _have_st() else "hash"
    if backend == "st":
        return _st(model)
    if backend == "hash":
        return HashEmbedder()
    raise ValueError(f"Unknown embed backend: {backend}")
