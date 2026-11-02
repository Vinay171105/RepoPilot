"""On-disk index: chunk metadata (JSON) + vectors (.npy) + import graph."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ..config import Settings
from ..ingest.chunker import Chunk


class Index:
    def __init__(self, name: str, chunks: list[Chunk], vectors: np.ndarray, graph: dict[str, list[str]], meta: dict):
        self.name = name
        self.chunks = chunks
        self.vectors = vectors
        self.graph = graph
        self.meta = meta
        self.by_file: dict[str, list[Chunk]] = {}
        for c in chunks:
            self.by_file.setdefault(c.file, []).append(c)
        self.reverse: dict[str, list[str]] = {}
        for src, dsts in graph.items():
            for d in dsts:
                self.reverse.setdefault(d, []).append(src)

    def neighbors(self, file: str) -> set[str]:
        return set(self.graph.get(file, [])) | set(self.reverse.get(file, []))

    @staticmethod
    def path_for(name: str, settings: Settings) -> Path:
        return settings.data_dir / "indexes" / name

    def save(self, settings: Settings) -> Path:
        d = self.path_for(self.name, settings)
        d.mkdir(parents=True, exist_ok=True)
        np.save(d / "vectors.npy", self.vectors)
        (d / "meta.json").write_text(
            json.dumps({"name": self.name, "meta": self.meta, "graph": self.graph, "chunks": [asdict(c) for c in self.chunks]})
        )
        return d

    @classmethod
    def load(cls, name: str, settings: Settings) -> "Index":
        d = cls.path_for(name, settings)
        if not (d / "meta.json").exists():
            raise FileNotFoundError(f"No index named {name!r}. Run: repopilot index <repo>")
        data = json.loads((d / "meta.json").read_text())
        chunks = [Chunk(**c) for c in data["chunks"]]
        return cls(data["name"], chunks, np.load(d / "vectors.npy"), data["graph"], data["meta"])

    @staticmethod
    def list_names(settings: Settings) -> list[str]:
        root = settings.data_dir / "indexes"
        return sorted(p.name for p in root.iterdir() if (p / "meta.json").exists()) if root.exists() else []
