from repopilot.ingest.chunker import Chunk
from repopilot.qa.guard import resolve_citations
from repopilot.qa.retrieve import Retrieved


def _r():
    c = Chunk("app/auth.py", 10, 30, "function", "login", "code", id=0)
    return [Retrieved(c, 0.9, "vector")]


def test_invented_file_is_dropped():
    valid, dropped = resolve_citations([{"file": "app/secret.py", "start_line": 1, "end_line": 5}], _r())
    assert valid == [] and len(dropped) == 1


def test_lines_are_clamped_to_retrieved_range():
    valid, _ = resolve_citations([{"file": "./app/auth.py", "start_line": 5, "end_line": 20}], _r())
    assert (valid[0]["start_line"], valid[0]["end_line"]) == (10, 20)


def test_non_overlapping_lines_fall_back_to_chunk_range():
    valid, _ = resolve_citations([{"file": "app/auth.py", "start_line": 500, "end_line": 600}], _r())
    assert (valid[0]["start_line"], valid[0]["end_line"]) == (10, 30)


def test_excerpt_number_resolves_when_file_missing():
    valid, _ = resolve_citations([{"excerpt": 1}], _r())
    assert valid[0]["file"] == "app/auth.py"


def test_garbage_and_duplicates():
    valid, dropped = resolve_citations(["x", {"file": "app/auth.py"}, {"file": "app/auth.py"}], _r())
    assert len(valid) == 1 and dropped == ["x"]
    assert resolve_citations(None, _r()) == ([], [])
