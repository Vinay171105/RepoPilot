from repopilot.ingest.chunker import chunk_file

PY = '''import os

X = 1


def a():
    return 1


class Foo:
    def m(self):
        return 2
'''


def test_python_chunks_follow_definitions():
    chunks = chunk_file("pkg/mod.py", PY)
    names = [(c.kind, c.name) for c in chunks]
    assert ("function", "a") in names and ("class", "Foo") in names
    a = next(c for c in chunks if c.name == "a")
    assert (a.start_line, a.end_line) == (6, 7)
    assert a.text.startswith("def a")


def test_large_class_splits_into_methods():
    body = "\n".join(f"    def m{i}(self):\n" + "\n".join(f"        x{j} = {j}" for j in range(5)) for i in range(20))
    chunks = chunk_file("big.py", f"class Big:\n{body}\n")
    assert any(c.kind == "method" and c.name == "Big.m3" for c in chunks)


def test_js_uses_declaration_boundaries():
    src = "import x from 'y';\n\nexport function one() {\n  return 1;\n}\n\nexport function two() {\n  return 2;\n}\n"
    chunks = chunk_file("a.ts", src)
    assert all(c.start_line >= 1 and c.end_line >= c.start_line for c in chunks)
    assert {c.name for c in chunks} >= {"<header>"} or any(c.name in {"one", "two"} for c in chunks)


def test_syntax_error_falls_back_to_windows():
    assert chunk_file("bad.py", "def (:\n  nope\n")


def test_long_file_is_windowed_with_valid_ranges():
    src = "\n".join(f"line {i}" for i in range(300))
    chunks = chunk_file("notes.md", src)
    assert len(chunks) > 3
    assert chunks[0].start_line == 1 and chunks[-1].end_line == 300
