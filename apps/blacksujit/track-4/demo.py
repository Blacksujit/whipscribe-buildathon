#!/usr/bin/env python3
"""
Demo Script - Meeting Quality Assurance Workflow

Shows the full flow: recording -> transcript -> LLM evaluation -> QA report.
This script is designed to be screen-recorded for a two-minute demo.

Usage:
    python demo.py --sample                           # Demo with sample transcript
    python demo.py --file path/to/audio.wav           # Upload and transcribe your recording
    python demo.py --job-id <whipscribe-job-id>       # Analyze an existing WhipScribe job
    python demo.py --deliver notion                    # Also push report to Notion
    python demo.py --compare-sample                    # Demo multi-meeting trend analysis

Requires: .env file with WHIPSKRIBE_API_KEY, LLM_API_KEY (see .env.template)
"""
import json
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.whip_api import submit_file, submit_url, poll_job, get_transcript, get_session_summary, get_high_signal
from src.evaluator import evaluate
from src.reporter import generate_report, save_report
from src.main import load_env
from src.compare import compare_evaluations, generate_comparison_report, make_sample_variation

DIVIDER = "=" * 64


def step(n, title):
    print(f"\n{DIVIDER}")
    print(f"  Step {n}: {title}")
    print(f"{DIVIDER}")


def load_sample_transcript():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "sample_transcript.json")
    with open(path) as f:
        return json.load(f)


def run_comparison_demo():
    """Demo multi-meeting trend analysis with 3 sample meetings."""
    print_banner("Multi-Meeting Trend Analysis Demo")
    print("  3 sample meetings compared for quality trends\n")

    names = ["Q4 Planning", "Retro: Sprint 12", "Sales Call #23"]
    base_transcript = load_sample_transcript()
    evaluations = []

    for i, name in enumerate(names):
        step(5 + i, f"Analyzing: {name}")
        transcript = make_sample_variation(base_transcript, name)
        evaluation = evaluate(transcript)  # rule-based fallback (no key needed)
        scores = evaluation.get("category_scores", {})
        print(f"  Overall: {evaluation.get('overall_score', 0)}/100")
        print(f"  Action Items: {scores.get('action_items', 0)}  "
              f"Clarity: {scores.get('clarity', 0)}  "
              f"Tension: {scores.get('tension', 0)}  "
              f"Compliance: {scores.get('compliance', 0)}")
        evaluations.append(evaluation)

    step(9, "Running trend analysis across meetings")
    comparisons = compare_evaluations(evaluations, names)

    print("\n  Score Trends:")
    for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
        trend = comparisons["trends"].get(metric, "stable")
        scores = [m["scores"][metric] for m in comparisons["meetings"]]
        arrow = {"improving": "+", "declining": "-", "stable": "="}.get(trend, "?")
        print(f"    {metric:>14}: {' -> '.join(str(s) for s in scores)} [{arrow} {trend}]")

    print("\n  Key Insights:")
    for insight in comparisons["insights"]:
        print(f"    * {insight}")

    tracking = comparisons["action_item_tracking"]
    print(f"\n  Action Items: {tracking['total']} total, "
          f"{tracking['completion_rate']}% resolved")

    report = generate_comparison_report(comparisons)
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparison_report.md")
    with open(output_path, "w") as f:
        f.write(report)
    print(f"\n  [OK] Comparison report saved to: {output_path}")

    print(f"\n{DIVIDER}")
    print("  Demo complete - multi-meeting trend analysis finished.")
    print(f"{DIVIDER}")


def print_banner(title):
    width = 70
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


if __name__ == "__main__":
    sample = "--sample" in sys.argv
    deliver = "--deliver" in sys.argv and sys.argv[sys.argv.index("--deliver") + 1] if "--deliver" in sys.argv else None
    file_path = next((a for a in sys.argv[1:] if not a.startswith("--") and not sample), None)
    compare_demo = "--compare-sample" in sys.argv

    load_env()

    if compare_demo:
        run_comparison_demo()
        sys.exit(0)

    step(1, "Acquire transcript from WhipScribe")

    job_id = None
    if sample:
        transcript = load_sample_transcript()
        print("  Mode: sample transcript (no API call needed for this demo)")
    else:
        whip_key = os.getenv("WHIPSKRIBE_API_KEY")
        if not whip_key:
            print("  [ERROR] WHIPSKRIBE_API_KEY not set. Copy .env.template to .env")
            sys.exit(1)
        if file_path and os.path.exists(file_path):
            print(f"  Mode: upload file")
            print(f"  Uploading {file_path}...")
            job_id = submit_file(whip_key, file_path)
            print(f"  Job submitted: {job_id}")
            print(f"  Polling until transcription is complete...")
            poll_job(whip_key, job_id)
            transcript = get_transcript(whip_key, job_id)
        else:
            print("  Usage: python demo.py --sample | --file <path> | --job-id <id>")
            sys.exit(1)

    seg_count = len(transcript.get("segments", []))
    wc = transcript.get("word_count", "?")
    print(f"  Transcript ready: {seg_count} segments, ~{wc} words, "
          f"language={transcript.get('language', '?')}")

    # Bonus: use WhipScribe's own highlight endpoints
    if job_id:
        print(f"\n  [bonus] Using WhipScribe high-signal moments:")
        for kind in ["question", "number"]:
            try:
                moments = get_high_signal(whip_key, job_id, kind=kind)
                print(f"    {kind}s found: {len(moments) if isinstance(moments, list) else 'n/a'}")
            except Exception:
                pass
    else:
        print(f"\n  [using sample data - real calls show questions/numbers via /clips/candidates]")

    step(2, "Run quality evaluation (action items, clarity, tension, compliance)")

    provider = os.getenv("LLM_PROVIDER")
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if provider and api_key:
        evaluation = evaluate(transcript, api_key=api_key, model=model, provider=provider)
        print(f"  Mode: LLM evaluation via {provider}/{model}")
    else:
        evaluation = evaluate(transcript)
        print(f"  Mode: rule-based fallback (set LLM_PROVIDER + LLM_API_KEY for LLM evaluation)")

    print(f"\n  Overall score: {evaluation['overall_score']}/100")
    for cat, score in evaluation["category_scores"].items():
        print(f"    {cat:15s}: {score}/100")

    # Show top issues
    issues = []
    for field in ("compliance_risks", "clarity_issues", "tension_signals"):
        for item in evaluation.get(field, []):
            issues.append((item["start"], field, item))
    issues.sort()
    if issues:
        print(f"\n  Top issues found:")
        for ts, field_name, item in issues[:4]:
            label = item.get("text") or item.get("text_a", item.get("text_b", ""))
            short = (label[:70] + "...") if len(label) > 70 else label[:70]
            print(f"    [{ts:5.1f}s] {field_name}: {short}")

    action_items = evaluation.get("action_items", [])
    if action_items:
        print(f"\n  Action items extracted ({len(action_items)}):")
        for item in action_items[:4]:
            print(f"    [{item['start']:5.1f}s] {item['text'][:70]}")

    step(3, "Generate QA report")

    report = generate_report(evaluation, transcript, job_id)
    output_file = "demo_report.md"
    save_report(report, output_file)
    print(f"  Report saved: {output_file} ({len(report)} bytes)")

    if deliver == "notion":
        from src.notion import deliver_report
        print("  Delivering to Notion...")
        try:
            result = deliver_report(report, job_id, evaluation.get("category_scores", {}))
            print(f"  Notion page: {result.get('page_url', result.get('id', 'unknown'))}")
        except Exception as e:
            print(f"  [WARN] Notion delivery failed: {e}")

    step(4, "Report preview")
    preview = report[:1200]
    print(textwrap.indent(preview, "  "))
    if len(report) > 1200:
        print(f"\n  ... ({len(report) - 1200} more characters in {output_file})")

    print(f"\n{DIVIDER}")
    print("  Demo complete! The workflow turned a recording into an actionable QA report.")
    print(f"{DIVIDER}")
