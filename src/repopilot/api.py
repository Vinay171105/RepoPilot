"""FastAPI app: POST /index, POST /ask, GET /map/{repo}, GET /repos, plus a tiny web UI at /."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .config import get_settings
from .extras.repomap import repo_map
from .index.store import Index
from .indexer import build_index
from .llm.client import LLMError
from .qa.answer import ask

app = FastAPI(title="RepoPilot", version="0.1.0")
_cache: dict[str, Index] = {}


def _load(name: str) -> Index:
    if name not in _cache:
        try:
            _cache[name] = Index.load(name, get_settings())
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
    return _cache[name]


class IndexReq(BaseModel):
    source: str
    name: str | None = None


class AskReq(BaseModel):
    repo: str
    question: str


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (Path(__file__).parent / "static" / "index.html").read_text()


@app.get("/repos")
def repos() -> list[str]:
    return Index.list_names(get_settings())


@app.post("/index")
def index_repo(req: IndexReq) -> dict:
    try:
        idx = build_index(req.source, req.name)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))
    _cache[idx.name] = idx
    return {"name": idx.name, "files": idx.meta["files"], "chunks": len(idx.chunks)}


@app.post("/ask")
def ask_repo(req: AskReq) -> dict:
    try:
        return ask(_load(req.repo), req.question)
    except LLMError as e:
        raise HTTPException(502, str(e))


@app.get("/map/{repo}")
def map_repo(repo: str) -> dict:
    return repo_map(_load(repo))
