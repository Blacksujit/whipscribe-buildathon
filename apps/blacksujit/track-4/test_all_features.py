"""Comprehensive test suite for all CallCoach-AI features.

Tests all major features:
1. Real-time coaching during calls
2. Post-call analysis with 4-agent scoring
3. Cross-call intelligence and trend analysis
4. CRM integration
5. Automated follow-up emails
6. Team performance benchmarking
7. Custom scoring rubrics

Usage:
    python test_all_features.py
"""

import json
import os
import sys

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


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def assert_true(self, condition, message):
        if condition:
            self.passed += 1
            print(f"    [PASS] {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"    [FAIL] {message}")

    def summary(self):
        print(f"\n  Results: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print(f"  Errors:")
            for error in self.errors:
                print(f"    - {error}")
        return self.failed == 0


def test_realtime_coaching(results):
    """Test: Real-time coaching during calls."""
    print("\n  [Test] Real-Time Coaching")

    analyzer = RealtimeAnalyzer()

    # Add segments
    segments = [
        {"text": "I think we should launch in November.", "speaker": "Sarah", "start": 0, "end": 5},
        {"text": "We'll definitely deliver by Q1. I promise.", "speaker": "Mike", "start": 5, "end": 8},
        {"text": "Let me circle back with you by Friday.", "speaker": "Sarah", "start": 8, "end": 12},
    ]

    for segment in segments:
        result = analyzer.add_segment(segment)
        results.assert_true('analysis' in result, "Analysis result exists")
        results.assert_true('coaching_prompts' in result, "Coaching prompts exist")

    stats = analyzer.get_live_stats()
    results.assert_true(stats['segment_count'] == 3, "Segment count is correct")
    results.assert_true(stats['speaker_count'] == 2, "Speaker count is correct")
    results.assert_true(stats['coaching_prompts'] > 0, "Coaching prompts generated")


def test_post_call_analysis(results):
    """Test: Post-call analysis with 4-agent scoring."""
    print("\n  [Test] Post-Call Analysis")

    transcript = load_sample_transcript()
    result = evaluate(transcript)

    if isinstance(result, dict) and "evaluation" in result:
        evaluation = result["evaluation"]
    else:
        evaluation = result

    results.assert_true(isinstance(evaluation, dict), "Evaluation is a dict")
    results.assert_true(len(evaluation) > 0, "Evaluation is not empty")


def test_cross_call_intelligence(results):
    """Test: Cross-call intelligence and trend analysis."""
    print("\n  [Test] Cross-Call Intelligence")

    base_transcript = load_sample_transcript()
    names = ["Q4 Planning", "Retro", "Sales Call"]
    evaluations = []

    for name in names:
        t = make_sample_variation(base_transcript, name)
        e = evaluate(t)
        evaluations.append(e)

    comparisons = compare_evaluations(evaluations, names)

    results.assert_true("trends" in comparisons, "Trends exist")
    results.assert_true("deal_velocity" in comparisons, "Deal velocity exists")
    results.assert_true("recurring_clusters" in comparisons, "Recurring clusters exist")
    results.assert_true("action_item_tracking" in comparisons, "Action item tracking exists")


def test_crm_integration(results):
    """Test: CRM integration."""
    print("\n  [Test] CRM Integration")

    transcript = load_sample_transcript()
    evaluation = evaluate(transcript)

    crm = create_crm_integration("hubspot")
    sync_results = sync_call_to_crm(evaluation, transcript, crm)

    results.assert_true("tasks_created" in sync_results, "Tasks created key exists")
    results.assert_true("notes_created" in sync_results, "Notes created key exists")


def test_followup_emails(results):
    """Test: Automated follow-up emails."""
    print("\n  [Test] Follow-Up Emails")

    transcript = load_sample_transcript()
    evaluation = evaluate(transcript)

    generator = FollowUpEmailGenerator()
    email = generator.generate_followup_email(evaluation, transcript, "test@example.com")

    results.assert_true("to" in email, "Email has recipient")
    results.assert_true("subject" in email, "Email has subject")
    results.assert_true("body" in email, "Email has body")
    results.assert_true("metadata" in email, "Email has metadata")


def test_team_benchmarking(results):
    """Test: Team performance benchmarking."""
    print("\n  [Test] Team Benchmarking")

    benchmark = TeamBenchmark()

    base_transcript = load_sample_transcript()
    names = ["Q4 Planning", "Retro", "Sales Call"]

    for rep_name in ["Sarah", "Mike", "Priya"]:
        rep_evals = []
        for name in names:
            t = make_sample_variation(base_transcript, name)
            e = evaluate(t)
            rep_evals.append(e)
        benchmark.add_rep_data(rep_name, rep_evals)

    summary = benchmark.get_team_summary()

    results.assert_true("team_size" in summary, "Team size exists")
    results.assert_true("team_averages" in summary, "Team averages exist")
    results.assert_true("top_performers" in summary, "Top performers exist")
    results.assert_true("needs_coaching" in summary, "Needs coaching exists")


def test_custom_rubrics(results):
    """Test: Custom scoring rubrics."""
    print("\n  [Test] Custom Scoring Rubrics")

    manager = RubricManager()
    create_default_rubrics(manager)

    results.assert_true(len(manager.list_rubrics()) > 0, "Rubrics exist")

    # Create custom rubric
    custom = manager.create_rubric(
        name="Test Rubric",
        categories={
            "compliance": 0.25,
            "tension": 0.25,
            "clarity": 0.25,
            "action_items": 0.25
        }
    )

    results.assert_true(custom is not None, "Custom rubric created")
    results.assert_true(custom.validate(), "Custom rubric is valid")

    # Apply rubric
    category_scores = {"compliance": 80, "tension": 70, "clarity": 90, "action_items": 60}
    score = manager.apply_rubric("Test Rubric", category_scores)
    results.assert_true(score > 0, "Rubric score calculated")


def main():
    print("=" * 60)
    print("  CallCoach-AI — Comprehensive Feature Test Suite")
    print("=" * 60)

    results = TestResults()

    test_realtime_coaching(results)
    test_post_call_analysis(results)
    test_cross_call_intelligence(results)
    test_crm_integration(results)
    test_followup_emails(results)
    test_team_benchmarking(results)
    test_custom_rubrics(results)

    print("\n" + "=" * 60)
    success = results.summary()
    print("=" * 60)

    if success:
        print("\n  All tests passed!")
        return 0
    else:
        print(f"\n  {results.failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
