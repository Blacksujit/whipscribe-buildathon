"""SQLite persistence for meeting evaluations.

Stores per-meeting evaluation results so the Trend Analysis Engine
can analyze quality across multiple meetings over time.
"""

import json
import os
import sqlite3
from datetime import datetime


DB_PATH = os.environ.get("DB_PATH", "evaluations.db")


def init_db(db_path=None):
    """Create tables if they don't exist."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            job_id TEXT PRIMARY KEY,
            meeting_name TEXT,
            created_at TEXT,
            overall_score INTEGER,
            action_items INTEGER,
            clarity INTEGER,
            tension INTEGER,
            compliance INTEGER,
            transcript_json TEXT,
            evaluation_json TEXT,
            segment_count INTEGER,
            word_count INTEGER,
            language TEXT
        )
    """
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def save_evaluation(job_id, transcript, evaluation, meeting_name=None, db_path=None):
    """Store an evaluation result for later trend analysis."""
    path = db_path or DB_PATH
    init_db(path)
    conn = sqlite3.connect(path)

    scores = evaluation.get("category_scores", {})
    now = datetime.now().isoformat()

    conn.execute(
        """
        INSERT OR REPLACE INTO evaluations
            (job_id, meeting_name, created_at, overall_score,
             action_items, clarity, tension, compliance,
             transcript_json, evaluation_json, segment_count, word_count, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            meeting_name or job_id[:8],
            now,
            evaluation.get("overall_score", 0),
            scores.get("action_items", 0),
            scores.get("clarity", 0),
            scores.get("tension", 0),
            scores.get("compliance", 0),
            json.dumps(transcript),
            json.dumps(evaluation),
            len(transcript.get("segments", [])),
            transcript.get("word_count", 0),
            transcript.get("language", "unknown"),
        ),
    )
    conn.commit()
    conn.close()


def get_all_evaluations(db_path=None):
    """Return all stored evaluations, newest first."""
    path = db_path or DB_PATH
    init_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT job_id, meeting_name, created_at, overall_score,
               action_items, clarity, tension, compliance,
               segment_count, word_count, language
        FROM evaluations
        ORDER BY created_at DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_evaluation(job_id, db_path=None):
    """Return a single stored evaluation with full data."""
    path = db_path or DB_PATH
    init_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT * FROM evaluations WHERE job_id = ?",
        (job_id,),
    ).fetchone()

    if row is None:
        conn.close()
        return None

    result = dict(row)
    result["transcript"] = json.loads(result.pop("transcript_json"))
    result["evaluation"] = json.loads(result.pop("evaluation_json"))
    conn.close()
    return result


def get_evaluation_dicts_for_comparison(db_path=None):
    """Return evaluation dicts in the format compare.py expects.

    Used by the trend analysis engine to run compare_evaluations().
    """
    rows = get_all_evaluations(db_path)
    evals = []
    names = []
    for row in rows:
        # Reconstruct the evaluation dict format
        evaluation = {
            "overall_score": row["overall_score"],
            "category_scores": {
                "action_items": row["action_items"],
                "clarity": row["clarity"],
                "tension": row["tension"],
                "compliance": row["compliance"],
            },
            "action_items": [],
            "clarity_issues": [],
            "tension_signals": [],
            "compliance_risks": [],
        }
        evals.append(evaluation)
        names.append(row["meeting_name"] or row["job_id"][:8])
    return evals, names


def save_setting(key, value, db_path=None):
    """Store a setting (e.g. API key)."""
    path = db_path or DB_PATH
    init_db(path)
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_setting(key, db_path=None):
    """Retrieve a setting."""
    path = db_path or DB_PATH
    init_db(path)
    conn = sqlite3.connect(path)
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row[0] if row else None
