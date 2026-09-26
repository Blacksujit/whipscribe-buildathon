"""Slack integration for Meeting QA Copilot.

Delivers quality reports and trend summaries to Slack channels.
"""
import os
import json
import requests
from typing import Dict, List, Optional


def get_slack_client():
    """Get Slack webhook URL from settings or env."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_WEBHOOK")
    # Try to get from store if available
    if not webhook_url:
        try:
            import store
            webhook_url = store.get_setting("slack_webhook")
        except:
            pass
    return webhook_url


def send_to_slack(webhook_url: str, message: Dict) -> bool:
    """Send a message to Slack via webhook."""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Slack delivery failed: {e}")
        return False


def format_qa_report_for_slack(evaluation: Dict, transcript: Dict, job_id: str) -> Dict:
    """Format a single meeting QA report for Slack."""
    overall_score = evaluation.get("overall_score", 0)
    category_scores = evaluation.get("category_scores", {})
    
    # Determine color based on score
    if overall_score >= 80:
        color = "#36a64f"  # green
    elif overall_score >= 60:
        color = "#ff9500"  # orange
    else:
        color = "#ff3b30"  # red
    
    # Build category score fields
    fields = [
        {
            "title": "Overall Score",
            "value": f"{overall_score}/100",
            "short": True
        },
        {
            "title": "Action Items",
            "value": f"{category_scores.get('action_items', 0)}/100",
            "short": True
        },
        {
            "title": "Clarity",
            "value": f"{category_scores.get('clarity', 0)}/100",
            "short": True
        },
        {
            "title": "Compliance",
            "value": f"{category_scores.get('compliance', 0)}/100",
            "short": True
        }
    ]
    
    # Add top issues
    top_issues = evaluation.get("top_issues", [])[:3]
    if top_issues:
        issue_text = "\n".join([
            f"• *{issue.get('category', 'Issue')}* at {issue.get('timestamp', '0:00')}: {issue.get('quote', '')[:60]}..."
            for issue in top_issues
        ])
        fields.append({
            "title": "Top Issues",
            "value": issue_text,
            "short": False
        })
    
    # Add action items
    action_items = evaluation.get("action_items", [])[:3]
    if action_items:
        items_text = "\n".join([
            f"• {item.get('text', '')[:50]}..." 
            for item in action_items
        ])
        fields.append({
            "title": "Action Items",
            "value": items_text,
            "short": False
        })
    
    return {
        "text": f"Meeting QA Report: {transcript.get('filename', 'Recording')}",
        "attachments": [
            {
                "color": color,
                "fields": fields,
                "footer": "Meeting QA Copilot",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "actions": [
                    {
                        "type": "button",
                        "text": "View Full Report",
                        "url": f"https://whipscribe.com/jobs/{job_id}",
                        "style": "primary"
                    }
                ]
            }
        ]
    }


def format_trend_summary_for_slack(comparisons: Dict) -> Dict:
    """Format multi-meeting trend analysis for Slack."""
    trends = comparisons.get("trends", {})
    meetings = comparisons.get("meetings", [])
    insights = comparisons.get("insights", [])
    action_tracking = comparisons.get("action_item_tracking", {})
    
    # Build trend fields
    trend_emojis = {
        "improving": "📈",
        "declining": "📉",
        "stable": "➡️"
    }
    
    fields = [
        {
            "title": "Overall Trend",
            "value": f"{trend_emojis.get(trends.get('overall', 'stable'), '➡️')} {trends.get('overall', 'stable').capitalize()}",
            "short": True
        },
        {
            "title": "Meetings Analyzed",
            "value": str(len(meetings)),
            "short": True
        },
        {
            "title": "Action Item Completion",
            "value": f"{action_tracking.get('completion_rate', 0)}%",
            "short": True
        }
    ]
    
    # Add key insights
    if insights:
        insight_text = "\n".join([f"• {insight}" for insight in insights[:3]])
        fields.append({
            "title": "Key Insights",
            "value": insight_text,
            "short": False
        })
    
    # Add per-metric trends
    metric_trends = []
    for metric in ["action_items", "clarity", "tension", "compliance"]:
        trend = trends.get(metric, "stable")
        emoji = trend_emojis.get(trend, "➡️")
        metric_trends.append(f"{emoji} {metric.replace('_', ' ').title()}: {trend}")
    
    if metric_trends:
        fields.append({
            "title": "Metric Trends",
            "value": "\n".join(metric_trends),
            "short": False
        })
    
    return {
        "text": "📊 Meeting Quality Trend Analysis",
        "attachments": [
            {
                "color": "#007aff",
                "fields": fields,
                "footer": "Meeting QA Copilot",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
            }
        ]
    }


def deliver_qa_report_to_slack(evaluation: Dict, transcript: Dict, job_id: str) -> Optional[str]:
    """Deliver a QA report to Slack and return success message."""
    webhook_url = get_slack_client()
    if not webhook_url:
        print("Slack webhook URL not configured")
        return None
    
    message = format_qa_report_for_slack(evaluation, transcript, job_id)
    success = send_to_slack(webhook_url, message)
    
    if success:
        return "Report delivered to Slack successfully"
    return None


def deliver_trend_summary_to_slack(comparisons: Dict) -> Optional[str]:
    """Deliver a trend summary to Slack and return success message."""
    webhook_url = get_slack_client()
    if not webhook_url:
        print("Slack webhook URL not configured")
        return None
    
    message = format_trend_summary_for_slack(comparisons)
    success = send_to_slack(webhook_url, message)
    
    if success:
        return "Trend summary delivered to Slack successfully"
    return None