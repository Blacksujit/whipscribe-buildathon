"""Comprehensive test suite for CallCoach-AI.

Tests all major features:
1. Single call analysis
2. Cross-call intelligence
3. Coaching recommendations
4. API integration
5. MCP server integration
6. Slack/Notion delivery

Usage:
    python test_comprehensive.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import load_sample_transcript, make_sample_variation
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.core.coach import generate_coaching_recommendations, format_recommendations
from src.reporter import generate_report


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

    def assert_equal(self, actual, expected, message):
        if actual == expected:
            self.passed += 1
            print(f"    [PASS] {message}")
        else:
            self.failed += 1
            self.errors.append(f"{message} (expected {expected}, got {actual})")
            print(f"    [FAIL] {message} (expected {expected}, got {actual})")

    def summary(self):
        print(f"\n  Results: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print(f"  Errors:")
            for error in self.errors:
                print(f"    - {error}")
        return self.failed == 0


def test_single_call_analysis(results):
    """Test: Single call analysis with 4-agent evaluation."""
    print("\n  [Test] Single Call Analysis")

    transcript = load_sample_transcript()
    result = evaluate(transcript)

    # Handle both wrapped and unwrapped evaluation results
    if isinstance(result, dict) and "evaluation" in result:
        evaluation = result["evaluation"]
    else:
        evaluation = result

    results.assert_true(isinstance(evaluation, dict), "Evaluation is a dict")
    results.assert_true(len(evaluation) > 0, "Evaluation is not empty")

    # Check for any score-related keys
    has_score = any(k in evaluation for k in ["overall_score", "score", "scores"])
    results.assert_true(has_score, "Evaluation has score data")

    # Check for any issue-related keys
    has_issues = any(k in evaluation for k in ["action_items", "issues", "findings"])
    results.assert_true(has_issues, "Evaluation has issue data")

    return evaluation


def test_cross_call_intelligence(results, evaluations, names):
    """Test: Cross-call trend analysis."""
    print("\n  [Test] Cross-Call Intelligence")

    comparisons = compare_evaluations(evaluations, names)

    results.assert_true("meetings" in comparisons, "Meetings exist")
    results.assert_true("trends" in comparisons, "Trends exist")
    results.assert_true("deal_velocity" in comparisons, "Deal velocity exists")
    results.assert_true("recurring_clusters" in comparisons, "Recurring clusters exist")
    results.assert_true("action_item_tracking" in comparisons, "Action item tracking exists")

    # Check trends
    trends = comparisons.get("trends", {})
    for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
        results.assert_true(metric in trends, f"Trend '{metric}' exists")

    # Check deal velocity
    velocity = comparisons.get("deal_velocity", {})
    results.assert_true("velocity" in velocity, "Velocity label exists")
    results.assert_true("score" in velocity, "Velocity score exists")

    # Check recurring clusters
    clusters = comparisons.get("recurring_clusters", [])
    results.assert_true(isinstance(clusters, list), "Recurring clusters is a list")

    # Check action item tracking
    tracking = comparisons.get("action_item_tracking", {})
    results.assert_true("total" in tracking, "Total action items exists")
    results.assert_true("completion_rate" in tracking, "Completion rate exists")

    return comparisons


def test_coaching_recommendations(results, comparisons):
    """Test: Coaching recommendations generation."""
    print("\n  [Test] Coaching Recommendations")

    recommendations = generate_coaching_recommendations(comparisons)

    results.assert_true(isinstance(recommendations, list), "Recommendations is a list")

    for rec in recommendations:
        results.assert_true("priority" in rec, "Recommendation has priority")
        results.assert_true("issue" in rec, "Recommendation has issue")
        results.assert_true("action" in rec, "Recommendation has action")
        results.assert_true("evidence" in rec, "Recommendation has evidence")

    # Test formatting
    formatted = format_recommendations(recommendations)
    results.assert_true(isinstance(formatted, str), "Formatted recommendations is a string")
    results.assert_true(len(formatted) > 0, "Formatted recommendations is not empty")

    return recommendations


def test_report_generation(results, evaluation, transcript):
    """Test: Report generation."""
    print("\n  [Test] Report Generation")

    report = generate_report(evaluation, transcript)

    results.assert_true(isinstance(report, str), "Report is a string")
    results.assert_true(len(report) > 0, "Report is not empty")
    results.assert_true("overall_score" in report or "Overall" in report, "Report contains score")

    return report


def test_mcp_server(results):
    """Test: MCP server tools."""
    print("\n  [Test] MCP Server")

    from src import mcp_server

    results.assert_true(hasattr(mcp_server, "MCPServer") or hasattr(mcp_server, "mcp"), "MCP server has entry point")
    results.assert_true(hasattr(mcp_server, "analyze_meeting"), "analyze_meeting tool exists")
    results.assert_true(hasattr(mcp_server, "get_deal_velocity"), "get_deal_velocity tool exists")
    results.assert_true(hasattr(mcp_server, "get_coaching_insights"), "get_coaching_insights tool exists")
    results.assert_true(hasattr(mcp_server, "export_meeting_report"), "export_meeting_report tool exists")


def test_api_integration(results):
    """Test: API integration functions."""
    print("\n  [Test] API Integration")

    from src.api import whip_api, slack, notion

    results.assert_true(hasattr(whip_api, "submit_file"), "submit_file exists")
    results.assert_true(hasattr(whip_api, "submit_url"), "submit_url exists")
    results.assert_true(hasattr(whip_api, "poll_job"), "poll_job exists")
    results.assert_true(hasattr(whip_api, "get_transcript"), "get_transcript exists")
    results.assert_true(hasattr(whip_api, "get_session_summary"), "get_session_summary exists")
    results.assert_true(hasattr(whip_api, "get_high_signal_moments"), "get_high_signal_moments exists")
    results.assert_true(hasattr(whip_api, "get_audio_url"), "get_audio_url exists")

    results.assert_true(hasattr(slack, "send_to_slack") or hasattr(slack, "send_slack_message"), "slack send function exists")
    results.assert_true(hasattr(notion, "deliver_report"), "deliver_report exists")


def main():
    print("=" * 60)
    print("  CallCoach-AI — Comprehensive Test Suite")
    print("=" * 60)

    results = TestResults()

    # Test 1: Single call analysis
    evaluation = test_single_call_analysis(results)

    # Test 2: Cross-call intelligence
    base_transcript = load_sample_transcript()
    names = ["Q4 Planning", "Retro", "Sales Call"]
    evaluations = []
    for name in names:
        t = make_sample_variation(base_transcript, name)
        e = evaluate(t)
        evaluations.append(e)

    comparisons = test_cross_call_intelligence(results, evaluations, names)

    # Test 3: Coaching recommendations
    recommendations = test_coaching_recommendations(results, comparisons)

    # Test 4: Report generation
    report = test_report_generation(results, evaluation, base_transcript)

    # Test 5: MCP server
    test_mcp_server(results)

    # Test 6: API integration
    test_api_integration(results)

    # Summary
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
