import json

from repopilot.extras.repomap import repo_map
from repopilot.extras.triage import triage
from repopilot.index.store import Index
from repopilot.indexer import build_index
from repopilot.qa import answer as answer_mod
from repopilot.llm import client


def test_index_roundtrip_and_retrieval(sample_repo, settings):
    idx = build_index(str(sample_repo), "sample", settings)
    loaded = Index.load("sample", settings)
    assert len(loaded.chunks) == len(idx.chunks)
    from repopilot.indexer import embedder_for
    from repopilot.qa.retrieve import retrieve

    res = retrieve(loaded, "authenticate user login password token", embedder_for(loaded, settings), k=2, graph_extra=2)
    assert res[0].chunk.file == "app/auth.py"
    assert "app/db.py" in {r.chunk.file for r in res}  # pulled in via the import graph


def test_repo_map(sample_repo, settings):
    m = repo_map(build_index(str(sample_repo), "sample", settings))
    assert m["import_edges"] >= 2
    assert m["most_imported"][0]["file"] in {"app/db.py", "web/view.ts"}


def _fake_llm(monkeypatch, payload):
    monkeypatch.setattr(client, "chat", lambda *a, **k: payload if isinstance(payload, str) else json.dumps(payload))


def test_ask_removes_hallucinated_citation(sample_repo, settings, monkeypatch):
    idx = build_index(str(sample_repo), "sample", settings)
    _fake_llm(monkeypatch, {
        "answer": "Login is in authenticate_user.",
        "citations": [
            {"file": "app/auth.py", "start_line": 5, "end_line": 9},
            {"file": "app/made_up.py", "start_line": 1, "end_line": 3},
        ],
    })
    out = answer_mod.ask(idx, "how does login authenticate user password?", settings)
    assert [c["file"] for c in out["citations"]] == ["app/auth.py"]
    assert out["dropped_citations"][0]["file"] == "app/made_up.py"


def test_ask_survives_non_json_model_output(sample_repo, settings, monkeypatch):
    idx = build_index(str(sample_repo), "sample", settings)
    _fake_llm(monkeypatch, "Sorry, here is a plain answer.")
    out = answer_mod.ask(idx, "login?", settings)
    assert out["answer"].startswith("Sorry") and out["citations"] == []


def test_parse_json_handles_fences_and_prose():
    assert client.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert client.parse_json('Sure! {"a": 2} hope that helps') == {"a": 2}


def test_triage_filters_labels(sample_repo, settings, monkeypatch):
    idx = build_index(str(sample_repo), "sample", settings)
    _fake_llm(monkeypatch, {"labels": ["Bug", "urgent"], "summary": "s", "citations": []})
    out = triage(idx, "login fails", "password rejected", settings)
    assert out["labels"] == ["bug"] and out["missing_info"] == []
