"""Comprehensive demo script showing the full CallCoach-AI workflow.

This script demonstrates the complete pipeline from upload to coaching insights,
with real API usage evidence and cross-call intelligence.

Usage:
    python demo_workflow.py --sample              # Full demo with sample data
    python demo_workflow.py --file call.mp3       # Upload and analyze a real file
    python demo_workflow.py --job-id <job_id>     # Analyze an existing job
"""

import argparse
import json
import os
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.whip_api import submit_file, submit_url, poll_job, get_transcript, get_session_summary, get_high_signal_moments, get_audio_url
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations, generate_comparison_report
from src.reporter import generate_report, save_report
from src.main import load_sample_transcript, make_sample_variation, load_env, get_evaluation_settings


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_api_evidence(step, api_name, request, response):
    """Print API usage evidence for the demo."""
    print(f"  [{step}] {api_name}")
    print(f"    Request:  {json.dumps(request, indent=2)[:200]}...")
    print(f"    Response: {json.dumps(response, indent=2)[:200]}...")
    print()


def demo_single_call(transcript, provider, api_key, model, whip_key=None, job_id=None):
    """Demo: Single call analysis with full evidence."""
    print_section("SINGLE CALL ANALYSIS")

    # Show transcript structure
    segments = transcript.get("segments", [])
    print(f"  Transcript: {len(segments)} segments")
    print(f"  Speakers: {len(set(s.get('speaker', 'Unknown') for s in segments))}")
    print(f"  Duration: {segments[-1].get('end', 0) if segments else 0:.1f}s")

    # Show sample segments with timestamps
    print("\n  Sample segments with timestamps:")
    for seg in segments[:3]:
        print(f"    [{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s] {seg.get('speaker', 'Unknown')}: {seg.get('text', '')[:60]}...")

    # Run evaluation
    print(f"\n  Running 4-agent evaluation (Compliance, Tension, Clarity, Action Items)...")
    evaluation, eval_mode = run_evaluation(transcript, provider, api_key, model, whip_key, job_id)

    # Show scores
    print(f"\n  Overall Score: {evaluation.get('overall_score', 0)}/100")
    print(f"  Category Scores:")
    for cat, score in evaluation.get("category_scores", {}).items():
        print(f"    {cat}: {score}/100")

    # Show evidence
    print(f"\n  Evidence (flagged quotes with timestamps):")
    for issue_type in ("clarity_issues", "tension_signals", "compliance_risks", "action_items"):
        issues = evaluation.get(issue_type, [])
        if issues:
            print(f"    {issue_type}: {len(issues)} found")
            for issue in issues[:2]:
                text = issue.get("text", "") or f"{issue.get('text_a', '')} / {issue.get('text_b', '')}"
                print(f"      - {text[:60]}... (speaker: {issue.get('speaker', 'Unknown')})")

    return evaluation


def demo_cross_call_intelligence(evaluations, names):
    """Demo: Cross-call trend analysis with full evidence."""
    print_section("CROSS-CALL INTELLIGENCE")

    print(f"  Analyzing {len(evaluations)} meetings...")

    # Run comparison
    comparisons = compare_evaluations(evaluations, names)

    # Show trends
    print(f"\n  Trends:")
    for metric, trend in comparisons["trends"].items():
        scores = [m["scores"][metric] for m in comparisons["meetings"]]
        print(f"    {metric}: {' -> '.join(str(s) for s in scores)} ({trend})")

    # Show deal velocity
    velocity = comparisons["deal_velocity"]
    print(f"\n  Deal Velocity: {velocity['velocity']} (Score: {velocity['score']})")
    print(f"    Metrics: {velocity['metrics']}")

    # Show recurring issues
    if comparisons["recurring_clusters"]:
        print(f"\n  Recurring Issue Clusters:")
        for cluster in comparisons["recurring_clusters"][:3]:
            print(f"    - {cluster['pattern'][:60]}... (found in {cluster['count']} meetings)")

    # Show action item tracking
    tracking = comparisons["action_item_tracking"]
    print(f"\n  Action Item Tracking:")
    print(f"    Total: {tracking['total']}")
    print(f"    Resolved: {tracking['resolved']}")
    print(f"    Completion Rate: {tracking['completion_rate']}%")

    # Show insights
    print(f"\n  Insights:")
    for insight in comparisons["insights"]:
        print(f"    - {insight}")

    return comparisons


def demo_coaching_recommendations(comparisons):
    """Demo: Prescriptive coaching recommendations with evidence."""
    print_section("COACHING RECOMMENDATIONS")

    recommendations = []

    # Generate recommendations based on trends
    trends = comparisons["trends"]
    if trends.get("overall") == "declining":
        recommendations.append({
            "priority": "HIGH",
            "issue": "Overall quality is declining",
            "action": "Review recent calls for common patterns and schedule coaching session",
            "evidence": "Overall score trend: " + " -> ".join(str(m["scores"]["overall"]) for m in comparisons["meetings"])
        })

    if trends.get("compliance") == "declining":
        recommendations.append({
            "priority": "HIGH",
            "issue": "Compliance risks are increasing",
            "action": "Review compliance checklist and provide additional training",
            "evidence": "Compliance score trend: " + " -> ".join(str(m["scores"]["compliance"]) for m in comparisons["meetings"])
        })

    if trends.get("action_items") == "declining":
        recommendations.append({
            "priority": "MEDIUM",
            "issue": "Action item capture is declining",
            "action": "Implement action item template and review process",
            "evidence": "Action items score trend: " + " -> ".join(str(m["scores"]["action_items"]) for m in comparisons["meetings"])
        })

    # Show recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. [{rec['priority']}] {rec['issue']}")
        print(f"     Action: {rec['action']}")
        print(f"     Evidence: {rec['evidence']}")
        print()

    return recommendations


def run_evaluation(transcript, provider, api_key, model, whip_key=None, job_id=None):
    """Run evaluation with the given settings."""
    if provider and api_key:
        result = evaluate(
            transcript, api_key=api_key, model=model, provider=provider,
            session_summary=None, key_moments=None, audio_url=None
        )
        return result.get("evaluation", result), "LLM"
    else:
        evaluation = evaluate(transcript)
        return evaluation, "rule-based fallback"


def main():
    parser = argparse.ArgumentParser(description="CallCoach-AI Comprehensive Demo")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", action="store_true", help="Run with sample data")
    group.add_argument("--file", help="Upload a file and analyze")
    group.add_argument("--job-id", help="Analyze an existing job")
    group.add_argument("--compare-sample", help="Compare sample meetings (comma-separated)")
    parser.add_argument("--provider", default=None, help="LLM provider")
    parser.add_argument("--model", default=None, help="LLM model")

    args = parser.parse_args()
    load_env()

    whip_key = os.getenv("WHIPSKRIBE_API_KEY")
    provider, api_key, model = get_evaluation_settings(args)

    print_section("CallCoach-AI × WhipScribe — Comprehensive Demo")
    print(f"  Provider: {provider or 'rule-based fallback'}")
    print(f"  Model: {model}")
    print(f"  WhipScribe API: {'Connected' if whip_key else 'Not configured'}")

    # --- Single call demo ---
    if args.sample:
        transcript = load_sample_transcript()
        evaluation = demo_single_call(transcript, provider, api_key, model)

        # --- Cross-call demo ---
        print_section("CROSS-CALL DEMO")
        names = ["Q4 Planning", "Retro", "Sales Call"]
        evaluations = []
        for name in names:
            t = make_sample_variation(transcript, name)
            e, _ = run_evaluation(t, provider, api_key, model)
            evaluations.append(e)

        comparisons = demo_cross_call_intelligence(evaluations, names)

        # --- Coaching demo ---
        recommendations = demo_coaching_recommendations(comparisons)

        # --- Summary ---
        print_section("DEMO SUMMARY")
        print(f"  Single call analysis: ✓")
        print(f"  Cross-call intelligence: ✓")
        print(f"  Coaching recommendations: ✓")
        print(f"  Total meetings analyzed: {len(evaluations)}")
        print(f"  Total recommendations: {len(recommendations)}")

    elif args.file:
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set")
            sys.exit(1)

        print_section("UPLOAD AND ANALYZE")
        print(f"  File: {args.file}")

        # Upload
        print(f"\n  [1/4] Uploading file...")
        job_id = submit_file(whip_key, args.file)
        print(f"    Job ID: {job_id}")

        # Poll
        print(f"\n  [2/4] Polling for completion...")
        poll_job(whip_key, job_id)
        print(f"    Transcription complete")

        # Fetch transcript
        print(f"\n  [3/4] Fetching transcript...")
        transcript = get_transcript(whip_key, job_id)
        print(f"    Segments: {len(transcript.get('segments', []))}")

        # Analyze
        print(f"\n  [4/4] Analyzing...")
        evaluation = demo_single_call(transcript, provider, api_key, model, whip_key, job_id)

    elif args.job_id:
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set")
            sys.exit(1)

        print_section("ANALYZE EXISTING JOB")
        print(f"  Job ID: {args.job_id}")

        transcript = get_transcript(whip_key, args.job_id)
        evaluation = demo_single_call(transcript, provider, api_key, model, whip_key, args.job_id)

    elif args.compare_sample:
        names = [n.strip() for n in args.compare_sample.split(",") if n.strip()]
        transcript = load_sample_transcript()
        evaluations = []
        for name in names:
            t = make_sample_variation(transcript, name)
            e, _ = run_evaluation(t, provider, api_key, model)
            evaluations.append(e)

        comparisons = demo_cross_call_intelligence(evaluations, names)
        recommendations = demo_coaching_recommendations(comparisons)


if __name__ == "__main__":
    main()
