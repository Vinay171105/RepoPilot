"""Get a repo onto disk and walk its source files."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterator

from ..config import Settings

SKIP_DIRS = {
    "node_modules", "venv", ".venv", "env", "dist", "build", "target", "vendor",
    "__pycache__", "site-packages", "coverage", "out", "bin", "obj",
}
CODE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt",
    ".rb", ".php", ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".swift", ".scala", ".sh",
}
TEXT_EXT = {".md", ".rst", ".txt", ".toml", ".yml", ".yaml"}
SPECIAL_NAMES = {"Dockerfile", "Makefile", "package.json", "go.mod", "Cargo.toml", "requirements.txt"}


def slugify(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-").lower() or "repo"


def parse_source(source: str) -> tuple[str, str, str]:
    """Return (kind, location, default_name). kind is 'local' or 'git'."""
    s = source.strip()
    p = Path(s).expanduser()
    if p.is_dir():
        return "local", str(p.resolve()), slugify(p.resolve().name)
    if s.startswith(("http://", "https://", "git@")):
        parts = [x for x in re.split(r"[/:]", re.sub(r"\.git$", "", s.rstrip("/"))) if x]
        return "git", s, slugify("-".join(parts[-2:]))
    m = re.match(r"^([\w.-]+)/([\w.-]+)$", s)
    if m:
        owner, repo = m.groups()
        return "git", f"https://github.com/{owner}/{repo}.git", slugify(f"{owner}-{repo}")
    raise ValueError(f"Can't understand repo source: {source!r} (use a path, URL, or owner/name)")


def fetch_repo(source: str, settings: Settings) -> tuple[Path, str]:
    kind, loc, name = parse_source(source)
    if kind == "local":
        return Path(loc), name
    if shutil.which("git") is None:
        raise RuntimeError("git is required to clone remote repositories")
    dest = settings.data_dir / "repos" / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(["git", "clone", "--depth", "1", loc, str(dest)], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr.strip()}")
    return dest, name


def iter_source_files(root: Path, max_bytes: int = 200_000, max_files: int = 5000) -> Iterator[tuple[str, str]]:
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if fn.endswith((".min.js", ".min.css")) or not (ext in CODE_EXT or ext in TEXT_EXT or fn in SPECIAL_NAMES):
                continue
            path = Path(dirpath) / fn
            try:
                if path.stat().st_size > max_bytes:
                    continue
                data = path.read_bytes()
            except OSError:
                continue
            if b"\0" in data:
                continue
            yield path.relative_to(root).as_posix(), data.decode("utf-8", errors="replace")
            n += 1
            if n >= max_files:
                return
