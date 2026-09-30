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


# -------------------------------------------------------------- hubspot

HUBSPOT_AUTHORIZE = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_SCOPES = ["oauth", "crm.objects.tasks.read", "crm.objects.tasks.write"]


def hubspot_configured() -> bool:
    return bool(os.environ.get("HUBSPOT_CLIENT_ID") and os.environ.get("HUBSPOT_CLIENT_SECRET"))


def hubspot_authorize_url(redirect_uri: str, state: str = "") -> str:
    params = {
        "client_id": os.environ["HUBSPOT_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "scope": " ".join(HUBSPOT_SCOPES),
    }
    if state:
        params["state"] = state
    return f"{HUBSPOT_AUTHORIZE}?{urlencode(params)}"


def hubspot_exchange(code: str, redirect_uri: str) -> Dict[str, Any]:
    resp = requests.post(
        HUBSPOT_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": os.environ["HUBSPOT_CLIENT_ID"],
            "client_secret": os.environ["HUBSPOT_CLIENT_SECRET"],
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"HubSpot OAuth failed: {resp.status_code} {resp.text[:180]}")
    data = resp.json()
    return {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_in": int(data.get("expires_in") or 1800),
    }


def hubspot_refresh(refresh_token: str) -> Dict[str, Any]:
    """HubSpot access tokens last 30 minutes; refresh tokens keep the tile green."""
    resp = requests.post(
        HUBSPOT_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["HUBSPOT_CLIENT_ID"],
            "client_secret": os.environ["HUBSPOT_CLIENT_SECRET"],
            "refresh_token": refresh_token,
        },
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"HubSpot token refresh failed: {resp.status_code} {resp.text[:180]}")
    data = resp.json()
    return {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token") or refresh_token,
        "expires_in": int(data.get("expires_in") or 1800),
    }


# ------------------------------------------------- state + setup helpers

def sign_state(secret: str, tool: str) -> str:
    """Signed, expiring OAuth state value (CSRF protection)."""
    from itsdangerous import URLSafeTimedSerializer

    return URLSafeTimedSerializer(secret, salt="oauth-state").dumps({"tool": tool})


def verify_state(secret: str, token: str, max_age: int = 900):
    """Return the tool from a signed state value, or None when invalid/expired."""
    from itsdangerous import URLSafeTimedSerializer

    try:
        payload = URLSafeTimedSerializer(secret, salt="oauth-state").loads(token, max_age=max_age)
        return payload.get("tool")
    except Exception:
        return None


SETUP_LINKS = {
    "slack": "https://api.slack.com/apps",
    "notion": "https://www.notion.so/my-integrations",
    "hubspot": "https://developers.hubspot.com/",
}

SETUP_ENV = {
    "slack": ["SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"],
    "notion": ["NOTION_CLIENT_ID", "NOTION_CLIENT_SECRET"],
    "hubspot": ["HUBSPOT_CLIENT_ID", "HUBSPOT_CLIENT_SECRET"],
}


def config(redirect_base: str) -> Dict[str, Any]:
    """What the Connect Center needs: one-click availability plus setup steps."""
    return {
        "slack": {
            "available": slack_configured(),
            "redirect_uri": f"{redirect_base}/api/oauth/slack/callback",
            "setup_url": SETUP_LINKS["slack"],
            "env": SETUP_ENV["slack"],
        },
        "notion": {
            "available": notion_configured(),
            "redirect_uri": f"{redirect_base}/api/oauth/notion/callback",
            "setup_url": SETUP_LINKS["notion"],
            "env": SETUP_ENV["notion"],
        },
        "hubspot": {
            "available": hubspot_configured(),
            "redirect_uri": f"{redirect_base}/api/oauth/hubspot/callback",
            "setup_url": SETUP_LINKS["hubspot"],
            "env": SETUP_ENV["hubspot"],
        },
    }
