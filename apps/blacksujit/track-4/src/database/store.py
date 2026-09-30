"""SQLite persistence for meeting evaluations.

Stores per-meeting evaluation results and tracks action item lifecycles.
"""

import json
import os
import sqlite3
from datetime import datetime

# Keep the database next to the project root so gunicorn, the CLI and the
# MCP server all agree on the location regardless of the process cwd.
_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "evaluations.db",
)
DB_PATH = os.environ.get("DB_PATH") or _DEFAULT_DB_PATH


def _connect(path=None):
    """Open a SQLite connection with sane concurrency settings."""
    conn = sqlite3.connect(path or DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(db_path=None):
    """Create tables if they don't exist (idempotent)."""
    conn = _connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        job_id TEXT PRIMARY KEY,
        transcript TEXT,
        evaluation TEXT,
        meeting_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS action_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        text TEXT,
        owner TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    # One row per (job, item) so re-analyzing a recording does not duplicate items.
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_action_items_job_text "
        "ON action_items (job_id, text)"
    )
    conn.commit()
    conn.close()


def seed_if_missing(db_path=None):
    """Restore the shipped seed DB when the working DB has no evaluations.

    Deployed containers start with an empty SQLite file (the DB is excluded from
    the image), so a fresh container restores the real evaluation snapshot that
    ships with the repo. Runtime writes then accumulate on top of it.
    """
    target = db_path or DB_PATH
    try:
        conn = _connect(target)
        count = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
        conn.close()
    except Exception:
        count = 0
    if count:
        return count

    seed = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "seed_evaluations.db",
    )
    if not os.path.exists(seed):
        return 0
    try:
        import shutil

        shutil.copyfile(seed, target)
        conn = _connect(target)
        count = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def save_evaluation(job_id, transcript, evaluation, meeting_name=None, db_path=None):
    """Store an evaluation result and track action items."""
    conn = _connect(db_path)

    # Extract the inner evaluation object if wrapped
    eval_data = evaluation.get("evaluation", evaluation) if isinstance(evaluation, dict) else evaluation

    conn.execute(
        "INSERT OR REPLACE INTO evaluations (job_id, transcript, evaluation, meeting_name) VALUES (?, ?, ?, ?)",
        (job_id, json.dumps(transcript), json.dumps(eval_data), meeting_name)
    )

    cursor = conn.cursor()
    for item in eval_data.get("action_items", []):
        cursor.execute(
            "INSERT OR IGNORE INTO action_items (job_id, text, owner) VALUES (?, ?, ?)",
            (job_id, item.get("text", ""), item.get("owner", "unspecified"))
        )

    conn.commit()
    conn.close()


def get_all_evaluations(db_path=None):
    """Return all stored evaluations, newest first."""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM evaluations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_evaluation(job_id, db_path=None):
    """Return a single stored evaluation."""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM evaluations WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r["transcript"] = json.loads(r["transcript"])
        r["evaluation"] = json.loads(r["evaluation"])
        return r
    return None


def get_evaluation_dicts_for_comparison(db_path=None):
    """Return evaluation dicts in the format compare.py expects."""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM evaluations ORDER BY created_at ASC").fetchall()
    conn.close()

    evals = []
    names = []
    for r in rows:
        eval_data = json.loads(r["evaluation"])
        evals.append(eval_data)
        names.append(r["meeting_name"] or r["job_id"])

    return evals, names


def get_unresolved_action_items(db_path=None):
    """Fetch all pending action items from previous meetings."""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT text, owner FROM action_items WHERE status = 'PENDING'").fetchall()
    conn.close()
    return [{"text": r["text"], "owner": r["owner"]} for r in rows]


def resolve_action_item(text, job_id=None, db_path=None):
    """Mark a pending action item as resolved based on its text."""
    conn = _connect(db_path)
    if job_id:
        conn.execute(
            "UPDATE action_items SET status = 'RESOLVED', resolved_at = ? "
            "WHERE text = ? AND job_id = ? AND status = 'PENDING'",
            (datetime.now().isoformat(), text, job_id)
        )
    else:
        conn.execute(
            "UPDATE action_items SET status = 'RESOLVED', resolved_at = ? "
            "WHERE text = ? AND status = 'PENDING'",
            (datetime.now().isoformat(), text)
        )
    conn.commit()
    conn.close()


def save_setting(key, value, db_path=None):
    conn = _connect(db_path)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_setting(key, db_path=None):
    conn = _connect(db_path)
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None
