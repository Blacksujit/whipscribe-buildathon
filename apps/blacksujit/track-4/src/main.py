"""Main entry point for Meeting Quality Assurance workflow.

Usage:
    python -m src.main --sample                           # Run with sample transcript (no API key needed)
    python -m src.main --job-id <job_id>                   # Analyze an existing WhipScribe job
    python -m src.main --file <path> [--language en]       # Upload a file and analyze
    python -m src.main --url <url>  [--language en]       # Submit a URL and analyze
"""

import argparse
import json
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.whip_api import submit_file, submit_url, poll_job, get_transcript
from src.evaluator import evaluate
from src.reporter import generate_report, save_report
from src.notion import deliver_report


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


def main():
    parser = argparse.ArgumentParser(
        description="Meeting Quality Assurance via WhipScribe API"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", action="store_true", help="Run with sample transcript (no API key)")
    group.add_argument("--job-id", help="Analyze an existing WhipScribe job ID")
    group.add_argument("--file", help="Upload a local audio file and analyze")
    group.add_argument("--url", help="Submit a URL and analyze")
    parser.add_argument("--language", default=None, help="ISO language code (e.g. en)")
    parser.add_argument("--output", default="report.md", help="Output report file")
    parser.add_argument("--provider", default=None, help="LLM provider (openai/anthropic/ollama)")
    parser.add_argument("--model", default=None, help="LLM model to use")
    parser.add_argument("--deliver", default=None, choices=["notion"],
                        help="Deliver the report to Notion")

    args = parser.parse_args()
    load_env()

    # Determine LLM settings
    provider = args.provider or os.getenv("LLM_PROVIDER")
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    model = args.model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Get the transcript
    job_id = None
    if args.sample:
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_transcript.json")
        with open(sample_path) as f:
            transcript = json.load(f)
        print("  Using sample transcript")
    elif args.job_id:
        job_id = args.job_id
        whip_key = os.getenv("WHIPSKRIBE_API_KEY")
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env and add your key.")
            sys.exit(1)
        print(f"  Polling job {job_id}...")
        poll_job(whip_key, job_id)
        transcript = get_transcript(whip_key, job_id)
        print(f"  Transcript fetched: {len(transcript.get('segments', []))} segments")
    elif args.file:
        whip_key = os.getenv("WHIPSKRIBE_API_KEY")
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env and add your key.")
            sys.exit(1)
        print(f"  Uploading {args.file}...")
        job_id = submit_file(whip_key, args.file, args.language)
        print(f"  Job {job_id} submitted, polling...")
        poll_job(whip_key, job_id)
        transcript = get_transcript(whip_key, job_id)
        print(f"  Transcript fetched: {len(transcript.get('segments', []))} segments")
    elif args.url:
        whip_key = os.getenv("WHIPSKRIBE_API_KEY")
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env and add your key.")
            sys.exit(1)
        print(f"  Submitting URL {args.url}...")
        job_id = submit_url(whip_key, args.url, args.language)
        print(f"  Job {job_id} submitted, polling...")
        poll_job(whip_key, job_id)
        transcript = get_transcript(whip_key, job_id)
        print(f"  Transcript fetched: {len(transcript.get('segments', []))} segments")

    # Run evaluation
    print("  Running LLM quality evaluation...")
    if provider and api_key:
        evaluation = evaluate(transcript, api_key=api_key, model=model, provider=provider)
        print("  Evaluation complete (via LLM)")
    else:
        evaluation = evaluate(transcript)
        print("  Evaluation complete (rule-based fallback — set LLM_PROVIDER + key for full LLM analysis)")

    # Generate and save report
    print(f"  Generating report...")
    report = generate_report(evaluation, transcript, job_id)
    save_report(report, args.output)
    print(f"  Report saved to: {args.output}")
    print(f"  Overall score: {evaluation.get('overall_score', 0)}/100")

    # Optional: deliver to Notion
    if args.deliver == "notion":
        print("  Delivering report to Notion...")
        try:
            result = deliver_report(
                report, job_id, evaluation.get("category_scores", {}),
            )
            print(f"  Notion page created: {result['page_url']}")
        except Exception as e:
            print(f"  [WARN] Notion delivery failed: {e}")

    # Print the report to console
    print("\n" + "=" * 60 + "\n")
    print(report)


if __name__ == "__main__":
    main()
