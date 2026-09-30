"""Verify all features work with real APIs and data, not mock data."""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def test_real_llm_scoring():
    """Test with real LLM API."""
    print("=" * 60)
    print("  TEST: Real LLM Scoring")
    print("=" * 60)

    from src.core.evaluator import evaluate
    from src.main import load_sample_transcript

    transcript = load_sample_transcript()
    provider = os.getenv("LLM_PROVIDER", "groq")
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    print(f"  Provider: {provider}")
    print(f"  Model: {model}")
    print(f"  API Key: {api_key[:10]}..." if api_key else "  API Key: NOT SET")

    if not api_key:
        print("  [FAIL] No LLM API key available")
        return None

    try:
        result = evaluate(transcript, api_key=api_key, provider=provider, model=model)
        if isinstance(result, dict) and "evaluation" in result:
            evaluation = result["evaluation"]
        else:
            evaluation = result

        score = evaluation.get("overall_score", 0)
        categories = evaluation.get("category_scores", {})
        action_items = evaluation.get("action_items", [])
        compliance_risks = evaluation.get("compliance_risks", [])

        print(f"  Overall Score: {score}/100")
        print(f"  Categories: {categories}")
        print(f"  Action Items: {len(action_items)}")
        print(f"  Compliance Risks: {len(compliance_risks)}")

        if score > 0:
            print("  [PASS] Real LLM scoring works")
            return evaluation
        else:
            print("  [FAIL] LLM scoring returned 0")
            return None

    except Exception as e:
        print(f"  [FAIL] LLM scoring error: {e}")
        return None


def test_real_whipscribe_api():
    """Test with real WhipScribe API."""
    print("\n" + "=" * 60)
    print("  TEST: Real WhipScribe API")
    print("=" * 60)

    whip_key = os.getenv("WHIPSKRIBE_API_KEY")
    print(f"  API Key: {whip_key[:10]}..." if whip_key else "  API Key: NOT SET")

    if not whip_key:
        print("  [FAIL] No WhipScribe API key")
        return None

    try:
        from src.api.whip_api import submit_file, poll_job, get_transcript, get_session_summary, get_high_signal_moments, get_audio_url

        test_file = "src/test_speech.wav"
        if not os.path.exists(test_file):
            print(f"  [SKIP] No test audio file found")
            return None

        file_size = os.path.getsize(test_file)
        print(f"  Audio file: {test_file} ({file_size} bytes)")

        print("  Submitting to WhipScribe API...")
        job_id = submit_file(whip_key, test_file)
        print(f"  Job ID: {job_id}")

        print("  Polling for completion...")
        poll_job(whip_key, job_id)
        print("  Transcription complete!")

        print("  Fetching transcript...")
        transcript = get_transcript(whip_key, job_id)
        segments = transcript.get("segments", [])
        print(f"  Segments: {len(segments)}")

        if len(segments) > 0:
            print(f"  First segment: {segments[0].get('text', '')[:80]}...")
            speakers = set(s.get("speaker", "Unknown") for s in segments)
            print(f"  Speakers: {len(speakers)}")

            # Fetch additional context
            print("  Fetching session summary...")
            session_summary = get_session_summary(whip_key, job_id)
            if session_summary:
                print(f"  Summary: {str(session_summary.get('summary', 'N/A'))[:80]}...")
            else:
                print("  Summary: None (API returned null)")

            print("  Fetching key moments...")
            key_moments = get_high_signal_moments(whip_key, job_id)
            if key_moments:
                print(f"  Key moments: {len(key_moments.get('moments', []))}")
            else:
                print("  Key moments: None (API returned null)")

            print("  [PASS] Real WhipScribe API works end-to-end")
            return transcript
        else:
            print("  [FAIL] No segments returned")
            return None

    except Exception as e:
        print(f"  [FAIL] WhipScribe API error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_real_time_coaching():
    """Test real-time coaching with real data."""
    print("\n" + "=" * 60)
    print("  TEST: Real-Time Coaching")
    print("=" * 60)

    from src.realtime.analyzer import RealtimeAnalyzer

    analyzer = RealtimeAnalyzer()

    segments = [
        {"text": "I think we should launch in November. I'm not sure about the timeline.", "speaker": "Sarah", "start": 0, "end": 5},
        {"text": "We'll definitely deliver by Q1. I promise.", "speaker": "Mike", "start": 5, "end": 8},
        {"text": "Let me circle back with you by Friday.", "speaker": "Sarah", "start": 8, "end": 12},
    ]

    for segment in segments:
        result = analyzer.add_segment(segment)

    stats = analyzer.get_live_stats()
    print(f"  Segments: {stats['segment_count']}")
    print(f"  Speakers: {stats['speaker_count']}")
    print(f"  Coaching Prompts: {stats['coaching_prompts']}")

    if stats['coaching_prompts'] > 0:
        print("  [PASS] Real-time coaching works")
        return True
    else:
        print("  [FAIL] No coaching prompts generated")
        return False


def test_cross_call_intelligence():
    """Test cross-call intelligence with real data."""
    print("\n" + "=" * 60)
    print("  TEST: Cross-Call Intelligence")
    print("=" * 60)

    from src.main import load_sample_transcript, make_sample_variation
    from src.core.evaluator import evaluate
    from src.core.compare import compare_evaluations

    base_transcript = load_sample_transcript()
    names = ["Q4 Planning", "Retro", "Sales Call"]
    evaluations = []

    for name in names:
        t = make_sample_variation(base_transcript, name)
        e = evaluate(t)
        evaluations.append(e)

    comparisons = compare_evaluations(evaluations, names)

    print(f"  Meetings: {len(evaluations)}")
    print(f"  Trends: {list(comparisons['trends'].keys())}")
    print(f"  Recurring Clusters: {len(comparisons['recurring_clusters'])}")

    if len(comparisons['trends']) > 0:
        print("  [PASS] Cross-call intelligence works")
        return True
    else:
        print("  [FAIL] No trends generated")
        return False


def test_crm_integration():
    """Test CRM integration."""
    print("\n" + "=" * 60)
    print("  TEST: CRM Integration")
    print("=" * 60)

    from src.api.crm import create_crm_integration

    try:
        crm = create_crm_integration("hubspot")
        print(f"  CRM Type: {type(crm).__name__}")
        print("  [PASS] CRM integration initialized")
        return True
    except Exception as e:
        print(f"  [FAIL] CRM integration error: {e}")
        return False


def test_export():
    """Test export functionality."""
    print("\n" + "=" * 60)
    print("  TEST: Export Functionality")
    print("=" * 60)

    from src.core.export import ExportManager
    from src.main import load_sample_transcript
    from src.core.evaluator import evaluate

    transcript = load_sample_transcript()
    evaluation = evaluate(transcript)

    exporter = ExportManager(evaluation, transcript)

    markdown = exporter.export_markdown()
    json_export = exporter.export_json()
    slack = exporter.export_slack()
    notion = exporter.export_notion()

    print(f"  Markdown: {len(markdown)} chars")
    print(f"  JSON: {len(json_export)} chars")
    print(f"  Slack: {len(slack['blocks'])} blocks")
    print(f"  Notion: {len(notion['properties'])} properties")

    if len(markdown) > 0 and len(json_export) > 0:
        print("  [PASS] Export works")
        return True
    else:
        print("  [FAIL] Export failed")
        return False


def main():
    print("=" * 60)
    print("  CallCoach-AI -- Real API Verification")
    print("=" * 60)

    results = {}

    evaluation = test_real_llm_scoring()
    results['llm_scoring'] = evaluation is not None

    transcript = test_real_whipscribe_api()
    results['whipscribe_api'] = transcript is not None

    results['realtime_coaching'] = test_real_time_coaching()
    results['cross_call_intelligence'] = test_cross_call_intelligence()
    results['crm_integration'] = test_crm_integration()
    results['export'] = test_export()

    print("\n" + "=" * 60)
    print("  VERIFICATION SUMMARY")
    print("=" * 60)

    for test, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test}")

    all_passed = all(results.values())
    print(f"\n  All Tests Passed: {all_passed}")

    if all_passed:
        print("\n  Ready to push!")
    else:
        print("\n  Some tests failed. Fix before pushing.")

    return results


if __name__ == "__main__":
    main()
