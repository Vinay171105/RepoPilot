"""Runtime settings, read from environment variables at call time."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    embed_backend: str  # auto | st | hash
    embed_model: str
    data_dir: Path
    top_k: int = 6
    graph_extra: int = 4
    max_file_bytes: int = 200_000


def get_settings() -> Settings:
    return Settings(
        llm_base_url=os.getenv("REPOPILOT_LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
        llm_api_key=os.getenv("REPOPILOT_LLM_API_KEY", "none"),
        llm_model=os.getenv("REPOPILOT_LLM_MODEL", "llama3.1:8b"),
        embed_backend=os.getenv("REPOPILOT_EMBED_BACKEND", "auto"),
        embed_model=os.getenv("REPOPILOT_EMBED_MODEL", "BAAI/bge-small-en-v1.5"),
        data_dir=Path(os.getenv("REPOPILOT_DATA_DIR", "~/.repopilot")).expanduser(),
        top_k=int(os.getenv("REPOPILOT_TOP_K", "6")),
        graph_extra=int(os.getenv("REPOPILOT_GRAPH_EXTRA", "4")),
    )
