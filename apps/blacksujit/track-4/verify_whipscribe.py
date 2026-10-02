"""Verify WhipScribe API with real audio file."""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def test_whipscribe_api():
    """Test WhipScribe API with real audio file."""
    print("=" * 60)
    print("  TEST: Real WhipScribe API with Audio File")
    print("=" * 60)

    whip_key = os.getenv("WHIPSKRIBE_API_KEY")
    print(f"  API Key: {whip_key[:10]}..." if whip_key else "  API Key: NOT SET")

    if not whip_key:
        print("  [FAIL] No WhipScribe API key")
        return None

    try:
        from src.api.whip_api import submit_file, poll_job, get_transcript, get_session_summary, get_high_signal_moments, get_audio_url

        # Use real audio file
        test_file = "src/test_speech.wav"
        if not os.path.exists(test_file):
            print(f"  [FAIL] Audio file not found: {test_file}")
            return None

        file_size = os.path.getsize(test_file)
        print(f"  Audio file: {test_file} ({file_size} bytes)")

        # Submit
        print("  Submitting to WhipScribe API...")
        job_id = submit_file(whip_key, test_file)
        print(f"  Job ID: {job_id}")

        # Poll
        print("  Polling for completion...")
        poll_job(whip_key, job_id)
        print("  Transcription complete!")

        # Fetch transcript
        print("  Fetching transcript...")
        transcript = get_transcript(whip_key, job_id)
        segments = transcript.get("segments", [])
        print(f"  Segments: {len(segments)}")

        if len(segments) > 0:
            print(f"  First segment: {segments[0].get('text', '')[:80]}...")
            print(f"  Speakers: {len(set(s.get('speaker', 'Unknown') for s in segments))}")

            # Fetch additional context
            print("  Fetching session summary...")
            session_summary = get_session_summary(whip_key, job_id)
            print(f"  Summary: {session_summary.get('summary', 'N/A')[:80]}...")

            print("  Fetching key moments...")
            key_moments = get_high_signal_moments(whip_key, job_id)
            print(f"  Key moments: {len(key_moments.get('moments', []))}")

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


def test_full_pipeline():
    """Test full pipeline: WhipScribe → LLM Scoring → Report."""
    print("\n" + "=" * 60)
    print("  TEST: Full Pipeline (WhipScribe → LLM → Report)")
    print("=" * 60)

    whip_key = os.getenv("WHIPSKRIBE_API_KEY")
    llm_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "groq")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    if not whip_key or not llm_key:
        print("  [FAIL] Missing API keys")
        return None

    try:
        from src.api.whip_api import submit_file, poll_job, get_transcript, get_session_summary, get_high_signal_moments, get_audio_url
        from src.core.evaluator import evaluate
        from src.reporter import generate_report

        # Step 1: Upload and transcribe
        print("  Step 1: Uploading audio to WhipScribe...")
        job_id = submit_file(whip_key, "src/test_speech.wav")
        poll_job(whip_key, job_id)
        transcript = get_transcript(whip_key, job_id)
        print(f"    Transcribed: {len(transcript.get('segments', []))} segments")

        # Step 2: Fetch context
        print("  Step 2: Fetching context...")
        session_summary = get_session_summary(whip_key, job_id)
        key_moments = get_high_signal_moments(whip_key, job_id)
        try:
            audio_url = get_audio_url(whip_key, job_id).get("url")
        except:
            audio_url = None

        # Step 3: LLM Scoring
        print("  Step 3: Running 4-agent LLM scoring...")
        result = evaluate(
            transcript,
            api_key=llm_key,
            provider=provider,
            model=model,
            session_summary=session_summary,
            key_moments=key_moments,
            audio_url=audio_url
        )

        if isinstance(result, dict) and "evaluation" in result:
            evaluation = result["evaluation"]
        else:
            evaluation = result

        print(f"    Overall Score: {evaluation.get('overall_score', 0)}/100")
        print(f"    Categories: {evaluation.get('category_scores', {})}")
        print(f"    Action Items: {len(evaluation.get('action_items', []))}")
        print(f"    Compliance Risks: {len(evaluation.get('compliance_risks', []))}")

        # Step 4: Generate report
        print("  Step 4: Generating report...")
        report = generate_report(evaluation, transcript, job_id)
        print(f"    Report length: {len(report)} characters")

        if evaluation.get('overall_score', 0) > 0:
            print("  [PASS] Full pipeline works end-to-end with real APIs")
            return evaluation
        else:
            print("  [FAIL] Pipeline returned 0 score")
            return None

    except Exception as e:
        print(f"  [FAIL] Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 60)
    print("  CallCoach-AI — Real WhipScribe API Verification")
    print("=" * 60)

    # Test 1: WhipScribe API
    transcript = test_whipscribe_api()

    # Test 2: Full Pipeline
    evaluation = test_full_pipeline()

    # Summary
    print("\n" + "=" * 60)
    print("  VERIFICATION SUMMARY")
    print("=" * 60)

    results = {
        'whipscribe_api': transcript is not None,
        'full_pipeline': evaluation is not None,
    }

    for test, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test}")

    all_passed = all(results.values())
    print(f"\n  All Tests Passed: {all_passed}")

    if all_passed:
        print("\n  Ready to push with real API integration confirmed!")
    else:
        print("\n  Some tests failed. Fix before pushing.")

    return results


if __name__ == "__main__":
    main()
