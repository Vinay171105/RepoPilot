"""Grounded Q&A: retrieve -> prompt -> structured JSON -> guard."""
from __future__ import annotations

from ..config import Settings, get_settings
from ..index.store import Index
from ..indexer import embedder_for
from ..llm import prompts
from ..llm.client import LLMFormatError, chat_json
from .guard import resolve_citations
from .retrieve import Retrieved, retrieve


def build_context(retrieved: list[Retrieved]) -> str:
    parts = []
    for i, r in enumerate(retrieved, 1):
        c = r.chunk
        body = "\n".join(f"{c.start_line + j:>5}| {ln}" for j, ln in enumerate(c.text.splitlines()))
        label = f"{c.kind} {c.name}".strip()
        parts.append(f"[{i}] {c.file} (lines {c.start_line}-{c.end_line}, {label})\n{body}")
    return "\n\n".join(parts)


def _sources(retrieved: list[Retrieved]) -> list[dict]:
    return [
        {"file": r.chunk.file, "start_line": r.chunk.start_line, "end_line": r.chunk.end_line,
         "score": round(r.score, 3), "via": r.via}
        for r in retrieved
    ]


def run_structured(index: Index, system: str, user: str, query: str, settings: Settings, embedder=None) -> dict:
    embedder = embedder or embedder_for(index, settings)
    retrieved = retrieve(index, query, embedder, settings.top_k, settings.graph_extra)
    if not retrieved:
        return {"answer": "The index is empty.", "citations": [], "dropped_citations": [], "retrieved": []}
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{user}\n\nCode excerpts:\n\n{build_context(retrieved)}"},
    ]
    try:
        data = chat_json(messages, settings=settings)
    except LLMFormatError as e:  # degrade gracefully: show raw text, no citations
        data = {"answer": e.raw, "citations": []}
    valid, dropped = resolve_citations(data.get("citations"), retrieved)
    data["citations"], data["dropped_citations"], data["retrieved"] = valid, dropped, _sources(retrieved)
    return data


def ask(index: Index, question: str, settings: Settings | None = None, embedder=None) -> dict:
    settings = settings or get_settings()
    out = run_structured(index, prompts.QA_SYSTEM, f"Question: {question}", question, settings, embedder)
    out.setdefault("answer", "")
    return out
