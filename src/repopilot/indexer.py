"""Fetch -> chunk -> graph -> embed -> save."""
from __future__ import annotations

from typing import Callable

from .config import Settings, get_settings
from .index.embed import get_embedder
from .index.store import Index
from .ingest.chunker import chunk_file
from .ingest.deps import build_graph
from .ingest.fetch import fetch_repo, iter_source_files


def build_index(
    source: str,
    name: str | None = None,
    settings: Settings | None = None,
    progress: Callable[[str], None] = lambda m: None,
) -> Index:
    settings = settings or get_settings()
    progress(f"Fetching {source} ...")
    root, auto_name = fetch_repo(source, settings)
    name = name or auto_name
    files = dict(iter_source_files(root, settings.max_file_bytes))
    if not files:
        raise ValueError("No supported source files found in that repository.")
    progress(f"Chunking {len(files)} files ...")
    chunks = [c for rel, src in files.items() for c in chunk_file(rel, src)]
    for i, c in enumerate(chunks):
        c.id = i
    graph = build_graph(files)
    emb = get_embedder(settings)
    progress(f"Embedding {len(chunks)} chunks with {emb.backend}:{emb.model} ...")
    vectors = emb.embed_documents([c.embed_text() for c in chunks])
    idx = Index(
        name, chunks, vectors, graph,
        {"source": source, "embed_backend": emb.backend, "embed_model": emb.model, "files": len(files)},
    )
    idx.save(settings)
    progress(f"Saved index '{name}' ({len(files)} files, {len(chunks)} chunks, {sum(len(v) for v in graph.values())} import edges).")
    return idx


def embedder_for(index: Index, settings: Settings):
    """Use the same embedder the index was built with."""
    return get_embedder(settings, index.meta.get("embed_backend"), index.meta.get("embed_model"))
