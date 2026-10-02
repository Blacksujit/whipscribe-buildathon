"""Deliver Meeting Quality Assurance reports to Notion databases."""

import os
from datetime import datetime
from typing import Dict, Any, Optional

import requests


NOTION_API = "https://api.notion.com/v1"

PUBLIC_APP_URL = os.environ.get("PUBLIC_APP_URL", "https://callcoachai.sujit.top").rstrip("/")


def deliver_report(
    report_md: str,
    job_id: str,
    scores: Dict[str, Any],
    notion_token: Optional[str] = None,
    database_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a Notion page with the QA report.

    Parameters
    ----------
    report_md : str
        Full Markdown report text.
    job_id : str
        WhipScribe job ID the report is based on.
    scores : dict
        Evaluation scores dict, e.g. {"overall_score": 90, ...}.
    notion_token : str
        Notion internal integration token (from .env: NOTION_TOKEN).
    database_id : str
        Target Notion database ID (from .env: NOTION_DATABASE_ID).
    """
    token = notion_token or os.getenv("NOTION_TOKEN")
    db_id = database_id or os.getenv("NOTION_DATABASE_ID")
    if not token or not db_id:
        raise RuntimeError(
            "Notion delivery requires NOTION_TOKEN and NOTION_DATABASE_ID env vars."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    overall = scores.get("overall_score", 0)
    report_url = f"{PUBLIC_APP_URL}/report/{job_id}"

    # Split report into Notion blocks (simple paragraph-per-line approach)
    children = [_block("paragraph", f"Open the live scorecard: {report_url}")]
    for line in report_md.strip().splitlines():
        if not line.strip():
            continue
        if line.startswith("# "):
            children.append(_block("heading_1", line.lstrip("# ").strip()))
        elif line.startswith("## "):
            children.append(_block("heading_2", line.lstrip("# ").strip()))
        elif line.startswith("### "):
            children.append(_block("heading_3", line.lstrip("# ").strip()))
        elif line.startswith("- "):
            children.append(_block("bulleted_list_item", line.lstrip("- ").strip()))
        elif line.startswith("|"):
            continue
        else:
            # Strip markdown formatting for Notion rich text
            clean = line.replace("**", "").replace("`", "")
            children.append(_block("paragraph", clean))

    name_property = {"title": [{"text": {"content": f"CallCoach-AI scorecard - {timestamp}"}}]}
    rich_properties = {
        "Name": name_property,
        "Score": {"number": overall},
        "Job ID": {"rich_text": [{"text": {"content": str(job_id)}}]},
        "Date": {"date": {"start": datetime.now().isoformat()[:10]}},
    }

    def _create_page(properties):
        body = {
            "parent": {"database_id": db_id},
            "properties": properties,
            "children": children,
        }
        return requests.post(f"{NOTION_API}/pages", headers=headers, json=body, timeout=30)

    resp = _create_page(rich_properties)
    if resp.status_code == 400:
        # The target database may not have Score / Job ID / Date properties;
        # create the page with the title only so delivery still works.
        resp = _create_page({"Name": name_property})
    resp.raise_for_status()
    result = resp.json()
    return {"page_url": result.get("url"), "page_id": result.get("id")}


def _block(block_type: str, text: str) -> Dict[str, Any]:
    """Create a Notion block dict with a single text paragraph."""
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": [{"text": {"content": text}}],
            "color": "default",
        },
    }
