"""Explain a file/function and suggest tests for it."""
from __future__ import annotations

from ..config import Settings, get_settings
from ..index.store import Index
from ..indexer import embedder_for
from ..ingest.chunker import Chunk
from ..llm import prompts
from ..llm.client import chat
from ..qa.answer import build_context
from ..qa.retrieve import Retrieved, retrieve

MAX_CHUNKS = 10


def select_chunks(index: Index, target: str, settings: Settings, embedder=None) -> list[Chunk]:
    t = target.strip().replace("\\", "/")
    files = [f for f in index.by_file if f == t or f.endswith("/" + t)]
    if files:
        return index.by_file[files[0]][:MAX_CHUNKS]
    sym = [c for c in index.chunks if c.name and (c.name == t or c.name.split(" ")[0].endswith("." + t) or c.name.split(" ")[0] == t)]
    if sym:
        return sym[:MAX_CHUNKS]
    embedder = embedder or embedder_for(index, settings)
    return [r.chunk for r in retrieve(index, target, embedder, 4, 0)]


def _run(index: Index, target: str, system: str, settings: Settings | None, embedder=None) -> dict:
    settings = settings or get_settings()
    chunks = select_chunks(index, target, settings, embedder)
    if not chunks:
        return {"text": f"Nothing found for {target!r}.", "sources": []}
    # include what the first file imports, so the explanation can place it in the project
    f0 = chunks[0].file
    deps = index.graph.get(f0, [])
    used_by = index.reverse.get(f0, [])
    ctx = (
        f"Target: {target}\nFile {f0} imports: {', '.join(deps) or 'none'}\n"
        f"File {f0} is imported by: {', '.join(used_by[:8]) or 'none'}\n\n"
        + build_context([Retrieved(c, 1.0, "vector") for c in chunks])
    )
    text = chat([{"role": "system", "content": system}, {"role": "user", "content": ctx}], temperature=0.2, settings=settings)
    return {"text": text, "sources": [{"file": c.file, "start_line": c.start_line, "end_line": c.end_line} for c in chunks]}


def explain(index: Index, target: str, settings: Settings | None = None, embedder=None) -> dict:
    return _run(index, target, prompts.EXPLAIN_SYSTEM, settings, embedder)


def suggest_tests(index: Index, target: str, settings: Settings | None = None, embedder=None) -> dict:
    return _run(index, target, prompts.TESTS_SYSTEM, settings, embedder)
