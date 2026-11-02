"""Grounding guard: a citation survives only if it points at code we actually retrieved."""
from __future__ import annotations

from .retrieve import Retrieved


def _norm(path: str) -> str:
    p = path.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def _int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def resolve_citations(raw, retrieved: list[Retrieved]) -> tuple[list[dict], list]:
    """Return (valid_citations, dropped_raw_citations). Never lets an invented path through."""
    valid: list[dict] = []
    dropped: list = []
    seen: set[tuple] = set()
    for c in raw if isinstance(raw, list) else []:
        if not isinstance(c, dict):
            dropped.append(c)
            continue
        s, e = _int(c.get("start_line")), _int(c.get("end_line"))
        f = c.get("file")
        ex = _int(c.get("excerpt"))
        cands = []
        if isinstance(f, str) and f.strip():
            cands = [r.chunk for r in retrieved if r.chunk.file == _norm(f)]
        elif ex is not None and 1 <= ex <= len(retrieved):
            cands = [retrieved[ex - 1].chunk]
        if not cands:
            dropped.append(c)  # invented or un-retrieved file
            continue
        chunk = cands[0]
        if s is not None and e is not None:
            if e < s:
                s, e = e, s
            best = max(cands, key=lambda ch: max(0, min(e, ch.end_line) - max(s, ch.start_line) + 1))
            if min(e, best.end_line) >= max(s, best.start_line):
                chunk, s, e = best, max(s, best.start_line), min(e, best.end_line)
            else:
                s, e = chunk.start_line, chunk.end_line
        else:
            s, e = chunk.start_line, chunk.end_line
        key = (chunk.file, s, e)
        if key in seen:
            continue
        seen.add(key)
        valid.append({"file": chunk.file, "start_line": s, "end_line": e, "symbol": chunk.name})
    return valid, dropped
