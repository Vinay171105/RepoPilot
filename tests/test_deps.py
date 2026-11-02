from repopilot.ingest.deps import build_graph


def test_python_relative_and_absolute_imports():
    files = {
        "app/__init__.py": "",
        "app/auth.py": "from .db import get_user\nimport app.payments\n",
        "app/db.py": "",
        "app/payments.py": "",
    }
    g = build_graph(files)
    assert g["app/auth.py"] == ["app/db.py", "app/payments.py"]


def test_python_src_layout_resolves_package_imports():
    files = {"src/pkg/a.py": "from pkg.b import x\n", "src/pkg/b.py": "x = 1\n"}
    assert build_graph(files)["src/pkg/a.py"] == ["src/pkg/b.py"]


def test_js_relative_imports():
    files = {"web/api.ts": "import { r } from './view';\n", "web/view.ts": "", "web/lib/index.ts": ""}
    files["web/x.ts"] = "import l from './lib';\n"
    g = build_graph(files)
    assert g["web/api.ts"] == ["web/view.ts"]
    assert g["web/x.ts"] == ["web/lib/index.ts"]
