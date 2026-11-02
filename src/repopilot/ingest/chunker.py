"""Split source files into chunks along function/class boundaries.

Python uses the `ast` module. Other languages use a light declaration-boundary
heuristic, then fall back to overlapping line windows. Every chunk keeps its
file path and line range so answers can cite real locations.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

MAX_LINES = 80
WINDOW = 60
OVERLAP = 10
MIN_LINES = 8

_DECL_RE = re.compile(
    r"^(?:export\s|async\s|function[\s*]|class\s|def\s|func\s|fn\s|pub[\s(]|const\s|interface\s|type\s|"
    r"public\s|private\s|protected\s|static\s|impl\b|struct\s|enum\s|trait\s|module\s|package\s)"
)
_NAME_RE = re.compile(
    r"(?:function\*?|class|def|func|fn|interface|type|struct|enum|trait|impl)\s+([A-Za-z_$][\w$]*)"
    r"|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="
)


@dataclass
class Chunk:
    file: str
    start_line: int
    end_line: int
    kind: str
    name: str
    text: str
    id: int = -1

    def embed_text(self) -> str:
        head = f"File: {self.file}\n{self.kind} {self.name}".rstrip()
        return f"{head}\n{self.text[:3000]}"


Span = tuple[int, int, str, str]  # start, end (1-based inclusive), kind, name


def _start(node: ast.AST) -> int:
    decos = getattr(node, "decorator_list", [])
    return min([node.lineno] + [d.lineno for d in decos])


def _class_spans(node: ast.ClassDef) -> list[Span]:
    methods = [c for c in node.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))]
    start = _start(node)
    if not methods:
        return [(start, node.end_lineno, "class", node.name)]
    first = _start(methods[0])
    out: list[Span] = [(start, max(start, first - 1), "class", node.name)]
    for m in methods:
        out.append((_start(m), m.end_lineno, "method", f"{node.name}.{m.name}"))
    return out


def _py_spans(src: str) -> list[Span]:
    tree = ast.parse(src)
    spans: list[Span] = []
    pend: tuple[int, int] | None = None

    def flush() -> None:
        nonlocal pend
        if pend:
            spans.append((pend[0], pend[1], "module", "<module>"))
            pend = None

    for node in tree.body:
        s, e = _start(node), node.end_lineno
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            flush()
            spans.append((s, e, "function", node.name))
        elif isinstance(node, ast.ClassDef):
            flush()
            spans.extend(_class_spans(node) if e - s + 1 > MAX_LINES else [(s, e, "class", node.name)])
        else:
            pend = (pend[0] if pend else s, e)
    flush()
    return spans


def _guess(line: str) -> tuple[str, str]:
    m = _NAME_RE.search(line)
    if not m:
        return "block", ""
    if m.group(1):
        kw = line[: m.start(1)].split()[-1].strip("*") if line[: m.start(1)].split() else "function"
        return ("class" if kw in {"class", "struct", "interface", "enum", "trait", "impl"} else "function"), m.group(1)
    return "const", m.group(2)


def _boundary_spans(lines: list[str]) -> list[Span] | None:
    starts = [i for i, ln in enumerate(lines) if _DECL_RE.match(ln)]
    if len(starts) < 2:
        return None
    raw: list[Span] = []
    if starts[0] > 0:
        raw.append((1, starts[0], "module", "<header>"))
    for j, s in enumerate(starts):
        e = starts[j + 1] if j + 1 < len(starts) else len(lines)
        kind, name = _guess(lines[s])
        raw.append((s + 1, e, kind, name))
    merged: list[Span] = []
    for sp in raw:  # merge tiny neighbours so we don't embed one-liners alone
        if merged and (merged[-1][1] - merged[-1][0] + 1) < MIN_LINES and (sp[1] - merged[-1][0] + 1) <= MAX_LINES:
            p = merged[-1]
            merged[-1] = (p[0], sp[1], p[2], p[3])
        else:
            merged.append(sp)
    return merged


def _window_spans(n_lines: int) -> list[Span]:
    spans, step, i = [], WINDOW - OVERLAP, 0
    while i < n_lines:
        spans.append((i + 1, min(i + WINDOW, n_lines), "block", ""))
        if i + WINDOW >= n_lines:
            break
        i += step
    return spans


def _to_chunks(rel: str, lines: list[str], spans: list[Span]) -> list[Chunk]:
    out: list[Chunk] = []
    for s, e, kind, name in spans:
        pieces = [(s, e, name)]
        if e - s + 1 > MAX_LINES:
            pieces, i, part = [], s, 1
            while i <= e:
                j = min(i + WINDOW - 1, e)
                pieces.append((i, j, f"{name} (part {part})".strip()))
                if j == e:
                    break
                i, part = j + 1 - OVERLAP, part + 1
        for ps, pe, pname in pieces:
            text = "\n".join(lines[ps - 1 : pe]).rstrip()
            if text.strip():
                out.append(Chunk(rel, ps, pe, kind, pname, text))
    return out


def chunk_file(rel: str, src: str) -> list[Chunk]:
    lines = src.splitlines()
    if not lines:
        return []
    spans: list[Span] | None = None
    if rel.endswith(".py"):
        try:
            spans = _py_spans(src)
        except SyntaxError:
            spans = None
    elif not rel.endswith((".md", ".rst", ".txt", ".yml", ".yaml", ".toml")):
        spans = _boundary_spans(lines)
    if not spans:
        spans = _window_spans(len(lines))
    return _to_chunks(rel, lines, spans)
