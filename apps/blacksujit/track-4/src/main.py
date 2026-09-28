"""Main entry point for Meeting Quality Assurance workflow.

Usage:
    python -m src.main --sample                           # Analyze one meeting (sample, no API key)
    python -m src.main --job-id <job_id>                  # Analyze an existing WhipScribe job
    python -m src.main --file <path> [--language en]       # Upload a file and analyze
    python -m src.main --url <url>  [--language en]       # Submit a URL and analyze
    python -m src.main --compare job1,job2,job3             # Compare multiple jobs (trend analysis)
    python -m src.main --compare-sample "Q4 Planning,Retro,Sales Call" # Compare sample meetings
"""

import argparse
import copy
import json
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.whip_api import submit_file, submit_url, poll_job, get_transcript
from src.core.evaluator import evaluate
from src.reporter import generate_report, save_report
from src.api.notion import deliver_report
from src.core.compare import compare_evaluations, generate_comparison_report, save_comparison_report


def load_env():
    """Load .env file if it exists."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def get_evaluation_settings(args):
    """Determine LLM provider, model, and API key from args or env."""
    provider = args.provider or os.getenv("LLM_PROVIDER")
    model = args.model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    else:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    return provider, api_key, model


def run_evaluation(transcript, provider, api_key, model, whip_key=None, job_id=None,
                    session_summary=None, key_moments=None, audio_url=None):
    """Run quality evaluation on a transcript, return evaluation dict."""
    if provider and api_key:
        result = evaluate(
            transcript, api_key=api_key, model=model, provider=provider,
            session_summary=session_summary, key_moments=key_moments, audio_url=audio_url
        )
        return result.get("evaluation", result), "LLM"
    else:
        evaluation = evaluate(transcript)
        return evaluation, "rule-based fallback"


def load_sample_transcript():
    """Load the sample transcript JSON from the src directory."""
    sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_transcript.json")
    with open(sample_path) as f:
        return json.load(f)


def make_sample_variation(base_transcript, name):
    """Create a slightly different sample transcript for comparison demos.

    Each variation has different quality characteristics so the
    comparison produces meaningful trends.
    """
    variation = copy.deepcopy(base_transcript)

    if "Retro" in name:
        # Retro meetings tend to have more tension and fewer action items
        for seg in variation.get("segments", []):
            text = seg.get("text", "")
            if "I think we should launch" in text:
                seg["text"] = text.replace(
                    "I think we should launch in November.",
                    "I am frustrated that we missed the October deadline again."
                )
            if "Let me circle back" in text:
                seg["text"] = "We will figure it out eventually"

    elif "Sales" in name:
        # Sales calls have compliance risks
        for seg in variation.get("segments", []):
            text = seg.get("text", "")
            if "Good morning" in text:
                seg["text"] = "Good morning! I am super excited about this partnership!"

    return variation


def main():
    parser = argparse.ArgumentParser(
        description="Meeting Quality Assurance via WhipScribe API"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", action="store_true", help="Run with sample transcript (no API key needed)")
    group.add_argument("--job-id", help="Analyze an existing WhipScribe job ID")
    group.add_argument("--file", help="Upload a local audio file and analyze")
    group.add_argument("--url", help="Submit a URL and analyze")
    group.add_argument("--compare", help="Comma-separated list of Job IDs to compare (multi-meeting trend analysis)")
    group.add_argument("--compare-sample", help="Comma-separated meeting names (multi-meeting analysis with sample data)")
    parser.add_argument("--language", default=None, help="ISO language code (e.g. en)")
    parser.add_argument("--output", default="report.md", help="Output report file")
    parser.add_argument("--provider", default=None, help="LLM provider (groq/openai/anthropic/ollama)")
    parser.add_argument("--model", default=None, help="LLM model to use")
    parser.add_argument("--deliver", default=None, choices=["notion"],
                        help="Deliver the report to Notion")

    args = parser.parse_args()
    load_env()

    whip_key = os.getenv("WHIPSKRIBE_API_KEY")
    provider, api_key, model = get_evaluation_settings(args)

    # --- Single meeting flow ---
    if not args.compare and not args.compare_sample:
        job_id = None
        session_summary = None
        key_moments = None
        audio_url = None
        if args.sample:
            transcript = load_sample_transcript()
            print("  Using sample transcript (LLM evaluation)")
        elif args.job_id:
            if not whip_key:
                print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env and add your key.")
                sys.exit(1)
            job_id = args.job_id
            print(f"  Polling job {job_id}...")
            poll_job(whip_key, job_id)
            transcript = get_transcript(whip_key, job_id)
            print(f"  Transcript fetched: {len(transcript.get('segments', []))} segments")
            # Fetch additional WhipScribe context for richer LLM evaluation
            from src.api.whip_api import get_session_summary, get_high_signal_moments, get_audio_url
            session_summary = get_session_summary(whip_key, job_id)
            key_moments = get_high_signal_moments(whip_key, job_id)
            try:
                audio_data = get_audio_url(whip_key, job_id)
                audio_url = audio_data.get("url")
            except Exception:
                pass
        elif args.file:
            if not whip_key:
                print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env and add your key.")
                sys.exit(1)
            print(f"  Uploading {args.file}...")
            job_id = submit_file(whip_key, args.file, args.language)
            print(f"  Job {job_id} submitted, polling...")
            poll_job(whip_key, job_id)
            transcript = get_transcript(whip_key, job_id)
            print(f"  Transcript fetched: {len(transcript.get('segments', []))} segments")
            from src.api.whip_api import get_session_summary, get_high_signal_moments, get_audio_url
            session_summary = get_session_summary(whip_key, job_id)
            key_moments = get_high_signal_moments(whip_key, job_id)
            try:
                audio_data = get_audio_url(whip_key, job_id)
                audio_url = audio_data.get("url")
            except Exception:
                pass
        elif args.url:
            if not whip_key:
                print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env and add your key.")
                sys.exit(1)
            print(f"  Submitting URL {args.url}...")
            job_id = submit_url(whip_key, args.url, args.language)
            print(f"  Job {job_id} submitted, polling...")
            poll_job(whip_key, job_id)
            transcript = get_transcript(whip_key, job_id)
            print(f"  Transcript fetched: {len(transcript.get('segments', []))} segments")
            from src.api.whip_api import get_session_summary, get_high_signal_moments, get_audio_url
            session_summary = get_session_summary(whip_key, job_id)
            key_moments = get_high_signal_moments(whip_key, job_id)
            try:
                audio_data = get_audio_url(whip_key, job_id)
                audio_url = audio_data.get("url")
            except Exception:
                pass

        evaluation, eval_mode = run_evaluation(
            transcript, provider, api_key, model,
            whip_key=whip_key, job_id=job_id,
            session_summary=session_summary,
            key_moments=key_moments, audio_url=audio_url
        )

        print(f"  Evaluation complete ({eval_mode})")

        print("  Generating report...")
        report = generate_report(evaluation, transcript, job_id)
        save_report(report, args.output)
        print(f"  Report saved to: {args.output}")
        print(f"  Overall score: {evaluation.get('overall_score', 0)}/100")

        if args.deliver == "notion":
            print("  Delivering report to Notion...")
            try:
                result = deliver_report(report, job_id, evaluation.get("category_scores", {}))
                print(f"  Notion page created: {result['page_url']}")
            except Exception as e:
                print(f"  [WARN] Notion delivery failed: {e}")

        print("\n" + "=" * 60 + "\n")
        print(report)

    # --- Multi-meeting comparison flow ---
    elif args.compare:
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set.")
            sys.exit(1)

        job_ids = [j.strip() for j in args.compare.split(",") if j.strip()]
        if len(job_ids) < 2:
            print("  [ERROR] Need at least 2 job IDs for comparison")
            sys.exit(1)

        names = [f"Job {j[:8]}" for j in job_ids]
        evaluations = []

        for i, jid in enumerate(job_ids):
            print(f"  [{i+1}/{len(job_ids)}] Processing {jid}...")
            poll_job(whip_key, jid)
            transcript = get_transcript(whip_key, jid)
            print(f"  Segments: {len(transcript.get('segments', []))}")
            evaluation, mode = run_evaluation(transcript, provider, api_key, model)
            print(f"  Score: {evaluation.get('overall_score', 0)}/100 ({mode})")
            evaluations.append(evaluation)

        print("  Running trend analysis...")
        comparisons = compare_evaluations(evaluations, names)
        report = generate_comparison_report(comparisons)
        save_comparison_report(report, args.output)
        print(f"  Comparison report saved to: {args.output}")
        print_comparison_summary(comparisons)
        print("\n" + "=" * 60 + "\n")
        print(report)

    elif args.compare_sample:
        names = [n.strip() for n in args.compare_sample.split(",") if n.strip()]
        if len(names) < 2:
            print("  [ERROR] Need at least 2 meeting names for comparison")
            sys.exit(1)

        base_transcript = load_sample_transcript()
        evaluations = []

        for i, name in enumerate(names):
            print(f"  [{i+1}/{len(names)}] Analyzing: {name}")
            transcript = make_sample_variation(base_transcript, name)
            evaluation, mode = run_evaluation(transcript, provider, api_key, model)
            print(f"  Score: {evaluation.get('overall_score', 0)}/100 ({mode})")
            evaluations.append(evaluation)

        print("  Running trend analysis...")
        comparisons = compare_evaluations(evaluations, names)
        report = generate_comparison_report(comparisons)
        save_comparison_report(report, args.output)
        print(f"  Comparison report saved to: {args.output}")
        print_comparison_summary(comparisons)
        print("\n" + "=" * 60 + "\n")
        print(report)


def print_comparison_summary(comparisons: dict):
    """Print a concise summary of the comparison results."""
    print("\n  --- Trend Summary ---")
    for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
        trend = comparisons["trends"].get(metric, "stable")
        scores = [m["scores"][metric] for m in comparisons["meetings"]]
        print(f"    {metric:>14}: {' -> '.join(str(s) for s in scores)} ({trend})")

    print(f"\n  --- Insights ---")
    for insight in comparisons["insights"]:
        print(f"    - {insight}")

    tracking = comparisons["action_item_tracking"]
    print(f"\n  Action items: {tracking['total']} total, "
          f"{tracking['completion_rate']}% completion rate")


if __name__ == "__main__":
    main()
