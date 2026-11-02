"""repopilot command line."""
from __future__ import annotations

import argparse
import json
import sys

from .config import get_settings
from .index.store import Index
from .indexer import build_index
from .llm.client import LLMError


def _print_sources(citations: list[dict]) -> None:
    if citations:
        print("\nSources:")
        for c in citations:
            sym = f"  ({c['symbol']})" if c.get("symbol") else ""
            print(f"  {c['file']}:{c['start_line']}-{c['end_line']}{sym}")


def cmd_index(a, s) -> int:
    build_index(a.source, a.name, s, progress=lambda m: print(m, file=sys.stderr))
    return 0


def cmd_list(a, s) -> int:
    names = Index.list_names(s)
    print("\n".join(names) if names else "No indexes yet. Run: repopilot index <repo>")
    return 0


def cmd_ask(a, s) -> int:
    from .qa.answer import ask

    out = ask(Index.load(a.repo, s), a.question, s)
    if a.json:
        print(json.dumps(out, indent=2))
        return 0
    print(out["answer"])
    _print_sources(out["citations"])
    if out["dropped_citations"]:
        print(f"\n({len(out['dropped_citations'])} citation(s) removed: not in retrieved code)")
    return 0


def cmd_map(a, s) -> int:
    from .extras.repomap import repo_map

    m = repo_map(Index.load(a.repo, s))
    print(f"{m['files']} files, {m['chunks']} chunks, {m['import_edges']} import edges\n\nMost imported:")
    for h in m["most_imported"]:
        print(f"  {h['imported_by']:>3}  {h['file']}")
    return 0


def _extra(fn_name: str):
    def run(a, s) -> int:
        from .extras import explain as ex

        out = getattr(ex, fn_name)(Index.load(a.repo, s), a.target, s)
        print(out["text"])
        print("\nBased on:")
        for src in out["sources"]:
            print(f"  {src['file']}:{src['start_line']}-{src['end_line']}")
        return 0

    return run


def cmd_triage(a, s) -> int:
    from .extras.triage import triage

    out = triage(Index.load(a.repo, s), a.title, a.body or "", s)
    if a.json:
        print(json.dumps(out, indent=2))
        return 0
    print(f"Labels: {', '.join(out['labels'])}\nSummary: {out.get('summary', '')}")
    if out["missing_info"]:
        print("Missing info:\n" + "\n".join(f"  - {m}" for m in out["missing_info"]))
    print(f"\nDraft reply (for a human to review):\n{out['draft_reply']}")
    _print_sources(out["citations"])
    return 0


def cmd_serve(a, s) -> int:
    import uvicorn

    uvicorn.run("repopilot.api:app", host=a.host, port=a.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="repopilot", description="Ask questions about any codebase, with real citations.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("index", help="index a repo (path, GitHub URL, or owner/name)")
    sp.add_argument("source"); sp.add_argument("--name"); sp.set_defaults(fn=cmd_index)

    sub.add_parser("list", help="list indexed repos").set_defaults(fn=cmd_list)

    sp = sub.add_parser("ask", help="ask a question about an indexed repo")
    sp.add_argument("repo"); sp.add_argument("question"); sp.add_argument("--json", action="store_true"); sp.set_defaults(fn=cmd_ask)

    sp = sub.add_parser("map", help="show the import structure")
    sp.add_argument("repo"); sp.set_defaults(fn=cmd_map)

    for name, fn in (("explain", "explain"), ("tests", "suggest_tests")):
        sp = sub.add_parser(name, help=f"{name} a file or function")
        sp.add_argument("repo"); sp.add_argument("target"); sp.set_defaults(fn=_extra(fn))

    sp = sub.add_parser("triage", help="triage an issue: labels, likely files, draft reply")
    sp.add_argument("repo"); sp.add_argument("--title", required=True); sp.add_argument("--body", default="")
    sp.add_argument("--json", action="store_true"); sp.set_defaults(fn=cmd_triage)

    sp = sub.add_parser("serve", help="run the web UI and API")
    sp.add_argument("--host", default="127.0.0.1"); sp.add_argument("--port", type=int, default=8000); sp.set_defaults(fn=cmd_serve)

    a = p.parse_args(argv)
    try:
        return a.fn(a, get_settings())
    except (FileNotFoundError, ValueError, RuntimeError, LLMError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
