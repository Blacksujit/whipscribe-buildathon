"""Slack delivery for CallCoach-AI scorecards and trend digests.

Two real paths:
- Webhook: the user pastes a Slack incoming webhook (validated with a test message).
- Bot token: after the OAuth flow, scorecards are posted via chat.postMessage.
"""

import os
from typing import Dict, List, Optional

import requests

PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "https://callcoachai.sujit.top").rstrip("/")


def get_slack_client():
    """Webhook URL: a connection made in the app wins over the deployment env."""
    webhook_url = None
    try:
        from src.database import store

        stored = store.get_setting("slack_webhook")
        if isinstance(stored, str) and stored.strip():
            webhook_url = stored.strip()
    except Exception:
        webhook_url = None
    if not webhook_url:
        env = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_WEBHOOK")
        webhook_url = env.strip() if env and env.strip() else None
    return webhook_url


def get_slack_bot():
    """Bot token + default channel from settings (OAuth path), trimmed."""
    try:
        from src.database import store

        token = store.get_setting("slack_bot_token")
        channel = store.get_setting("slack_channel")
        token = token.strip() if isinstance(token, str) and token.strip() else None
        channel = channel.strip() if isinstance(channel, str) and channel.strip() else None
        return token, channel
    except Exception:
        return None, None


def send_to_slack(webhook_url: str, message: Dict) -> bool:
    """Send a message to Slack via webhook."""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Slack delivery failed: {exc}")
        return False


def send_via_token(token: str, channel: str, message: Dict):
    """Post via chat.postMessage; returns (ok, error)."""
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={**message, "channel": channel},
            timeout=10,
        )
        data = resp.json()
        return bool(data.get("ok")), data.get("error")
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _fmt_time(seconds) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        total = 0
    return f"{total // 60}:{total % 60:02d}"


def collect_top_issues(evaluation: Dict, limit: int = 4) -> List[str]:
    """Merge the issue lists the four agents produce into readable lines."""
    lines: List[str] = []
    for item in (evaluation.get("compliance_risks") or [])[:2]:
        lines.append(
            f"*Compliance* {_fmt_time(item.get('start'))} - {item.get('speaker', 'Unknown')}: "
            f"\"{(item.get('text') or '')[:110]}\""
        )
    for item in (evaluation.get("tension_signals") or [])[:1]:
        lines.append(
            f"*Tension* {_fmt_time(item.get('start'))} - {item.get('speaker_a', 'Unknown')}: "
            f"\"{(item.get('text_a') or '')[:110]}\""
        )
    for item in (evaluation.get("clarity_issues") or [])[:2]:
        lines.append(
            f"*Clarity* {_fmt_time(item.get('start'))} - {item.get('speaker', 'Unknown')}: "
            f"\"{(item.get('text') or '')[:110]}\""
        )
    return lines[:limit]


def format_qa_report_for_slack(evaluation: Dict, transcript: Dict, job_id: str,
                               call_name: Optional[str] = None) -> Dict:
    """Format a scorecard for Slack: score, what to fix, commitments, link."""
    score = evaluation.get("overall_score", 0)
    categories = evaluation.get("category_scores", {})
    color = "#36a64f" if score >= 80 else "#ff9500" if score >= 60 else "#ff3b30"
    report_url = f"{PUBLIC_APP_URL}/report/{job_id}"
    title = call_name or (transcript or {}).get("filename") or "Recording"

    fields = [
        {"title": "Overall", "value": f"{score}/100", "short": True},
        {"title": "Compliance", "value": f"{categories.get('compliance', 0)}/100", "short": True},
        {"title": "Clarity", "value": f"{categories.get('clarity', 0)}/100", "short": True},
        {"title": "Tension", "value": f"{categories.get('tension', 0)}/100", "short": True},
    ]

    issues = collect_top_issues(evaluation)
    if issues:
        fields.append({"title": "What to fix", "value": "\n".join(issues), "short": False})

    items = evaluation.get("action_items", [])[:3]
    if items:
        fields.append({
            "title": "Commitments",
            "value": "\n".join(f"- {(item.get('text') or '')[:90]}" for item in items),
            "short": False,
        })

    return {
        "text": f"*{title}* scored {score}/100 - <{report_url}|open the scorecard>",
        "attachments": [
            {
                "color": color,
                "fields": fields,
                "footer": "CallCoach-AI x WhipScribe",
            }
        ],
    }


def format_trend_summary_for_slack(comparisons: Dict) -> Dict:
    """Format the cross-call trend summary for Slack."""
    trends = comparisons.get("trends", {})
    meetings = comparisons.get("meetings", [])
    insights = comparisons.get("insights", [])
    action_tracking = comparisons.get("action_item_tracking", {})

    fields = [
        {"title": "Overall trend", "value": str(trends.get("overall", "stable")).capitalize(), "short": True},
        {"title": "Calls analyzed", "value": str(len(meetings)), "short": True},
        {"title": "Action item completion", "value": f"{action_tracking.get('completion_rate', 0)}%", "short": True},
    ]

    if insights:
        fields.append({
            "title": "Key insights",
            "value": "\n".join(f"- {insight}" for insight in insights[:3]),
            "short": False,
        })

    metric_lines = []
    for metric in ["action_items", "clarity", "tension", "compliance"]:
        trend = trends.get(metric, "stable")
        metric_lines.append(f"{metric.replace('_', ' ').title()}: {trend}")
    if metric_lines:
        fields.append({"title": "Metric trends", "value": "\n".join(metric_lines), "short": False})

    return {
        "text": "CallCoach-AI trend summary",
        "attachments": [
            {
                "color": "#007aff",
                "fields": fields,
                "footer": "CallCoach-AI x WhipScribe",
            }
        ],
    }


def deliver_qa_report(evaluation: Dict, transcript: Dict, job_id: str,
                      call_name: Optional[str] = None) -> Optional[str]:
    """Deliver a scorecard: bot token first (OAuth), then webhook."""
    message = format_qa_report_for_slack(evaluation, transcript, job_id, call_name)

    token, channel = get_slack_bot()
    if token and channel:
        ok, error = send_via_token(token, channel, message)
        if ok:
            return f"scorecard posted to {channel}"
        print(f"Slack bot delivery failed: {error}")

    webhook_url = get_slack_client()
    if webhook_url and send_to_slack(webhook_url, message):
        return "scorecard posted to the Slack channel"
    return None


def deliver_qa_report_to_slack(evaluation: Dict, transcript: Dict, job_id: str) -> Optional[str]:
    """Backwards-compatible alias used by the export endpoint."""
    return deliver_qa_report(evaluation, transcript, job_id)


def deliver_trend_summary_to_slack(comparisons: Dict) -> Optional[str]:
    """Deliver a trend summary to Slack."""
    message = format_trend_summary_for_slack(comparisons)
    token, channel = get_slack_bot()
    if token and channel:
        ok, _ = send_via_token(token, channel, message)
        if ok:
            return f"trend summary posted to {channel}"
    webhook_url = get_slack_client()
    if webhook_url and send_to_slack(webhook_url, message):
        return "trend summary posted to the Slack channel"
    return None
