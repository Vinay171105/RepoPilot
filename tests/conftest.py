import pytest

from repopilot.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(
        llm_base_url="http://fake", llm_api_key="x", llm_model="fake",
        embed_backend="hash", embed_model="x", data_dir=tmp_path / "data",
    )


@pytest.fixture
def sample_repo(tmp_path):
    r = tmp_path / "sample"
    (r / "app").mkdir(parents=True)
    (r / "web").mkdir()
    (r / "app" / "__init__.py").write_text("")
    (r / "app" / "auth.py").write_text(
        '"""Authentication."""\nfrom .db import get_user\n\n\ndef authenticate_user(username, password):\n'
        '    """Check login credentials and return a session token."""\n    user = get_user(username)\n'
        '    if user and user["password"] == password:\n        return "token-" + username\n    return None\n'
    )
    (r / "app" / "db.py").write_text(
        'USERS = {"ann": {"password": "pw"}}\n\n\ndef get_user(name):\n    return USERS.get(name)\n'
    )
    (r / "app" / "payments.py").write_text(
        "def charge_invoice(amount, currency):\n    return {'amount': amount, 'currency': currency, 'status': 'paid'}\n"
    )
    (r / "web" / "api.ts").write_text(
        "import { render } from './view';\n\nexport function loadDashboard() {\n  return render('dashboard');\n}\n"
    )
    (r / "web" / "view.ts").write_text("export function render(name: string) {\n  return `<div>${name}</div>`;\n}\n")
    return r
