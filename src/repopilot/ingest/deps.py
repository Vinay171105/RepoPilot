"""Build a file-level import graph (Python and JS/TS)."""
from __future__ import annotations

import ast
import posixpath
import re

_JS_IMPORT = re.compile(r"""(?:from\s+|import\s+|require\(\s*)['"](\.{1,2}/[^'"]*|\.{1,2})['"]""")
_JS_EXT = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]


def _py_module_index(files: set[str]) -> dict[str, str]:
    """dotted-name suffix -> file, so `pkg.mod` resolves even under src/."""
    idx: dict[str, str] = {}
    for f in sorted(files):
        if not f.endswith(".py"):
            continue
        parts = f[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        for i in range(len(parts)):
            idx.setdefault(".".join(parts[i:]), f)
    return idx


def _py_edges(rel: str, src: str, files: set[str], idx: dict[str, str]) -> set[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    out: set[str] = set()

    def rel_lookup(parts: list[str]) -> str | None:
        base = "/".join(parts)
        for cand in (f"{base}.py", f"{base}/__init__.py"):
            if cand in files:
                return cand
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                bits = a.name.split(".")
                for n in range(len(bits), 0, -1):
                    hit = idx.get(".".join(bits[:n]))
                    if hit:
                        out.add(hit)
                        break
        elif isinstance(node, ast.ImportFrom):
            names = [a.name for a in node.names]
            if node.level:
                pkg = rel.split("/")[:-1]
                if node.level > 1:
                    pkg = pkg[: -(node.level - 1)] if len(pkg) >= node.level - 1 else []
                mod = node.module.split(".") if node.module else []
                hit = rel_lookup(pkg + mod)
                if hit:
                    out.add(hit)
                for n in names:
                    sub = rel_lookup(pkg + mod + [n])
                    if sub:
                        out.add(sub)
            elif node.module:
                hit = idx.get(node.module)
                if hit:
                    out.add(hit)
                for n in names:
                    sub = idx.get(f"{node.module}.{n}")
                    if sub:
                        out.add(sub)
    out.discard(rel)
    return out


def _js_edges(rel: str, src: str, files: set[str]) -> set[str]:
    out: set[str] = set()
    base = posixpath.dirname(rel)
    for m in _JS_IMPORT.finditer(src):
        target = posixpath.normpath(posixpath.join(base, m.group(1)))
        cands = [target] + [target + e for e in _JS_EXT] + [f"{target}/index{e}" for e in _JS_EXT]
        for c in cands:
            if c in files:
                out.add(c)
                break
    out.discard(rel)
    return out


def build_graph(sources: dict[str, str]) -> dict[str, list[str]]:
    """file -> sorted list of files it imports."""
    files = set(sources)
    py_idx = _py_module_index(files)
    graph: dict[str, list[str]] = {}
    for rel, src in sources.items():
        if rel.endswith(".py"):
            edges = _py_edges(rel, src, files, py_idx)
        elif rel.endswith(tuple(_JS_EXT)):
            edges = _js_edges(rel, src, files)
        else:
            continue
        if edges:
            graph[rel] = sorted(edges)
    return graph
