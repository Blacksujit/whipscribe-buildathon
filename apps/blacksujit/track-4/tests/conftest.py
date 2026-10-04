"""Shared pytest setup: fully offline, isolated database.

Everything here runs before any test module imports ``app`` or ``src``:

* ``.env`` is never loaded (``dotenv.load_dotenv`` becomes a no-op) and every
  provider key is removed from the environment, so no test can reach the real
  WhipScribe / Groq / Slack / Notion / HubSpot accounts.
* ``DB_PATH`` points at a throwaway copy of ``seed_evaluations.db`` so route
  tests read the real seeded calls without touching the developer database.
* An autouse fixture makes any outbound ``requests`` call or socket connect
  raise, so a test that accidentally goes to the network fails loudly.
"""

import json
import os
import shutil
import socket
import sys
import tempfile

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

SEED_DB = os.path.join(PROJECT_DIR, "seed_evaluations.db")

# --- environment isolation (must happen before app / store import) ----------
import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *args, **kwargs: False

_SECRET_ENV = (
    "WHIPSKRIBE_API_KEY", "WHIPSCRIBE_API_KEY",
    "GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_API_KEY",
    "LLM_PROVIDER", "LLM_MODEL",
    "SLACK_WEBHOOK_URL", "SLACK_WEBHOOK", "SLACK_BOT_TOKEN",
    "SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET",
    "NOTION_TOKEN", "NOTION_DATABASE_ID", "NOTION_CLIENT_ID", "NOTION_CLIENT_SECRET",
    "HUBSPOT_TOKEN", "HUBSPOT_CLIENT_ID", "HUBSPOT_CLIENT_SECRET",
)
for _name in _SECRET_ENV:
    os.environ.pop(_name, None)

_TMP_DIR = tempfile.mkdtemp(prefix="callcoach-tests-")
TEST_DB = os.path.join(_TMP_DIR, "callcoach-test.db")
shutil.copyfile(SEED_DB, TEST_DB)
os.environ["DB_PATH"] = TEST_DB
os.environ.setdefault("FLASK_SECRET_KEY", "pytest-only-secret")


class NetworkBlocked(RuntimeError):
    """Raised when a test tries to leave the machine."""


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any outbound HTTP or socket connection made during a test."""
    import requests

    def _blocked(*args, **kwargs):
        raise NetworkBlocked(f"network access attempted in an offline test: {args[:3]}")

    monkeypatch.setattr(requests.sessions.Session, "request", _blocked)
    monkeypatch.setattr(requests, "get", _blocked)
    monkeypatch.setattr(requests, "post", _blocked)
    monkeypatch.setattr(requests, "put", _blocked)
    monkeypatch.setattr(requests, "patch", _blocked)
    monkeypatch.setattr(requests, "delete", _blocked)
    monkeypatch.setattr(requests, "request", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    yield


@pytest.fixture(scope="session")
def project_dir():
    return PROJECT_DIR


@pytest.fixture(scope="session")
def test_db_path():
    """Path of the per-session copy of the seed database (what app.py uses)."""
    return TEST_DB


@pytest.fixture
def fresh_db(tmp_path):
    """An empty, initialised database private to one test."""
    from src.database import store

    path = str(tmp_path / "fresh.db")
    store.init_db(path)
    return path


@pytest.fixture
def sample_transcript():
    with open(os.path.join(PROJECT_DIR, "src", "sample_transcript.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def seed_rows():
    """Every evaluation row of the shipped seed DB, parsed (read-only)."""
    import sqlite3

    conn = sqlite3.connect(f"file:{SEED_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM evaluations ORDER BY created_at ASC")]
    conn.close()
    for row in rows:
        row["transcript"] = json.loads(row["transcript"])
        row["evaluation"] = json.loads(row["evaluation"])
    return rows


@pytest.fixture(scope="session")
def flask_app():
    """The real Flask app, bound to the temp copy of the seed DB."""
    import app as app_module

    app_module.app.config["TESTING"] = True
    return app_module


@pytest.fixture
def client(flask_app):
    return flask_app.app.test_client()
