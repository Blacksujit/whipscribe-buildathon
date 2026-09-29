"""End-to-end check for the CallCoach-AI pipeline.

Usage:
  python e2e_test.py            # auto: real run if WHIPSKRIBE_API_KEY + audio fixture exist
  python e2e_test.py --offline  # force the sample-transcript rule-based path
  python e2e_test.py --real     # force the live WhipScribe + LLM path

Real mode:
  upload -> poll -> transcript -> multi-agent evaluation -> store -> trend analysis

Offline mode:
  sample transcript -> rule-based evaluation -> temp DB -> trend analysis

Exit code 0 = pass, 1 = fail.
"""

import argparse
import json
import os
import sys
import tempfile

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.api.whip_api import (  # noqa: E402
    submit_file, poll_job, get_transcript,
    get_session_summary, get_high_signal_moments, get_audio_url,
)
from src.core.evaluator import evaluate  # noqa: E402
from src.core.compare import compare_evaluations  # noqa: E402
from src.database.store import (  # noqa: E402
    init_db, save_evaluation, get_evaluation_dicts_for_comparison,
)

load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_sample():
    with open(os.path.join(PROJECT_DIR, "src", "sample_transcript.json"), encoding="utf-8") as f:
        return json.load(f)


def _evaluation_settings():
    provider = os.environ.get("LLM_PROVIDER", "groq")
    api_key = (
        os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    model = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
    return provider, api_key, model


def run_offline():
    """Rule-based path over the bundled sample transcript (no API key needed)."""
    print("[1/4] Loading sample transcript")
    transcript = _load_sample()

    print("[2/4] Running rule-based evaluation")
    result = evaluate(transcript)
    if not result.get("success"):
        print("[FAIL] Evaluation did not return a wrapped result")
        return False
    core = result["evaluation"]
    issue_count = (
        len(core["action_items"]) + len(core["clarity_issues"])
        + len(core["tension_signals"]) + len(core["compliance_risks"])
    )
    print(f"      overall_score={core['overall_score']} issues={issue_count}")

    print("[3/4] Storing in a temporary database")
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "e2e.db")
        init_db(db_path)
        save_evaluation("sample-e2e-job", transcript, result, "E2E Sample Call", db_path=db_path)

        print("[4/4] Running trend comparison")
        evals, names = get_evaluation_dicts_for_comparison(db_path=db_path)
        comparisons = compare_evaluations(evals, names)
        velocity = comparisons["deal_velocity"]
        print(f"      Deal Velocity: {velocity['velocity']} (score {velocity['score']})")

    print("[PASS] Offline pipeline works end to end")
    return True


def run_real():
    """Full pipeline against the live WhipScribe + LLM APIs."""
    whip_key = os.environ["WHIPSKRIBE_API_KEY"]
    provider, llm_api_key, llm_model = _evaluation_settings()
    test_file = os.path.join(PROJECT_DIR, "src", "test_speech.wav")

    print(f"[1/5] Uploading {test_file}")
    job_id = submit_file(whip_key, test_file)
    print(f"      job_id={job_id}")

    print("[2/5] Polling for completion")
    poll_job(whip_key, job_id)
    transcript = get_transcript(whip_key, job_id)
    print(f"      segments={len(transcript.get('segments', []))}")

    print("[3/5] Fetching WhipScribe context (summary, key moments, audio)")
    session_summary = get_session_summary(whip_key, job_id)
    key_moments = get_high_signal_moments(whip_key, job_id)
    audio_url = None
    try:
        audio_data = get_audio_url(whip_key, job_id)
        audio_url = audio_data.get("url")
    except Exception:
        pass

    print("[4/5] Running multi-agent evaluation")
    result = evaluate(
        transcript, llm_api_key, llm_model, provider,
        session_summary=session_summary, key_moments=key_moments, audio_url=audio_url,
    )
    if not result.get("success"):
        print("[FAIL] Evaluation failed")
        return False
    print(f"      overall_score={result['evaluation']['overall_score']}")

    print("[5/5] Storing and running trend comparison")
    init_db()
    save_evaluation(job_id, transcript, result, "E2E Test Call")
    evals, names = get_evaluation_dicts_for_comparison()
    if evals:
        comparisons = compare_evaluations(evals, names)
        print(f"      Deal Velocity: {comparisons['deal_velocity']['velocity']}")

    print("[PASS] Real pipeline works end to end")
    return True


def main():
    parser = argparse.ArgumentParser(description="CallCoach-AI end-to-end check")
    parser.add_argument("--offline", action="store_true", help="Force the offline sample-transcript path")
    parser.add_argument("--real", action="store_true", help="Force the live WhipScribe + LLM path")
    args = parser.parse_args()

    api_key = os.environ.get("WHIPSKRIBE_API_KEY")
    test_file = os.path.join(PROJECT_DIR, "src", "test_speech.wav")

    if args.real or (not args.offline and api_key and os.path.exists(test_file)):
        if not api_key:
            print("[FAIL] --real requires WHIPSKRIBE_API_KEY")
            sys.exit(1)
        ok = run_real()
    else:
        reason = "forced offline" if args.offline else (
            "no WHIPSKRIBE_API_KEY" if not api_key else "no src/test_speech.wav"
        )
        print(f"[INFO] Running offline mode ({reason})")
        ok = run_offline()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FAIL] E2E test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
