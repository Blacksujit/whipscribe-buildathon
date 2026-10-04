"""Re-score the shipped seed calls with the current evaluator.

The seed DB was scored while src/core/evaluator.py read the wrong
category_scores keys (clarity/tension/compliance were always 50) and skipped
grounding for action items. This re-runs the four agents on the transcripts
already stored in seed_evaluations.db - LLM calls only, no WhipScribe
transcription - and writes the new evaluations back, keeping job_id,
meeting_name, created_at and any stored WhipScribe extras ("whip" block).

Usage:
    python scripts/rescore_seed.py                 # rescore seed_evaluations.db
    python scripts/rescore_seed.py --working-db    # also update the same rows in evaluations.db
    python scripts/rescore_seed.py --dry-run       # score and print, write nothing
    python scripts/rescore_seed.py --reground [--working-db]
                                                   # no LLM: re-run only the quote grounding

Needs LLM_PROVIDER + its key (e.g. GROQ_API_KEY) in the environment / .env.
A backup of the seed DB is written next to it before anything changes.
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from src.core.evaluator import evaluate, ground_items  # noqa: E402

SEED_DB = os.path.join(PROJECT_DIR, "seed_evaluations.db")
WORKING_DB = os.environ.get("DB_PATH") or os.path.join(PROJECT_DIR, "evaluations.db")


def llm_settings():
    provider = os.environ.get("LLM_PROVIDER")
    keys = {
        "groq": os.environ.get("GROQ_API_KEY"),
        "openai": os.environ.get("OPENAI_API_KEY"),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
    }
    api_key = keys.get(provider) or os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL")
    if provider == "groq" and not model:
        model = "openai/gpt-oss-120b"
    return provider, api_key, model


def cats(evaluation):
    c = (evaluation or {}).get("category_scores") or {}
    return {k: c.get(k) for k in ("action_items", "clarity", "tension", "compliance")}


def reground(include_working):
    """Re-apply ground_items() to every stored evidence list (deterministic, offline)."""
    targets = [SEED_DB] + ([WORKING_DB] if include_working and os.path.exists(WORKING_DB) else [])
    for path in targets:
        db = sqlite3.connect(path)
        rows = db.execute("SELECT job_id, transcript, evaluation FROM evaluations").fetchall()
        before = after = 0
        for job_id, transcript_raw, evaluation_raw in rows:
            segments = (json.loads(transcript_raw or "{}") or {}).get("segments", [])
            core = json.loads(evaluation_raw)
            inner = core.get("evaluation", core) if isinstance(core.get("evaluation"), dict) else core
            for key in ("compliance_risks", "tension_signals", "clarity_issues", "action_items"):
                items = inner.get(key)
                if isinstance(items, list):
                    before += sum(1 for i in items if isinstance(i, dict) and i.get("verified") is True)
                    inner[key] = ground_items(key, items, segments)
                    after += sum(1 for i in inner[key] if i.get("verified") is True)
            db.execute("UPDATE evaluations SET evaluation = ? WHERE job_id = ?", (json.dumps(core), job_id))
        db.commit()
        db.close()
        print(f"[OK] {os.path.basename(path)}: {len(rows)} rows re-grounded, verified quotes {before} -> {after}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-db", action="store_true", help="also update the same job rows in evaluations.db")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reground", action="store_true", help="re-ground stored quotes only (no LLM calls)")
    args = parser.parse_args()

    if args.reground:
        return reground(args.working_db)

    provider, api_key, model = llm_settings()
    if not provider or not api_key:
        print("[FAIL] No LLM_PROVIDER / key configured - rescoring needs the LLM agents.")
        return 1

    if not args.dry_run:
        backup = SEED_DB + f".bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copyfile(SEED_DB, backup)
        print(f"[OK] backup written: {os.path.basename(backup)}")

    conn = sqlite3.connect(SEED_DB)
    rows = conn.execute("SELECT job_id, transcript, evaluation, meeting_name FROM evaluations").fetchall()
    results = []
    for job_id, transcript_raw, evaluation_raw, name in rows:
        transcript = json.loads(transcript_raw)
        old = json.loads(evaluation_raw)
        old_core = old.get("evaluation", old) if isinstance(old, dict) else {}
        started = time.time()
        fresh = evaluate(transcript, api_key=api_key, model=model, provider=provider)
        core = fresh.get("evaluation", fresh)
        if (fresh.get("metadata") or {}).get("mode") == "rule-based":
            print(f"[SKIP] {name}: evaluator fell back to rule-based scoring")
            continue
        if isinstance(old_core.get("whip"), dict):
            core["whip"] = old_core["whip"]
        results.append((job_id, core))
        print(json.dumps({
            "job_id": job_id, "name": name, "seconds": round(time.time() - started, 1),
            "before": {"overall": old_core.get("overall_score"), **cats(old_core)},
            "after": {"overall": core.get("overall_score"), **cats(core)},
        }))
    conn.close()

    if args.dry_run:
        return 0
    targets = [SEED_DB] + ([WORKING_DB] if args.working_db and os.path.exists(WORKING_DB) else [])
    for path in targets:
        db = sqlite3.connect(path)
        for job_id, core in results:
            # UPDATE (not INSERT OR REPLACE) keeps created_at and the row order.
            db.execute("UPDATE evaluations SET evaluation = ? WHERE job_id = ?", (json.dumps(core), job_id))
        db.commit()
        db.close()
        print(f"[OK] updated {len(results)} rows in {os.path.basename(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
