"""HubSpot delivery: real CRM tasks for analyzed calls.

Uses the HubSpot v3 CRM API with a private-app token. Every task created here
lands in the user's real portal.
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

BASE = "https://api.hubapi.com"
PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "https://callcoachai.sujit.top").rstrip("/")


def _headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def verify(token: str) -> Dict[str, Any]:
    """Check the token by reading one task. Raises with a friendly message."""
    resp = requests.get(
        f"{BASE}/crm/v3/objects/tasks",
        headers=_headers(token),
        params={"limit": 1},
        timeout=15,
    )
    if resp.status_code == 401:
        raise RuntimeError(
            "HubSpot rejected the token. Create a private app with the "
            "crm.objects.tasks read+write scope and paste its token."
        )
    resp.raise_for_status()
    return resp.json()


def deliver_task(evaluation: Dict[str, Any], job_id: str,
                 call_name: Optional[str] = None,
                 token: Optional[str] = None) -> Dict[str, Any]:
    """Create a real HubSpot task describing the scorecard."""
    token = token or os.getenv("HUBSPOT_TOKEN")
    if not token:
        raise RuntimeError("HubSpot is not connected.")

    from src.api.slack import collect_top_issues

    score = evaluation.get("overall_score", 0)
    lines = [f"CallCoach-AI scorecard: {score}/100"]
    if evaluation.get("summary"):
        lines.append(str(evaluation["summary"])[:300])
    lines.append(f"Report: {PUBLIC_APP_URL}/report/{job_id}")
    lines.append("")

    issues = collect_top_issues(evaluation, limit=3)
    if issues:
        lines.append("What to fix:")
        lines.extend(f"- {line.replace('*', '')}" for line in issues)

    items = evaluation.get("action_items", [])[:3]
    if items:
        lines.append("")
        lines.append("Commitments:")
        lines.extend(f"- {(item.get('text') or '')[:120]}" for item in items)

    payload = {
        "properties": {
            "hs_task_subject": f"Call review: {call_name or job_id[:8]} ({score}/100)",
            "hs_task_body": "\n".join(lines),
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "MEDIUM",
            "hs_timestamp": str(int(time.time() * 1000)),
        }
    }
    resp = requests.post(
        f"{BASE}/crm/v3/objects/tasks",
        headers=_headers(token),
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data.get("id"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
