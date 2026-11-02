"""Issue triage: labels, missing info, likely files, and a draft reply (for a human to approve)."""
from __future__ import annotations

from ..config import Settings, get_settings
from ..index.store import Index
from ..llm import prompts
from ..qa.answer import run_structured

ALLOWED = {"bug", "feature", "question", "docs"}


def triage(index: Index, title: str, body: str, settings: Settings | None = None, embedder=None) -> dict:
    settings = settings or get_settings()
    query = f"{title}\n{body[:1500]}"
    out = run_structured(index, prompts.TRIAGE_SYSTEM, f"Issue title: {title}\n\nIssue body:\n{body[:3000]}", query, settings, embedder)
    labels = [str(x).lower() for x in out.get("labels", []) if str(x).lower() in ALLOWED] if isinstance(out.get("labels"), list) else []
    out["labels"] = labels or ["question"]
    out.setdefault("missing_info", [])
    out.setdefault("draft_reply", "")
    return out
