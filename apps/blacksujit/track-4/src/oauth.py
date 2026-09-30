"""OAuth helpers for one-click Slack and Notion connections.

Every helper here is env-gated: if the client id/secret are not configured the
app falls back to the guided paste flow.
"""

import base64
import os
from typing import Any, Dict, List
from urllib.parse import urlencode

import requests

SLACK_AUTHORIZE = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN = "https://slack.com/api/oauth.v2.access"
SLACK_SCOPES = "chat:write,channels:read,groups:read"

NOTION_AUTHORIZE = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


# ---------------------------------------------------------------- slack

def slack_configured() -> bool:
    return bool(os.environ.get("SLACK_CLIENT_ID") and os.environ.get("SLACK_CLIENT_SECRET"))


def slack_authorize_url(redirect_uri: str, state: str = "") -> str:
    params = {
        "client_id": os.environ["SLACK_CLIENT_ID"],
        "scope": SLACK_SCOPES,
        "redirect_uri": redirect_uri,
    }
    if state:
        params["state"] = state
    return f"{SLACK_AUTHORIZE}?{urlencode(params)}"


def slack_exchange(code: str, redirect_uri: str) -> Dict[str, Any]:
    resp = requests.post(
        SLACK_TOKEN,
        data={
            "client_id": os.environ["SLACK_CLIENT_ID"],
            "client_secret": os.environ["SLACK_CLIENT_SECRET"],
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=20,
    )
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack OAuth failed: {data.get('error', 'unknown')}")
    return {
        "access_token": data.get("access_token"),
        "team": (data.get("team") or {}).get("name") or "",
    }


def slack_channels(token: str) -> List[Dict[str, str]]:
    """List channels the bot can post to."""
    resp = requests.get(
        "https://slack.com/api/conversations.list",
        headers={"Authorization": f"Bearer {token}"},
        params={"types": "public_channel,private_channel", "limit": 200, "exclude_archived": "true"},
        timeout=20,
    )
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack channel list failed: {data.get('error', 'unknown')}")
    return [
        {"id": c.get("id"), "name": c.get("name"), "member": bool(c.get("is_member"))}
        for c in data.get("channels", [])
    ]


# --------------------------------------------------------------- notion

def notion_configured() -> bool:
    return bool(os.environ.get("NOTION_CLIENT_ID") and os.environ.get("NOTION_CLIENT_SECRET"))


def notion_authorize_url(redirect_uri: str, state: str = "") -> str:
    params = {
        "client_id": os.environ["NOTION_CLIENT_ID"],
        "response_type": "code",
        "owner": "user",
        "redirect_uri": redirect_uri,
    }
    if state:
        params["state"] = state
    return f"{NOTION_AUTHORIZE}?{urlencode(params)}"


def notion_exchange(code: str, redirect_uri: str) -> Dict[str, Any]:
    credentials = f"{os.environ['NOTION_CLIENT_ID']}:{os.environ['NOTION_CLIENT_SECRET']}"
    basic = base64.b64encode(credentials.encode()).decode()
    resp = requests.post(
        NOTION_TOKEN_URL,
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/json"},
        json={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Notion OAuth failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    return {
        "access_token": data.get("access_token"),
        "workspace": data.get("workspace_name") or "",
    }


def notion_databases(token: str) -> List[Dict[str, str]]:
    """Search the workspace for databases the integration can write to."""
    resp = requests.post(
        f"{NOTION_API}/search",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
        json={"filter": {"value": "database", "property": "object"}, "page_size": 100},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Notion search failed: {resp.status_code} {resp.text[:200]}")
    results = []
    for item in resp.json().get("results", []):
        title = ""
        for part in (item.get("title") or []):
            title += part.get("plain_text", "")
        results.append({"id": item.get("id"), "title": title or "Untitled database"})
    return results
