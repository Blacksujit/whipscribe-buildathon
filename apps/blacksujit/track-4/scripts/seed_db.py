"""Seed a real evaluations DB from WhipScribe jobs.

Every row is a real transcript + real LLM evaluation produced through the same
code path the app uses - no hand-written fixtures.

Usage:
    python scripts/seed_db.py                                  # curated list -> seed_evaluations.db
    python scripts/seed_db.py --out seed_evaluations.db
    python scripts/seed_db.py --jobs id1,id2 --out custom.db
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.whip_api import list_jobs, get_transcript
from src.core.evaluator import evaluate
from src.database import store


DEFAULT_JOB_IDS = [
    "7ebaeca0-9076-4c14-97be-a8b1948c8482",  # Q4 Rollout Plan Discussion, 38s
    "560ae0c0-5eba-43ed-8769-c5cd08fbf128",  # Q4 Rollout Plan Discussion, 38s
    "4bf909e2-d01c-482c-adec-4298a5f7736c",  # 10 AI Course Inquiry, 16s
    "e6e4487a-ec19-408f-a643-d54facb3edfe",  # Topic Research Process, 24s
    "bcfcea2d-b6d7-4cff-b75c-d5e3628ec5e7",  # Sample Call ENG MA, 13.6 min
    "cdb49994-9469-4fcc-b18b-ed1e946a3114",  # Introduction by Sujit Nirmal, 26s
    "def51fa6-e499-42d4-be2b-4cddbafdf992",  # Beruf und Zufriedenheit im Radio, 38s
    "8b9ec24c-f3c0-4a0a-a125-2b5f2ff2b26c",  # Sunjitha's 4000-Year Journey, 17s
]


def load_env():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(path):
        with open(path) as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="seed_evaluations.db")
    parser.add_argument("--jobs", default=None, help="comma-separated job ids")
    args = parser.parse_args()
    load_env()

    whip_key = os.environ.get("WHIPSKRIBE_API_KEY")
    provider = os.environ.get("LLM_PROVIDER", "groq")
    llm_key = (
        os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    model = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
    if not whip_key:
        print("[FAIL] WHIPSKRIBE_API_KEY missing")
        sys.exit(1)

    out = os.path.abspath(args.out)
    if os.path.exists(out):
        os.remove(out)
    store.init_db(out)

    names = {}
    try:
        listing = list_jobs(whip_key, limit=100)
        jobs = listing.get("jobs", []) if isinstance(listing, dict) else listing
        names = {j.get("job_id"): j.get("filename") for j in jobs or [] if isinstance(j, dict)}
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] could not list jobs for names: {exc}")

    ids = [j.strip() for j in (args.jobs.split(",") if args.jobs else DEFAULT_JOB_IDS) if j.strip()]
    ok = 0
    for job_id in ids:
        try:
            transcript = get_transcript(whip_key, job_id)
            segments = len(transcript.get("segments", []))
            if llm_key:
                result = evaluate(transcript, api_key=llm_key, model=model, provider=provider)
            else:
                result = evaluate(transcript)
            core = result.get("evaluation", result)
            name = names.get(job_id) or job_id[:8]
            store.save_evaluation(job_id, transcript, result, meeting_name=name, db_path=out)
            print(f"  {job_id[:8]}  segments={segments:<4} score={core.get('overall_score')}  {name}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {job_id[:8]}: {exc}")

    print(f"\nseeded {ok}/{len(ids)} evaluations -> {out}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
