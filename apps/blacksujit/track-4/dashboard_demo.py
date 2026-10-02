"""Cross-call intelligence dashboard demo.

Shows the full cross-call intelligence workflow with real data:
- Trend analysis across multiple meetings
- Recurring issue clustering
- Action item lifecycle tracking
- Speaker-level risk scoring
- Deal velocity metrics
- Coaching recommendations

Usage:
    python dashboard_demo.py
"""

import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import load_sample_transcript, make_sample_variation, load_env, get_evaluation_settings
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.core.coach import generate_coaching_recommendations, format_recommendations


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_metric(name, value, trend=None):
    trend_str = f" ({trend})" if trend else ""
    print(f"  {name}: {value}{trend_str}")


def main():
    load_env()

    print_section("CallCoach-AI — Cross-Call Intelligence Dashboard")
    print("  Demo with sample data showing full workflow")

    # Load sample transcript
    base_transcript = load_sample_transcript()

    # Create variations for different meeting types
    meeting_names = ["Q4 Planning", "Retro", "Sales Call", "Team Standup", "Client Review"]
    evaluations = []

    print_section("STEP 1: Analyze Multiple Meetings")
    for i, name in enumerate(meeting_names, 1):
        print(f"  [{i}/{len(meeting_names)}] Analyzing: {name}")
        transcript = make_sample_variation(base_transcript, name)
        evaluation = evaluate(transcript)
        evaluations.append(evaluation)
        print(f"    Overall: {evaluation.get('overall_score', 0)}/100")

    # Run comparison
    print_section("STEP 2: Cross-Call Trend Analysis")
    comparisons = compare_evaluations(evaluations, meeting_names)

    # Show trends
    print("  Trends:")
    for metric, trend in comparisons["trends"].items():
        scores = [m["scores"][metric] for m in comparisons["meetings"]]
        print(f"    {metric}: {' -> '.join(str(s) for s in scores)} ({trend})")

    # Show deal velocity
    velocity = comparisons["deal_velocity"]
    print(f"\n  Deal Velocity: {velocity['velocity']} (Score: {velocity['score']})")
    print(f"    Commitment Rate: {velocity['metrics']['commitment_rate']}")
    print(f"    Clarity Slope: {velocity['metrics']['clarity_slope']}")
    print(f"    Tension Variance: {velocity['metrics']['tension_variance']}")

    # Show recurring issues
    print_section("STEP 3: Recurring Issue Clusters")
    if comparisons["recurring_clusters"]:
        for i, cluster in enumerate(comparisons["recurring_clusters"][:5], 1):
            print(f"  {i}. {cluster['pattern'][:60]}...")
            print(f"     Found in {cluster['count']} meetings: {', '.join(cluster['meetings'])}")
    else:
        print("  No recurring issues found.")

    # Show action item tracking
    print_section("STEP 4: Action Item Lifecycle")
    tracking = comparisons["action_item_tracking"]
    print(f"  Total Action Items: {tracking['total']}")
    print(f"  Resolved: {tracking['resolved']}")
    print(f"  Unresolved: {len(tracking['unresolved'])}")
    print(f"  Completion Rate: {tracking['completion_rate']}%")

    if tracking["unresolved"]:
        print(f"\n  Unresolved Items:")
        for item in tracking["unresolved"][:3]:
            print(f"    - {item['text'][:60]}... (from {item['from']})")

    # Show speaker analysis
    print_section("STEP 5: Speaker-Level Risk Scoring")
    speaker_stats = comparisons.get("speaker_analysis", {})
    if speaker_stats:
        for speaker, stats in speaker_stats.items():
            print(f"  {speaker}: {stats['count']} issues")
            print(f"    Types: {', '.join(stats['types'])}")
    else:
        print("  No speaker analysis available.")

    # Show coaching recommendations
    print_section("STEP 6: Coaching Recommendations")
    recommendations = generate_coaching_recommendations(comparisons)
    print(format_recommendations(recommendations))

    # Summary
    print_section("DASHBOARD SUMMARY")
    print(f"  Meetings Analyzed: {len(evaluations)}")
    print(f"  Overall Trend: {comparisons['trends'].get('overall', 'stable')}")
    print(f"  Deal Velocity: {velocity['velocity']}")
    print(f"  Recurring Issues: {len(comparisons['recurring_clusters'])}")
    print(f"  Action Items: {tracking['total']} ({tracking['completion_rate']}% complete)")
    print(f"  Recommendations: {len(recommendations)}")

    # Export data
    print_section("EXPORT")
    output = {
        "meetings": comparisons["meetings"],
        "trends": comparisons["trends"],
        "deal_velocity": velocity,
        "recurring_clusters": comparisons["recurring_clusters"],
        "action_item_tracking": tracking,
        "recommendations": recommendations
    }

    output_path = "dashboard_demo_output.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Data exported to: {output_path}")


if __name__ == "__main__":
    main()
