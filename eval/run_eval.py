"""Measure RepoPilot on a question set.

  python eval/run_eval.py eval/questions.json                # retrieval + LLM answers
  python eval/run_eval.py eval/questions.json --retrieval-only

Metrics
  retrieval hit@k   any gold file appears in the retrieved chunks
  citation hit      any valid citation points at a gold file
  keyword accuracy  all expected keywords appear in the answer (crude but reproducible)
  hallucinated      citations the guard had to remove (lower is better)
"""
from __future__ import annotations

import argparse
import json

from repopilot.config import get_settings
from repopilot.index.store import Index
from repopilot.indexer import embedder_for
from repopilot.qa.answer import ask
from repopilot.qa.retrieve import retrieve


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions")
    ap.add_argument("--repo")
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--out", default="eval/results.md")
    a = ap.parse_args()

    spec = json.load(open(a.questions))
    s = get_settings()
    idx = Index.load(a.repo or spec["repo"], s)
    emb = embedder_for(idx, s)
    qs = spec["questions"]

    hits = cite_hits = kw_ok = dropped = 0
    rows = []
    for item in qs:
        gold = set(item["gold_files"])
        retrieved = retrieve(idx, item["q"], emb, s.top_k, s.graph_extra)
        r_hit = bool(gold & {r.chunk.file for r in retrieved})
        hits += r_hit
        c_hit = k_ok = None
        if not a.retrieval_only:
            out = ask(idx, item["q"], s, emb)
            c_hit = bool(gold & {c["file"] for c in out["citations"]})
            k_ok = all(k.lower() in out["answer"].lower() for k in item.get("keywords", []))
            cite_hits += c_hit
            kw_ok += k_ok
            dropped += len(out["dropped_citations"])
        rows.append((item["q"], r_hit, c_hit, k_ok))

    n = len(qs)
    lines = [f"# RepoPilot eval: {idx.name} ({n} questions)", "", f"- Retrieval hit@{s.top_k}(+graph): **{hits}/{n}** ({hits / n:.0%})"]
    if not a.retrieval_only:
        lines += [
            f"- Citation hit: **{cite_hits}/{n}** ({cite_hits / n:.0%})",
            f"- Keyword accuracy: **{kw_ok}/{n}** ({kw_ok / n:.0%})",
            f"- Hallucinated citations removed by guard: **{dropped}**",
        ]
    lines += ["", "| Question | Retrieved gold | Cited gold | Keywords |", "|---|---|---|---|"]
    mark = lambda v: "-" if v is None else ("yes" if v else "no")
    lines += [f"| {q} | {mark(r)} | {mark(c)} | {mark(k)} |" for q, r, c, k in rows]
    text = "\n".join(lines)
    print(text)
    open(a.out, "w").write(text + "\n")


if __name__ == "__main__":
    main()
