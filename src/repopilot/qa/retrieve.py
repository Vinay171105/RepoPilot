"""Vector search plus import-graph expansion."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..index.store import Index
from ..ingest.chunker import Chunk


@dataclass
class Retrieved:
    chunk: Chunk
    score: float
    via: str  # "vector" or "graph"


def retrieve(index: Index, query: str, embedder, k: int = 6, graph_extra: int = 4) -> list[Retrieved]:
    if not len(index.chunks):
        return []
    sims = index.vectors @ embedder.embed_query(query)
    order = np.argsort(-sims)
    out = [Retrieved(index.chunks[i], float(sims[i]), "vector") for i in order[:k]]

    if graph_extra > 0:
        have = {r.chunk.id for r in out}
        top_files = list(dict.fromkeys(r.chunk.file for r in out))[:3]
        near = set().union(*(index.neighbors(f) for f in top_files)) - {r.chunk.file for r in out}
        cands = [c for f in near for c in index.by_file.get(f, []) if c.id not in have]
        cands.sort(key=lambda c: -float(sims[c.id]))
        out += [Retrieved(c, float(sims[c.id]), "graph") for c in cands[:graph_extra]]
    return out
