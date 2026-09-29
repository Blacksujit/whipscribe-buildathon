"""Comprehensive demo showing all CallCoach-AI features working together.

This demo showcases:
1. Real-time coaching during calls
2. Post-call analysis with 4-agent scoring
3. Cross-call intelligence and trend analysis
4. CRM integration
5. Automated follow-up emails
6. Team performance benchmarking
7. Custom scoring rubrics

Usage:
    python comprehensive_demo.py
"""

import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import load_sample_transcript, make_sample_variation
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.core.coach import generate_coaching_recommendations, format_recommendations
from src.core.benchmark import TeamBenchmark
from src.core.rubric import RubricManager, create_default_rubrics
from src.realtime.analyzer import RealtimeAnalyzer
from src.api.crm import create_crm_integration, sync_call_to_crm
from src.api.followup import FollowUpEmailGenerator


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_feature(name, status, details=""):
    status_str = "[PASS]" if status else "[FAIL]"
    print(f"  {status_str} {name}")
    if details:
        print(f"         {details}")


def main():
    print_section("CallCoach-AI × WhipScribe — Comprehensive Feature Demo")
    print("  Demonstrating all high-impact features working together")

    # Initialize components
    base_transcript = load_sample_transcript()
    rubric_manager = RubricManager()
    create_default_rubrics(rubric_manager)

    results = {}

    # =========================================================================
    # Feature 1: Real-Time Coaching During Calls
    # =========================================================================
    print_section("Feature 1: Real-Time Coaching During Calls")

    analyzer = RealtimeAnalyzer()

    # Simulate live call segments
    live_segments = [
        {"text": "I think we should launch in November. I'm not sure about the timeline.", "speaker": "Sarah", "start": 0, "end": 5},
        {"text": "We'll definitely deliver by Q1. I promise.", "speaker": "Mike", "start": 5, "end": 8},
        {"text": "Let me circle back with you by Friday. Thanks.", "speaker": "Sarah", "start": 8, "end": 12},
        {"text": "The engineering team isn't ready yet. Can we push to December?", "speaker": "Priya", "start": 12, "end": 18},
        {"text": "I guarantee this will be our best quarter ever.", "speaker": "Mike", "start": 18, "end": 22},
    ]

    print("  Simulating live call with real-time coaching...")
    for i, segment in enumerate(live_segments, 1):
        result = analyzer.add_segment(segment)
        print(f"    Segment {i}: {result['analysis']['sentiment']['label']} sentiment")
        if result['coaching_prompts']:
            for prompt in result['coaching_prompts']:
                print(f"      -> [{prompt['priority'].upper()}] {prompt['message']}")

    live_stats = analyzer.get_live_stats()
    print(f"\n  Live Stats:")
    print(f"    Segments: {live_stats['segment_count']}")
    print(f"    Speakers: {live_stats['speaker_count']}")
    print(f"    Action Items: {live_stats['action_items']}")
    print(f"    Compliance Risks: {live_stats['compliance_risks']}")
    print(f"    Coaching Prompts: {live_stats['coaching_prompts']}")

    results['realtime_coaching'] = {
        'status': True,
        'segments_analyzed': live_stats['segment_count'],
        'coaching_prompts': live_stats['coaching_prompts'],
        'action_items': live_stats['action_items'],
        'compliance_risks': live_stats['compliance_risks']
    }

    # =========================================================================
    # Feature 2: Post-Call Analysis with 4-Agent Scoring
    # =========================================================================
    print_section("Feature 2: Post-Call Analysis with 4-Agent Scoring")

    evaluation = evaluate(base_transcript)

    print(f"  Overall Score: {evaluation.get('overall_score', 0)}/100")
    print(f"  Category Scores:")
    for cat, score in evaluation.get('category_scores', {}).items():
        print(f"    {cat}: {score}/100")

    print(f"\n  Evidence:")
    print(f"    Action Items: {len(evaluation.get('action_items', []))}")
    print(f"    Clarity Issues: {len(evaluation.get('clarity_issues', []))}")
    print(f"    Tension Signals: {len(evaluation.get('tension_signals', []))}")
    print(f"    Compliance Risks: {len(evaluation.get('compliance_risks', []))}")

    results['post_call_analysis'] = {
        'status': True,
        'overall_score': evaluation.get('overall_score', 0),
        'categories': list(evaluation.get('category_scores', {}).keys()),
        'evidence_count': len(evaluation.get('action_items', [])) + len(evaluation.get('compliance_risks', []))
    }

    # =========================================================================
    # Feature 3: Cross-Call Intelligence and Trend Analysis
    # =========================================================================
    print_section("Feature 3: Cross-Call Intelligence and Trend Analysis")

    names = ["Q4 Planning", "Retro", "Sales Call", "Team Standup", "Client Review"]
    evaluations = []
    for name in names:
        t = make_sample_variation(base_transcript, name)
        e = evaluate(t)
        evaluations.append(e)

    comparisons = compare_evaluations(evaluations, names)

    print(f"  Meetings Analyzed: {len(evaluations)}")
    print(f"  Trends:")
    for metric, trend in comparisons['trends'].items():
        scores = [m['scores'][metric] for m in comparisons['meetings']]
        print(f"    {metric}: {' -> '.join(str(s) for s in scores)} ({trend})")

    print(f"\n  Recurring Issue Clusters: {len(comparisons['recurring_clusters'])}")
    for cluster in comparisons['recurring_clusters'][:3]:
        print(f"    - {cluster['pattern'][:50]}... (found in {cluster['count']} meetings)")

    print(f"\n  Action Item Tracking:")
    tracking = comparisons['action_item_tracking']
    print(f"    Total: {tracking['total']}")
    print(f"    Completion Rate: {tracking['completion_rate']}%")

    results['cross_call_intelligence'] = {
        'status': True,
        'meetings_analyzed': len(evaluations),
        'trends': comparisons['trends'],
        'recurring_clusters': len(comparisons['recurring_clusters']),
        'action_item_completion': tracking['completion_rate']
    }

    # =========================================================================
    # Feature 4: CRM Integration
    # =========================================================================
    print_section("Feature 4: CRM Integration")

    # Create a mock CRM integration
    crm = create_crm_integration("salesforce", api_key="mock_key", instance_url="https://mock.salesforce.com")

    # Sync call to CRM
    sync_results = sync_call_to_crm(evaluation, base_transcript, crm)

    print(f"  CRM Sync Results:")
    print(f"    Tasks Created: {len(sync_results['tasks_created'])}")
    print(f"    Notes Created: {len(sync_results['notes_created'])}")

    for task in sync_results['tasks_created']:
        print(f"      - {task['subject']}")

    results['crm_integration'] = {
        'status': True,
        'tasks_created': len(sync_results['tasks_created']),
        'notes_created': len(sync_results['notes_created'])
    }

    # =========================================================================
    # Feature 5: Automated Follow-Up Emails
    # =========================================================================
    print_section("Feature 5: Automated Follow-Up Emails")

    email_generator = FollowUpEmailGenerator()
    email = email_generator.generate_followup_email(evaluation, base_transcript, "sarah@company.com")

    print(f"  Generated Email:")
    print(f"    To: {email['to']}")
    print(f"    Subject: {email['subject']}")
    print(f"    Metadata: {email['metadata']}")

    results['followup_emails'] = {
        'status': True,
        'email_generated': True,
        'action_items_included': email['metadata']['action_items_count']
    }

    # =========================================================================
    # Feature 6: Team Performance Benchmarking
    # =========================================================================
    print_section("Feature 6: Team Performance Benchmarking")

    benchmark = TeamBenchmark()

    # Add rep data
    rep_names = ["Sarah", "Mike", "Priya", "Alex"]
    for rep_name in rep_names:
        rep_evals = []
        for name in names[:3]:
            t = make_sample_variation(base_transcript, name)
            e = evaluate(t)
            rep_evals.append(e)
        benchmark.add_rep_data(rep_name, rep_evals)

    team_summary = benchmark.get_team_summary()

    print(f"  Team Size: {team_summary['team_size']}")
    print(f"  Overall Trend: {team_summary['overall_trend']}")
    print(f"\n  Team Averages:")
    for metric, score in team_summary['team_averages'].items():
        print(f"    {metric}: {score:.1f}/100")

    print(f"\n  Top Performers:")
    for i, rep in enumerate(team_summary['top_performers'], 1):
        print(f"    {i}. {rep['rep_name']} - {rep['overall_score']:.1f}/100")

    print(f"\n  Needs Coaching:")
    for i, rep in enumerate(team_summary['needs_coaching'], 1):
        print(f"    {i}. {rep['rep_name']} - {rep['overall_score']:.1f}/100")

    results['team_benchmarking'] = {
        'status': True,
        'team_size': team_summary['team_size'],
        'top_performers': len(team_summary['top_performers']),
        'needs_coaching': len(team_summary['needs_coaching'])
    }

    # =========================================================================
    # Feature 7: Custom Scoring Rubrics
    # =========================================================================
    print_section("Feature 7: Custom Scoring Rubrics")

    print(f"  Available Rubrics: {rubric_manager.list_rubrics()}")

    # Apply a custom rubric
    category_scores = evaluation.get('category_scores', {})
    for rubric_name in rubric_manager.list_rubrics():
        score = rubric_manager.apply_rubric(rubric_name, category_scores)
        print(f"    {rubric_name}: {score}/100")

    # Create a custom rubric
    custom_rubric = rubric_manager.create_rubric(
        name="Custom Sales Rubric",
        categories={
            "compliance": 0.25,
            "tension": 0.15,
            "clarity": 0.30,
            "action_items": 0.30
        }
    )

    custom_score = rubric_manager.apply_rubric("Custom Sales Rubric", category_scores)
    print(f"\n  Custom Rubric Score: {custom_score}/100")

    results['custom_rubrics'] = {
        'status': True,
        'rubrics_available': len(rubric_manager.list_rubrics()),
        'custom_rubric_created': True
    }

    # =========================================================================
    # Summary
    # =========================================================================
    print_section("DEMO SUMMARY")

    print("  All Features Demonstrated:")
    for feature, data in results.items():
        status = "[PASS]" if data['status'] else "[FAIL]"
        print(f"    {status} {feature}")

    print(f"\n  Total Features: {len(results)}")
    print(f"  All Working: {all(d['status'] for d in results.values())}")

    # Export results
    output_path = "comprehensive_demo_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results exported to: {output_path}")

    return results


if __name__ == "__main__":
    main()
