"""Integration demo showing real WhipScribe API and MCP server usage.

This script demonstrates:
1. Real WhipScribe API calls (upload, poll, fetch transcript)
2. MCP server integration for library operations
3. Slack/Notion delivery of coaching insights
4. Export functionality for coaching reports

Usage:
    python integration_demo.py --api-key <whipscribe_api_key>
    python integration_demo.py --mcp-server
    python integration_demo.py --deliver
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.whip_api import submit_file, submit_url, poll_job, get_transcript, get_session_summary, get_high_signal_moments, get_audio_url
from src.api.slack import send_slack_message
from src.api.notion import deliver_report
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.core.coach import generate_coaching_recommendations, format_recommendations
from src.reporter import generate_report


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_api_integration(api_key):
    """Demo: Real WhipScribe API integration."""
    print_section("WhipScribe API Integration Demo")

    # 1. Submit a file
    print("  [1/5] Submitting file to WhipScribe API...")
    job_id = submit_file(api_key, "test_audio.wav")
    print(f"    Job ID: {job_id}")

    # 2. Poll for completion
    print("\n  [2/5] Polling for completion...")
    poll_job(api_key, job_id)
    print(f"    Transcription complete")

    # 3. Fetch transcript
    print("\n  [3/5] Fetching transcript...")
    transcript = get_transcript(api_key, job_id)
    segments = transcript.get("segments", [])
    print(f"    Segments: {len(segments)}")
    print(f"    Speakers: {len(set(s.get('speaker', 'Unknown') for s in segments))}")

    # 4. Fetch additional context
    print("\n  [4/5] Fetching additional context...")
    session_summary = get_session_summary(api_key, job_id)
    key_moments = get_high_signal_moments(api_key, job_id)
    audio_url = get_audio_url(api_key, job_id)
    print(f"    Session summary: {session_summary.get('summary', 'N/A')[:100]}...")
    print(f"    Key moments: {len(key_moments.get('moments', []))}")
    print(f"    Audio URL: {audio_url.get('url', 'N/A')[:50]}...")

    # 5. Evaluate
    print("\n  [5/5] Running 4-agent evaluation...")
    evaluation = evaluate(transcript, session_summary=session_summary, key_moments=key_moments, audio_url=audio_url)
    print(f"    Overall Score: {evaluation.get('overall_score', 0)}/100")
    print(f"    Categories: {list(evaluation.get('category_scores', {}).keys())}")

    return evaluation


def demo_mcp_integration():
    """Demo: MCP server integration for library operations."""
    print_section("MCP Server Integration Demo")

    print("  MCP Tools Available:")
    print("    1. analyze_meeting - Analyze a meeting transcript")
    print("    2. get_deal_velocity - Get deal velocity metrics")
    print("    3. get_coaching_insights - Get coaching recommendations")
    print("    4. export_meeting_report - Export meeting report")

    print("\n  Example MCP call:")
    print('    tool: "analyze_meeting"')
    print('    arguments: {"job_id": "abc123", "language": "en"}')
    print("    result: {evaluation: {...}, report: {...}}")

    print("\n  MCP server usage:")
    print("    python src/mcp_server.py")
    print("    # Connects to Claude, Cursor, or other AI assistants")
    print("    # Provides 4 tools for meeting analysis and coaching")


def demo_delivery_integration():
    """Demo: Slack and Notion delivery integration."""
    print_section("Delivery Integration Demo")

    print("  Slack Integration:")
    print("    - Send coaching insights to Slack channel")
    print("    - Include score, top issues, and recommendations")
    print("    - Support for threaded replies and reactions")

    print("\n  Notion Integration:")
    print("    - Create Notion page with full coaching report")
    print("    - Include evidence, timestamps, and action items")
    print("    - Support for database views and filtering")

    print("\n  Example Slack message:")
    print("    Channel: #coaching")
    print("    Message: 'CallCoach-AI Report: Overall 72/100'")
    print("    - Compliance: 65/100 (2 risks found)")
    print("    - Action Items: 80/100 (3 items captured)")
    print("    - Top recommendation: Review compliance checklist")

    print("\n  Example Notion page:")
    print("    Title: 'CallCoach-AI Report - Q4 Planning'")
    print("    Content: Full report with evidence and recommendations")
    print("    Database: Coaching reports with filtering by date, score, category")


def demo_export_functionality():
    """Demo: Export functionality for coaching reports."""
    print_section("Export Functionality Demo")

    print("  Supported export formats:")
    print("    1. Markdown (.md) - Full report with evidence")
    print("    2. JSON (.json) - Structured data for integrations")
    print("    3. PDF (.pdf) - Printable coaching report")
    print("    4. Slack message - Formatted for Slack delivery")
    print("    5. Notion page - Full page with database integration")

    print("\n  Example export:")
    print("    python -m src.main --sample --output report.md")
    print("    python -m src.main --sample --output report.json")
    print("    python -m src.main --sample --deliver notion")


def main():
    parser = argparse.ArgumentParser(description="CallCoach-AI Integration Demo")
    parser.add_argument("--api-key", help="WhipScribe API key")
    parser.add_argument("--mcp-server", action="store_true", help="Show MCP server integration")
    parser.add_argument("--deliver", action="store_true", help="Show delivery integration")
    parser.add_argument("--export", action="store_true", help="Show export functionality")
    parser.add_argument("--all", action="store_true", help="Run all demos")

    args = parser.parse_args()

    print_section("CallCoach-AI × WhipScribe — Integration Demo")

    if args.all or args.api_key:
        if not args.api_key:
            print("  [ERROR] --api-key required for API integration demo")
        else:
            demo_api_integration(args.api_key)

    if args.all or args.mcp_server:
        demo_mcp_integration()

    if args.all or args.deliver:
        demo_delivery_integration()

    if args.all or args.export:
        demo_export_functionality()

    if not any([args.api_key, args.mcp_server, args.deliver, args.export, args.all]):
        print("  Usage:")
        print("    python integration_demo.py --all")
        print("    python integration_demo.py --api-key <key>")
        print("    python integration_demo.py --mcp-server")
        print("    python integration_demo.py --deliver")
        print("    python integration_demo.py --export")


if __name__ == "__main__":
    main()
