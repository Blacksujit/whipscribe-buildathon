"""Complete test suite for all CallCoach-AI features.

Tests all major features:
1. Real-time coaching during calls
2. Post-call analysis with 4-agent scoring
3. Cross-call intelligence and trend analysis
4. CRM integration
5. Automated follow-up emails
6. Team performance benchmarking
7. Custom scoring rubrics
8. Sentiment analysis over time
9. Automated coaching plans
10. Multi-language support
11. AI coaching assistant
12. Export functionality
13. MCP integration

Usage:
    python test_complete.py
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
from src.core.sentiment import SentimentTracker
from src.core.coaching_plan import CoachingPlanGenerator
from src.core.multilang import MultiLanguageSupport
from src.core.assistant import CoachingAssistant
from src.core.export import ExportManager
from src.realtime.analyzer import RealtimeAnalyzer
from src.api.crm import create_crm_integration, sync_call_to_crm
from src.api.followup import FollowUpEmailGenerator
from src.api.mcp_integration import WhipScribeMCPIntegration


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

    category_scores = {"compliance": 80, "tension": 70, "clarity": 90, "action_items": 60}
    score = manager.apply_rubric("Test Rubric", category_scores)
    results.assert_true(score > 0, "Rubric score calculated")


def test_sentiment_analysis(results):
    """Test: Sentiment analysis over time."""
    print("\n  [Test] Sentiment Analysis")

    tracker = SentimentTracker()

    calls = [
        ("Q4 Planning", [
            {"text": "I think we should launch in November.", "speaker": "Sarah", "start": 0},
            {"text": "The engineering team isn't ready yet.", "speaker": "Priya", "start": 5},
        ]),
        ("Retro", [
            {"text": "I'm frustrated that we missed the deadline.", "speaker": "Sarah", "start": 0},
            {"text": "The timeline was unrealistic.", "speaker": "Mike", "start": 5},
        ]),
    ]

    for call_name, segments in calls:
        tracker.add_call(call_name, segments)

    trend = tracker.get_sentiment_trend()
    results.assert_true("trend" in trend, "Trend exists")
    results.assert_true("calls" in trend, "Calls exist")

    speaker_sentiments = tracker.get_sentiment_by_speaker()
    results.assert_true(isinstance(speaker_sentiments, dict), "Speaker sentiments is a dict")


def test_coaching_plans(results):
    """Test: Automated coaching plans."""
    print("\n  [Test] Coaching Plans")

    generator = CoachingPlanGenerator()

    base_transcript = load_sample_transcript()
    evaluations = []
    for name in ["Q4 Planning", "Retro", "Sales Call"]:
        t = make_sample_variation(base_transcript, name)
        e = evaluate(t)
        evaluations.append(e)

    plan = generator.generate_plan("Sarah", evaluations)

    results.assert_true("rep_name" in plan, "Plan has rep name")
    results.assert_true("average_scores" in plan, "Plan has average scores")
    results.assert_true("weaknesses" in plan, "Plan has weaknesses")
    results.assert_true("action_items" in plan, "Plan has action items")
    results.assert_true("goals" in plan, "Plan has goals")


def test_multilang(results):
    """Test: Multi-language support."""
    print("\n  [Test] Multi-Language Support")

    multilang = MultiLanguageSupport(target_language="en")

    results.assert_true(len(multilang.get_supported_languages()) > 0, "Supported languages exist")

    transcript = load_sample_transcript()
    result = multilang.analyze_multilang(transcript, source_language="en")

    results.assert_true("source_language" in result, "Source language exists")
    results.assert_true("target_language" in result, "Target language exists")
    results.assert_true("coaching_prompts" in result, "Coaching prompts exist")


def test_assistant(results):
    """Test: AI coaching assistant."""
    print("\n  [Test] AI Coaching Assistant")

    assistant = CoachingAssistant()

    transcript = load_sample_transcript()
    evaluation = evaluate(transcript)
    assistant.set_context(evaluation, transcript)

    answer = assistant.ask("How did I do on my last call?")
    results.assert_true("answer" in answer, "Answer exists")
    results.assert_true("type" in answer, "Type exists")

    answer = assistant.ask("What should I improve?")
    results.assert_true("answer" in answer, "Improvement answer exists")


def test_export(results):
    """Test: Export functionality."""
    print("\n  [Test] Export Functionality")

    transcript = load_sample_transcript()
    evaluation = evaluate(transcript)

    exporter = ExportManager(evaluation, transcript)

    markdown = exporter.export_markdown()
    results.assert_true(isinstance(markdown, str), "Markdown export is a string")
    results.assert_true(len(markdown) > 0, "Markdown export is not empty")

    json_export = exporter.export_json()
    results.assert_true(isinstance(json_export, str), "JSON export is a string")

    slack = exporter.export_slack()
    results.assert_true("blocks" in slack, "Slack export has blocks")

    notion = exporter.export_notion()
    results.assert_true("properties" in notion, "Notion export has properties")


def test_mcp_integration(results):
    """Test: MCP integration."""
    print("\n  [Test] MCP Integration")

    mcp = WhipScribeMCPIntegration(api_key="mock_key")

    recordings = mcp.list_recordings(limit=5)
    results.assert_true(isinstance(recordings, list), "Recordings is a list")

    folders = mcp.list_folders()
    results.assert_true(isinstance(folders, list), "Folders is a list")

    details = mcp.get_recording_details("rec_1")
    results.assert_true("name" in details, "Details has name")


def test_dynamics_and_commitments(results):
    """Test: conversation dynamics, commitment ledger, rubric math."""
    print("\n  [Test] Dynamics, Ledger, Rubrics")

    from src.core.dynamics import analyze_dynamics, dynamics_line
    from src.core.commitments import build_ledger
    from src.core.rubric import ScoringRubric

    transcript = load_sample_transcript()
    dynamics = analyze_dynamics(transcript)

    results.assert_true("speakers" in dynamics, "Dynamics produce speakers")
    results.assert_true(dynamics.get("turns", 0) >= 2, "Dynamics count turns")
    line = dynamics_line(dynamics)
    results.assert_true(line.startswith("Talk balance") or line == "", "Dynamics line renders")

    rows = [
        {"job_id": "call-1", "text": "Follow up with the team by Friday", "owner": "you", "status": "PENDING", "resolved_at": None},
        {"job_id": "call-2", "text": "Follow up with the team by Friday!", "owner": "you", "status": "PENDING", "resolved_at": None},
        {"job_id": "call-2", "text": "Send the pricing deck", "owner": "you", "status": "RESOLVED", "resolved_at": "2026-09-30T10:00:00"},
    ]
    evaluations = [
        {"job_id": "call-1", "meeting_name": "First call", "created_at": "2026-09-28 10:00:00"},
        {"job_id": "call-2", "meeting_name": "Second call", "created_at": "2026-09-30 10:00:00"},
    ]
    ledger = build_ledger(rows, evaluations)
    results.assert_true(ledger["open_count"] == 1, "Ledger groups repeated commitments")
    results.assert_true(ledger["repeated_count"] == 1, "Ledger flags repeats across calls")
    results.assert_true(ledger["resolved_count"] == 1, "Ledger tracks resolved items")

    rubric = ScoringRubric("Compliance heavy", {"compliance": 0.5, "tension": 0.15, "clarity": 0.15, "action_items": 0.2})
    score = rubric.calculate_score({"compliance": 100, "tension": 0, "clarity": 0, "action_items": 0})
    results.assert_true(abs(score - 50.0) < 0.01, "Rubric applies weights to real scores")


def main():
    print("=" * 60)
    print("  CallCoach-AI — Complete Test Suite")
    print("=" * 60)

    results = TestResults()

    test_realtime_coaching(results)
    test_post_call_analysis(results)
    test_cross_call_intelligence(results)
    test_crm_integration(results)
    test_followup_emails(results)
    test_team_benchmarking(results)
    test_custom_rubrics(results)
    test_sentiment_analysis(results)
    test_coaching_plans(results)
    test_multilang(results)
    test_assistant(results)
    test_export(results)
    test_mcp_integration(results)
    test_dynamics_and_commitments(results)

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
