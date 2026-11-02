"""A quick structural map of the repo from the import graph."""
from __future__ import annotations

from ..index.store import Index


def repo_map(index: Index, top: int = 10) -> dict:
    hubs = sorted(index.by_file, key=lambda f: -len(index.reverse.get(f, [])))
    return {
        "files": len(index.by_file),
        "chunks": len(index.chunks),
        "import_edges": sum(len(v) for v in index.graph.values()),
        "most_imported": [{"file": f, "imported_by": len(index.reverse.get(f, []))} for f in hubs[:top] if index.reverse.get(f)],
        "graph": index.graph,
    }
