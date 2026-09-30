"""CallCoach-AI Flask API.

JSON API behind the Next.js dashboard. The server-rendered Jinja dashboard
was retired in favor of the Next.js app in `frontend/` (see README).

Routes:
  /                          Service info (points at the dashboard URL)
  /api/health                Health check
  /api/connections           GET integration status (whipscribe/slack/notion/llm)
  /api/connections/slack     POST connect (validates with a test message) / DELETE
  /api/connections/slack/test POST send a test message
  /api/connections/notion    POST connect (validates the database) / DELETE
  /api/connections/notion/test POST send a test page
  /api/connections/whipscribe/test POST verify the WhipScribe key
  /api/jobs                  GET WhipScribe jobs, enriched with stored scores
  /api/report/<job_id>       GET one stored report (transcript + evaluation)
  /api/speakers              GET speaker-level issue analysis
  /api/analyze/<job_id>      POST evaluate one existing job
  /api/analyze-all           POST evaluate every finished job on the account
  /api/upload                POST upload a file; returns immediately, processes in a thread
  /api/upload/status/<id>    GET live stage of an upload (transcribing/scoring/done/error)
  /api/trends-data           GET cross-meeting trend metrics for charts
  /api/coach-data            GET prescriptive coaching insights
  /api/export/notion         POST push a report to Notion
  /api/export/slack          POST push a report to Slack
  /api/export/trends         POST push the trend summary to Slack
"""

import json
import os
import re
import sys
import threading
import time
import uuid

import requests
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.whip_api import (
    list_jobs, get_transcript, poll_job, submit_file, submit_url, get_audio_url, get_me,
    get_session_summary, get_high_signal_moments, get_insights,
)
from src.api.notion import NOTION_API, deliver_report
from src.api.slack import (
    collect_top_issues,
    deliver_qa_report,
    deliver_qa_report_to_slack,
    deliver_trend_summary_to_slack,
    format_qa_report_for_slack,
    get_slack_client,
    send_to_slack,
    send_via_token,
)
from src.api.hubspot import deliver_task as deliver_hubspot_task, verify as verify_hubspot
from src import oauth
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.core.dynamics import analyze_dynamics, dynamics_line
from src.core.commitments import build_ledger
from src.core.sentiment import SentimentTracker
from src.core.rubric import RubricManager, create_default_rubrics, DEFAULT_RUBRICS, ScoringRubric
from src.core.coaching_plan import CoachingPlanGenerator
from src.core.export import ExportManager
from src.database import store

MASK = "********"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
UPLOAD_POLL_TIMEOUT = int(os.environ.get("UPLOAD_POLL_TIMEOUT", "900"))
UPLOAD_URL_POLL_TIMEOUT = int(os.environ.get("UPLOAD_URL_POLL_TIMEOUT", "1800"))

# Restore the shipped seed snapshot first, then create tables: the copy would
# otherwise replace the freshly created deliveries table with the seed file.
try:
    store.seed_if_missing()
except Exception:
    pass
store.init_db()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24).hex()
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "2048")) * 1024 * 1024

_cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://callcoach-ai-dashboard.vercel.app,https://callcoach-ai-whhipscribe.vercel.app",
    ).split(",")
    if origin.strip()
]
CORS(app, origins=_cors_origins if _cors_origins else "*", supports_credentials=True)


def get_api_key():
    """Get a request-scoped key, then fall back to env or local settings."""
    request_key = request.headers.get("X-API-Key", "").strip()
    return request_key or os.environ.get("WHIPSKRIBE_API_KEY") or store.get_setting("whipscribe_api_key")


def get_eval_settings():
    """Get LLM settings from env or DB."""
    provider = os.environ.get("LLM_PROVIDER") or store.get_setting("llm_provider")
    model = os.environ.get("LLM_MODEL") or store.get_setting("llm_model") or "gpt-4o-mini"

    api_key = None
    if provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY") or store.get_setting("groq_api_key")
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or store.get_setting("llm_api_key")
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY") or store.get_setting("llm_api_key")
    else:
        api_key = os.environ.get("LLM_API_KEY") or store.get_setting("llm_api_key")

    if provider == "groq" and not os.environ.get("LLM_MODEL"):
        model = "openai/gpt-oss-120b"
    elif provider == "anthropic" and not os.environ.get("LLM_MODEL"):
        model = "claude-3-5-sonnet-20241022"

    return provider, api_key, model


def _core_eval(evaluation):
    """Return the inner evaluation dict (LLM pipeline output is wrapped)."""
    if not isinstance(evaluation, dict):
        return {}
    inner = evaluation.get("evaluation")
    return inner if isinstance(inner, dict) else evaluation


def _stored_eval_dicts(evaluations):
    """Normalize stored rows into compare.py inputs."""
    eval_dicts = []
    names = []
    for item in evaluations:
        raw = item["evaluation"]
        eval_json = json.loads(raw) if isinstance(raw, str) else raw
        core = _core_eval(eval_json)
        eval_dicts.append({
            "overall_score": core.get("overall_score", 0),
            "category_scores": core.get("category_scores", {}),
            "action_items": core.get("action_items", []),
            "clarity_issues": core.get("clarity_issues", []),
            "tension_signals": core.get("tension_signals", []),
            "compliance_risks": core.get("compliance_risks", []),
        })
        names.append(item.get("meeting_name") or item["job_id"][:8])
    return eval_dicts, names


def _stored_setting(name):
    """Return a setting value that is not blank, else None."""
    value = store.get_setting(name)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


# ---------------------------------------------------------------- connections

def _slack_connection():
    stored = _stored_setting("slack_webhook")
    env = (os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK") or "").strip() or None
    token = _stored_setting("slack_bot_token")
    channel = _stored_setting("slack_channel")
    return {
        "connected": bool(stored or env or (token and channel)),
        "mode": "oauth" if (token and channel) else ("stored" if stored else ("env" if env else None)),
        "detail": channel or ("webhook" if (stored or env) else None),
    }


def _notion_connection():
    stored_token = _stored_setting("notion_token")
    env_token = (os.environ.get("NOTION_TOKEN") or "").strip() or None
    database = _stored_setting("notion_database_id") or (os.environ.get("NOTION_DATABASE_ID") or "").strip() or None
    token = stored_token or env_token
    database_name = _stored_setting("notion_database_name")
    # A leftover placeholder from an old env file must not read as connected.
    if database and "your_notion" in database:
        database = None
    return {
        "connected": bool(token and database),
        "mode": "oauth" if database_name else ("stored" if stored_token else ("env" if env_token else None)),
        "detail": database_name or database,
        "database_id": database,
        "token_set": bool(token),
    }


def _hubspot_connection():
    stored = _stored_setting("hubspot_token")
    env = (os.environ.get("HUBSPOT_TOKEN") or "").strip() or None
    return {
        "connected": bool(stored or env),
        "mode": "stored" if stored else ("env" if env else None),
        "detail": "tasks" if (stored or env) else None,
    }


def _auto_enabled(tool):
    """Auto-delivery is on unless the user turned it off."""
    return _stored_setting(f"deliver_auto_{tool}") != "0"


def _whip_extras(api_key, job_id):
    """Extra WhipScribe API reads per analysis: summary, insights, moments, audio URL."""
    extras = {}
    try:
        summary = get_session_summary(api_key, job_id)
        if summary:
            extras["session_summary"] = summary
    except Exception:
        pass
    try:
        insights = get_insights(api_key, job_id)
        if insights:
            extras["insights"] = insights
    except Exception:
        pass
    try:
        moments = get_high_signal_moments(api_key, job_id)
        if moments:
            extras["key_moments"] = moments
    except Exception:
        pass
    try:
        audio = get_audio_url(api_key, job_id)
        if isinstance(audio, dict) and audio.get("url"):
            extras["audio_url"] = audio["url"]
    except Exception:
        pass
    return extras


def _attach_whip_extras(evaluation, extras):
    """Keep the WhipScribe extras on the stored record for the report page."""
    if not isinstance(evaluation, dict) or not extras:
        return
    inner = evaluation.get("evaluation")
    if not isinstance(inner, dict):
        inner = evaluation
    clean = {}
    summary = extras.get("session_summary")
    if isinstance(summary, dict):
        clean["session_summary"] = summary.get("summary") or summary.get("text") or ""
    elif isinstance(summary, str):
        clean["session_summary"] = summary
    moments = extras.get("key_moments")
    if isinstance(moments, dict):
        moments = moments.get("moments") or moments.get("candidates") or moments.get("clips") or []
    if isinstance(moments, list) and moments:
        clean["key_moments"] = moments[:5]
    insights = extras.get("insights")
    if isinstance(insights, dict):
        clean["insights"] = {
            "summary": str(insights.get("summary") or "")[:1200],
            "topics": (insights.get("topics") or [])[:8],
            "quotes": (insights.get("quotes") or [])[:8],
            "speakers": (insights.get("speakers") or [])[:6],
        }
    if extras.get("audio_url"):
        clean["audio_url"] = extras["audio_url"]
    if clean:
        inner["whip"] = clean


def _deliver_scorecard(tool, job_id, evaluation, transcript, name=None):
    """Deliver one scorecard through one tool. Returns (ok, detail)."""
    try:
        if tool == "slack":
            message = deliver_qa_report(evaluation, transcript, job_id, name)
            if message:
                return True, message
            configured = bool(os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK")
                              or _stored_setting("slack_webhook")
                              or (_stored_setting("slack_bot_token") and _stored_setting("slack_channel")))
            return False, ("Slack rejected the message - check the webhook" if configured
                           else "Slack is not connected")
        if tool == "notion":
            report_md = f"# Scorecard: {name or job_id}\n\nOverall score: {evaluation.get('overall_score', 0)}/100\n\n"
            for category, score in (evaluation.get("category_scores") or {}).items():
                report_md += f"- {category}: {score}\n"
            balance = dynamics_line(analyze_dynamics(transcript))
            if balance:
                report_md += f"\n{balance}\n"
            issues = collect_top_issues(evaluation, limit=4)
            if issues:
                report_md += "\n## What to fix\n"
                for line in issues:
                    report_md += f"- {line.replace('*', '')}\n"
            result = deliver_report(
                report_md=report_md,
                job_id=job_id,
                scores=evaluation,
                notion_token=_stored_setting("notion_token") or os.environ.get("NOTION_TOKEN"),
                database_id=_stored_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID"),
            )
            return True, result.get("page_url") or "page created"
        if tool == "hubspot":
            result = deliver_hubspot_task(
                evaluation, job_id, call_name=name, token=_stored_setting("hubspot_token") or os.environ.get("HUBSPOT_TOKEN"),
                transcript=transcript,
            )
            return True, f"task {result.get('id')} created"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return False, "unknown tool"


def _dispatch_deliveries(job_id, evaluation, transcript, name=None):
    """Send the scorecard to every connected tool with auto-delivery on."""
    connections = {
        "slack": _slack_connection()["connected"],
        "notion": _notion_connection()["connected"],
        "hubspot": _hubspot_connection()["connected"],
    }
    for tool, connected in connections.items():
        if not connected or not _auto_enabled(tool):
            continue
        ok, detail = _deliver_scorecard(tool, job_id, evaluation, transcript, name)
        try:
            store.save_delivery(job_id, tool, "ok" if ok else "failed", detail or "")
        except Exception:
            pass


def _dispatch_async(job_id, evaluation, transcript, name=None):
    threading.Thread(
        target=_dispatch_deliveries,
        args=(job_id, evaluation, transcript, name),
        daemon=True,
    ).start()


def _notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def _notion_database_id(value):
    """Accept a raw UUID (dashed or not) or a full Notion URL and return the id."""
    if not value:
        return None
    value = value.strip().split("?")[0].rstrip("/")
    match = re.search(r"([0-9a-fA-F]{32})", value.replace("-", ""))
    if not match:
        return None
    raw = match.group(1)
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


@app.route("/api/connections")
def api_connections():
    """Integration status. Secrets are never returned, only states and sources."""
    api_key = get_api_key()
    whip_env = bool(os.environ.get("WHIPSKRIBE_API_KEY"))
    whip_stored = bool(_stored_setting("whipscribe_api_key"))
    provider, llm_key, model = get_eval_settings()

    try:
        last_deliveries = store.get_last_deliveries()
    except Exception:
        last_deliveries = {}

    oauth_available = {
        "slack": oauth.slack_configured(),
        "notion": oauth.notion_configured(),
        "hubspot": False,
    }

    def tool_block(tool, connection):
        return {
            **connection,
            "auto": _auto_enabled(tool),
            "last_delivery": last_deliveries.get(tool),
            "oauth_available": oauth_available.get(tool, False),
        }

    whip_block = {
        "connected": bool(api_key),
        "source": "env" if whip_env else ("stored" if whip_stored else None),
    }
    if api_key:
        try:
            me = get_me(api_key)
            if isinstance(me, dict):
                whip_block["account"] = me.get("email") or me.get("name")
                whip_block["plan"] = me.get("plan") or me.get("tier")
        except Exception:
            pass

    return jsonify({
        "whipscribe": whip_block,
        "slack": tool_block("slack", _slack_connection()),
        "notion": tool_block("notion", _notion_connection()),
        "hubspot": tool_block("hubspot", _hubspot_connection()),
        "llm": {
            "provider": provider or None,
            "model": model,
            "key_set": bool(llm_key),
        },
    })


@app.route("/api/connections/whipscribe/test", methods=["POST"])
def api_connections_whipscribe_test():
    """Verify the configured WhipScribe key with a real API call."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No WhipScribe key configured on the server."}), 400
    try:
        me = get_me(api_key)
    except Exception as exc:
        return jsonify({"success": False, "error": f"WhipScribe rejected the key: {exc}"}), 502
    if isinstance(me, dict):
        label = me.get("email") or me.get("name") or me.get("plan") or "account verified"
    else:
        label = "account verified"
    return jsonify({"success": True, "message": f"WhipScribe says hello - {label}."})


@app.route("/api/connections/slack", methods=["POST", "DELETE"])
def api_connections_slack():
    """Connect Slack by validating an incoming webhook with a test message."""
    if request.method == "DELETE":
        store.save_setting("slack_webhook", "")
        return jsonify({"success": True, "message": "Slack disconnected."})

    payload = request.get_json(silent=True) or {}
    webhook = str(payload.get("webhook_url", "")).strip()
    if not webhook:
        return jsonify({"success": False, "error": "Paste the Slack incoming webhook URL."}), 400
    if not webhook.startswith("https://hooks.slack.com/"):
        return jsonify({"success": False, "error": "That is not a Slack incoming webhook URL (it starts with https://hooks.slack.com/)."}), 400

    message = {
        "text": "CallCoach-AI is connected. Scores and trend summaries will land in this channel.",
    }
    if not send_to_slack(webhook, message):
        return jsonify({"success": False, "error": "Slack did not accept the test message. Check that the webhook is still active and try again."}), 400

    store.save_setting("slack_webhook", webhook)
    return jsonify({"success": True, "message": "Connected - test message delivered to Slack."})


@app.route("/api/connections/slack/test", methods=["POST"])
def api_connections_slack_test():
    """Send a real test message through whichever Slack path is connected."""
    token, channel = _stored_setting("slack_bot_token"), _stored_setting("slack_channel")
    if token and channel:
        ok, error = send_via_token(token, channel, {"text": "Test from CallCoach-AI - delivery is working."})
        if ok:
            return jsonify({"success": True, "message": f"Test message delivered to {channel}."})
        return jsonify({"success": False, "error": f"Slack rejected the message: {error}"}), 400

    webhook = get_slack_client()
    if not webhook:
        return jsonify({"success": False, "error": "Slack is not connected yet."}), 400
    if not send_to_slack(webhook, {"text": "Test from CallCoach-AI - delivery is working."}):
        return jsonify({"success": False, "error": "Slack did not accept the message - the webhook may be revoked. Reconnect it in the Connect Center."}), 400
    return jsonify({"success": True, "message": "Test message delivered."})


@app.route("/api/connections/notion", methods=["POST", "DELETE"])
def api_connections_notion():
    """Connect Notion by validating the integration token against the database."""
    if request.method == "DELETE":
        store.save_setting("notion_token", "")
        store.save_setting("notion_database_id", "")
        return jsonify({"success": True, "message": "Notion disconnected."})

    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token", "")).strip() or _stored_setting("notion_token") or os.environ.get("NOTION_TOKEN")
    database = str(payload.get("database", "")).strip()
    database_id = _notion_database_id(database) or _stored_setting("notion_database_id")
    if not token:
        return jsonify({"success": False, "error": "Paste the Notion integration token."}), 400
    if not database_id:
        return jsonify({"success": False, "error": "Paste the database link from Notion (Share -> Copy link)."}), 400

    try:
        resp = requests.get(f"{NOTION_API}/databases/{database_id}", headers=_notion_headers(token), timeout=20)
    except Exception as exc:
        return jsonify({"success": False, "error": f"Could not reach Notion: {exc}"}), 502
    if resp.status_code == 404:
        return jsonify({"success": False, "error": "Notion cannot see that database. Share it with your integration first."}), 404
    if resp.status_code >= 400:
        return jsonify({"success": False, "error": f"Notion rejected the token (HTTP {resp.status_code})."}), 502

    title = ""
    try:
        parts = resp.json().get("title", [])
        title = "".join(p.get("plain_text", "") for p in parts)
    except Exception:
        title = ""

    store.save_setting("notion_token", token)
    store.save_setting("notion_database_id", database_id)
    label = f" - {title}" if title else ""
    return jsonify({"success": True, "message": f"Connected to the Notion database{label}."})


@app.route("/api/connections/notion/test", methods=["POST"])
def api_connections_notion_test():
    """Write a small test page into the connected Notion database."""
    token = _stored_setting("notion_token") or os.environ.get("NOTION_TOKEN")
    database_id = _stored_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID")
    if not token or not database_id:
        return jsonify({"success": False, "error": "Notion is not connected yet."}), 400
    try:
        result = deliver_report(
            "# CallCoach-AI test page\n\nIf you can read this, report delivery works.",
            "test-page",
            {"overall_score": 0},
            notion_token=token,
            database_id=database_id,
        )
    except Exception as exc:
        return jsonify({"success": False, "error": f"Notion delivery failed: {exc}"}), 502
    return jsonify({"success": True, "message": "Test page created in Notion.", "page_url": result.get("page_url")})


# -------------------------------------------------------------------- uploads

UPLOAD_JOBS = {}
UPLOAD_LOCK = threading.Lock()


def _set_upload_state(job_id, **fields):
    with UPLOAD_LOCK:
        state = UPLOAD_JOBS.setdefault(job_id, {})
        state.update(fields)
        state["updated_at"] = time.time()


def _process_upload(api_key, job_id, poll_timeout=UPLOAD_POLL_TIMEOUT, name=None):
    """Background worker: transcribe, score, store. Updates the live stage."""
    try:
        _set_upload_state(job_id, stage="transcribing", message="WhipScribe is transcribing the recording.")
        poll_job(api_key, job_id, timeout=poll_timeout)
        transcript = get_transcript(api_key, job_id)
        _set_upload_state(job_id, stage="scoring", message="Four agents are reading the transcript.")

        pending_items = store.get_unresolved_action_items()
        provider, llm_key, model = get_eval_settings()
        extras = _whip_extras(api_key, job_id)
        evaluation = evaluate(
            transcript, api_key=llm_key, model=model,
            provider=provider, pending_items=pending_items,
            session_summary=extras.get("session_summary"),
            key_moments=extras.get("key_moments"),
            audio_url=extras.get("audio_url"),
        )
        _attach_whip_extras(evaluation, extras)
        store.save_evaluation(job_id, transcript, evaluation, meeting_name=name)

        core = _core_eval(evaluation)
        _dispatch_async(job_id, core, transcript, name)
        for item in core.get("resolved_items", []):
            store.resolve_action_item(item.get("text", ""), job_id=job_id)

        _set_upload_state(
            job_id,
            stage="done",
            message="Report ready.",
            score=core.get("overall_score", 0),
            segments=len(transcript.get("segments", [])),
        )
    except Exception as exc:
        _set_upload_state(job_id, stage="error", message=str(exc))


@app.errorhandler(413)
def too_large(error):
    return jsonify({"success": False, "error": "Upload exceeds the configured size limit"}), 413


@app.route("/")
def root():
    """Service info. The product UI is the Next.js dashboard."""
    return jsonify({
        "service": "CallCoach-AI",
        "status": "ok",
        "dashboard": FRONTEND_URL,
        "health": "/api/health",
    })


@app.route("/api/health")
def api_health():
    """Health check endpoint for testing."""
    return jsonify({"status": "ok", "message": "Flask backend is running"})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Accept the file, submit it to WhipScribe and return at once.

    Processing (transcription + four-agent scoring) runs in a background
    thread; the dashboard watches /api/upload/status/<job_id> for stages.
    """
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No WhipScribe API key configured"}), 401

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400

    filename = secure_filename(file.filename) or f"upload-{uuid.uuid4().hex}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    try:
        job_id = submit_file(api_key, filepath)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 502
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass

    _set_upload_state(job_id, stage="transcribing", message="WhipScribe is transcribing the recording.", filename=filename)
    threading.Thread(target=_process_upload, args=(api_key, job_id), kwargs={"name": filename}, daemon=True).start()

    return jsonify({"success": True, "job_id": job_id, "stage": "transcribing"}), 202


@app.route("/api/upload/status/<job_id>")
def api_upload_status(job_id):
    """Live stage of an upload: transcribing -> scoring -> done (or error)."""
    with UPLOAD_LOCK:
        state = dict(UPLOAD_JOBS.get(job_id) or {})

    if not state:
        stored = store.get_evaluation(job_id)
        if stored:
            core = stored["evaluation"]
            return jsonify({
                "success": True,
                "stage": "done",
                "message": "Report ready.",
                "score": core.get("overall_score", 0),
            })
        return jsonify({"success": False, "stage": "unknown", "error": "Unknown job."}), 404

    return jsonify({"success": state.get("stage") != "error", **state})


@app.route("/api/upload/url", methods=["POST"])
def api_upload_url():
    """Submit a paste-link to WhipScribe and return at once.

    WhipScribe fetches the media from the URL; processing (transcription +
    four-agent scoring) runs in a background thread and the dashboard polls
    /api/upload/status/<job_id> for stages.
    """
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No WhipScribe API key configured"}), 401

    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url", "")).strip()
    if not url:
        return jsonify({"success": False, "error": "Paste a link to a recording."}), 400

    try:
        job_id = submit_url(api_key, url)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 502

    _set_upload_state(job_id, stage="transcribing", message="WhipScribe is fetching and transcribing the link.", url=url)
    threading.Thread(
        target=_process_upload,
        args=(api_key, job_id),
        kwargs={"poll_timeout": UPLOAD_URL_POLL_TIMEOUT, "name": url},
        daemon=True,
    ).start()

    return jsonify({"success": True, "job_id": job_id, "stage": "transcribing"}), 202


@app.route("/api/jobs")
def api_jobs():
    """Return jobs as JSON for the Next.js frontend."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"jobs": [], "success": False, "error": "No API key configured"}), 401

    try:
        all_jobs = list_jobs(api_key, limit=100)
        jobs = []

        if isinstance(all_jobs, str):
            return jsonify({"jobs": [], "success": False, "error": all_jobs}), 500
        elif isinstance(all_jobs, dict):
            all_jobs = all_jobs.get("jobs", [])

        if isinstance(all_jobs, list):
            for job in all_jobs:
                if isinstance(job, dict) and job.get("status") == "done":
                    stored_eval = store.get_evaluation(job.get("job_id"))
                    score = None
                    if stored_eval:
                        eval_json = stored_eval.get("evaluation", {})
                        if isinstance(eval_json, str):
                            eval_json = json.loads(eval_json)
                        score = _core_eval(eval_json).get("overall_score")
                    jobs.append({
                        "job_id": job.get("job_id"),
                        "filename": job.get("filename", "unknown"),
                        "status": job.get("status"),
                        "duration": job.get("audio_duration_seconds", 0),
                        "created_at": job.get("created_at", ""),
                        "score": score,
                    })

        return jsonify({"jobs": jobs, "success": True})
    except Exception as e:
        return jsonify({"jobs": [], "success": False, "error": str(e)}), 500


@app.route("/api/report/<job_id>")
def api_report(job_id):
    """JSON endpoint for a single meeting report."""
    result = store.get_evaluation(job_id)
    if result is None:
        return jsonify({"success": False, "error": "No evaluation found. Analyze first."}), 404

    transcript = result["transcript"]
    evaluation = result["evaluation"]

    audio_url = None
    api_key = get_api_key()
    if api_key:
        try:
            audio_data = get_audio_url(api_key, job_id)
            audio_url = audio_data.get("url")
        except Exception:
            pass

    # WhipScribe's own read of this call: fresh when possible, stored otherwise.
    whip_read = (evaluation.get("whip") or {}).get("insights") or {}
    if api_key:
        try:
            fresh = get_insights(api_key, job_id)
            if fresh:
                whip_read = {
                    "summary": str(fresh.get("summary") or "")[:1200],
                    "topics": (fresh.get("topics") or [])[:8],
                    "quotes": (fresh.get("quotes") or [])[:8],
                    "speakers": (fresh.get("speakers") or [])[:6],
                }
        except Exception:
            pass

    return jsonify({
        "success": True,
        "job_id": job_id,
        "transcript": transcript,
        "evaluation": evaluation,
        "audio_url": audio_url,
        "dynamics": analyze_dynamics(transcript),
        "whip_read": whip_read,
    })


@app.route("/api/speakers")
def api_speakers():
    """JSON endpoint for speaker performance analysis."""
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        return jsonify({"success": False, "error": "Need at least 2 analyzed meetings for speaker analysis."}), 400

    eval_dicts, names = _stored_eval_dicts(evaluations)
    comparisons = compare_evaluations(eval_dicts, names)

    speaker_analysis = comparisons.get("speaker_analysis", {})
    speakers_list = [
        {
            "name": name,
            "issue_count": info.get("count", 0),
            "issue_types": list(info.get("types", [])),
        }
        for name, info in speaker_analysis.items()
    ]
    speakers_list.sort(key=lambda s: s["issue_count"], reverse=True)

    # Conversation dynamics per speaker across every stored call (pure timestamps).
    totals = {}
    for evaluation in evaluations:
        transcript = evaluation.get("transcript")
        if isinstance(transcript, str):
            try:
                transcript = json.loads(transcript)
            except (json.JSONDecodeError, TypeError):
                transcript = {}
        dynamics = analyze_dynamics(transcript or {})
        for speaker in dynamics.get("speakers", []):
            if speaker["name"] == "Unknown":
                continue
            agg = totals.setdefault(speaker["name"], {
                "talk_seconds": 0.0, "calls": 0, "questions": 0, "overlaps": 0, "longest_seconds": 0.0,
            })
            agg["talk_seconds"] += speaker["talk_seconds"]
            agg["calls"] += 1
            agg["questions"] += speaker["questions"]
            agg["overlaps"] += speaker["overlaps"]
            agg["longest_seconds"] = max(agg["longest_seconds"], speaker["longest_monologue"]["seconds"])

    total_seconds = sum(a["talk_seconds"] for a in totals.values()) or 1.0
    dynamics_list = sorted(
        [
            {
                "name": name,
                "talk_share": round(agg["talk_seconds"] / total_seconds * 100, 1),
                "calls": agg["calls"],
                "questions": agg["questions"],
                "overlaps": agg["overlaps"],
                "longest_monologue_seconds": round(agg["longest_seconds"], 1),
            }
            for name, agg in totals.items()
        ],
        key=lambda item: -item["talk_share"],
    )

    return jsonify({
        "success": True,
        "speakers": speakers_list,
        "dynamics": dynamics_list,
        "high_risk": [s["name"] for s in speakers_list if s["issue_count"] > 5][:5],
        "top_contributors": speakers_list[:5],
    })


@app.route("/api/analyze/<job_id>", methods=["POST"])
def api_analyze(job_id):
    """API endpoint: analyze a single meeting and return JSON."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No API key configured"}), 401

    provider, llm_key, model = get_eval_settings()
    try:
        transcript = get_transcript(api_key, job_id)
        extras = _whip_extras(api_key, job_id)
        evaluation = evaluate(
            transcript, api_key=llm_key, model=model, provider=provider,
            session_summary=extras.get("session_summary"),
            key_moments=extras.get("key_moments"),
            audio_url=extras.get("audio_url"),
        )
        _attach_whip_extras(evaluation, extras)
        store.save_evaluation(job_id, transcript, evaluation)
        core = _core_eval(evaluation)
        _dispatch_async(job_id, core, transcript)
        return jsonify({
            "success": True,
            "job_id": job_id,
            "score": core.get("overall_score", 0),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze-all", methods=["POST"])
def api_analyze_all():
    """API endpoint: analyze all on-account jobs."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No API key configured"}), 401

    provider, llm_key, model = get_eval_settings()
    try:
        all_jobs = list_jobs(api_key, limit=100)
        done_jobs = [j for j in all_jobs if j.get("status") == "done"]
        evaluated = 0
        for job in done_jobs[:20]:
            jid = job.get("job_id")
            if not jid:
                continue
            try:
                transcript = get_transcript(api_key, jid)
                if not transcript.get("speech_detected", True):
                    continue
                if len(transcript.get("segments", [])) < 2:
                    continue
                evaluation = evaluate(transcript, api_key=llm_key, model=model, provider=provider)
                store.save_evaluation(jid, transcript, evaluation)
                evaluated += 1
            except Exception:
                continue
        return jsonify({"success": True, "evaluated": evaluated, "total": len(done_jobs)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """Griot: grounded Q&A over the stored evaluations."""
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"success": False, "error": "Ask a question."}), 400
    job_id = (payload.get("job_id") or "").strip() or None

    from src.core import companion

    provider, llm_key, model = get_eval_settings()
    evaluations = store.get_all_evaluations()
    evidence = companion.build_evidence(evaluations, job_id=job_id)
    result = companion.ask(question, evidence, provider=provider, api_key=llm_key, model=model)
    return jsonify({
        "success": True,
        "answer": result.get("answer", ""),
        "mode": result.get("mode", "data"),
        "sources": result.get("sources", []),
        "calls_used": len(evidence.get("calls", [])),
    })


@app.route("/api/spotter", methods=["POST"])
def api_spotter():
    """Spotter: a real coaching prompt for one live utterance."""
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"success": False, "error": "Send a segment of speech."}), 400

    from src.realtime.analyzer import RealtimeAnalyzer

    analyzer = RealtimeAnalyzer()
    try:
        start = float(payload.get("start") or 0)
    except (TypeError, ValueError):
        start = 0.0
    result = analyzer.add_segment({
        "text": text,
        "speaker": payload.get("speaker") or "Speaker",
        "start": start,
        "end": start + 3,
    })
    analysis = result.get("analysis", {})
    return jsonify({
        "success": True,
        "prompts": result.get("coaching_prompts", []),
        "sentiment": analysis.get("sentiment"),
        "action_item": analysis.get("action_item"),
        "compliance_risk": analysis.get("compliance_risk"),
        "clarity_issue": analysis.get("clarity_issue"),
        "tension_signal": analysis.get("tension_signal"),
    })


@app.route("/api/trends-data")
def trends_data():
    """JSON endpoint for the score progression and momentum charts."""
    from src.core.metrics import calculate_deal_velocity, calculate_momentum_slope

    evaluations = store.get_all_evaluations()
    if not evaluations:
        return jsonify({"labels": [], "overall": [], "velocity": 0, "momentum": "stable"})

    sorted_evals = sorted(evaluations, key=lambda e: e["created_at"])

    parsed_evals = []
    for e in sorted_evals:
        try:
            eval_json = json.loads(e["evaluation"])
            core_eval = _core_eval(eval_json)
            parsed_evals.append({
                "meeting_name": e["meeting_name"] or e["job_id"][:8],
                "overall_score": core_eval.get("overall_score", 0),
                "core": core_eval,
                "created_at": e.get("created_at") or "",
            })
        except (json.JSONDecodeError, TypeError):
            continue

    labels = [p["meeting_name"] for p in parsed_evals]
    scores = [p["overall_score"] or 0 for p in parsed_evals]

    velocity = calculate_deal_velocity([p["core"] for p in parsed_evals])
    slope = calculate_momentum_slope(scores)
    momentum = "increasing" if slope > 0.5 else "decreasing" if slope < -0.5 else "stable"

    category_scores = {"action_items": 0, "clarity": 0, "tension": 0, "compliance": 0}
    for p in reversed(parsed_evals):
        cat = p.get("core", {}).get("category_scores", {})
        if not isinstance(cat, dict) or not cat:
            continue
        if "action_items" in cat:
            mapped = {
                "action_items": int(cat.get("action_items", 0) or 0),
                "clarity": int(cat.get("clarity", 0) or 0),
                "tension": int(cat.get("tension", 0) or 0),
                "compliance": int(cat.get("compliance", 0) or 0),
            }
        elif "commitments" in cat:
            mapped = {
                "action_items": int(cat.get("commitments", 0) or 0),
                "clarity": int(cat.get("narrative", 0) or 0),
                "tension": int(cat.get("friction", 0) or 0),
                "compliance": int(cat.get("velocity", 0) or 0),
            }
        else:
            continue
        if any(v > 0 for v in mapped.values()):
            category_scores = mapped
            break

    # What changed: category movement between the first and second half of the calls.
    changes = []
    core_list = [p["core"] for p in parsed_evals]
    if len(core_list) >= 4:
        half = len(core_list) // 2
        first_half, second_half = core_list[:half], core_list[half:]

        def _avg(evals, key):
            values = [
                int((e.get("category_scores") or {}).get(key, 0) or 0)
                for e in evals
                if isinstance(e.get("category_scores"), dict)
            ]
            values = [v for v in values if v > 0]
            return round(sum(values) / len(values), 1) if values else 0

        for category in ("compliance", "clarity", "tension", "action_items"):
            before, after = _avg(first_half, category), _avg(second_half, category)
            if before or after:
                changes.append({
                    "category": category,
                    "before": before,
                    "after": after,
                    "delta": round(after - before, 1),
                })
        changes.sort(key=lambda c: -abs(c["delta"]))

    # Tone across calls, from the stored transcripts (src/core/sentiment.py).
    tracker = SentimentTracker()
    for evaluation in sorted_evals:
        transcript = evaluation.get("transcript")
        if isinstance(transcript, str):
            try:
                transcript = json.loads(transcript)
            except (json.JSONDecodeError, TypeError):
                transcript = {}
        segments = (transcript or {}).get("segments") or []
        if segments:
            try:
                tracker.add_call(evaluation.get("meeting_name") or evaluation["job_id"][:8], segments)
            except Exception:
                continue
    sentiment = tracker.get_sentiment_trend()

    return jsonify({
        "labels": labels,
        "overall": scores,
        "velocity": round(velocity, 1),
        "momentum": momentum,
        "slope": round(slope, 2),
        "category_scores": category_scores,
        "changes": changes,
        "sentiment": sentiment,
    })


@app.route("/api/coach-data")
def coach_data():
    """Return real cross-meeting coaching insights for the Next.js frontend."""
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        return jsonify({"ready": False, "insights": [], "message": "Analyze at least two meetings first."})

    eval_dicts, names = _stored_eval_dicts(evaluations)
    comparisons = compare_evaluations(eval_dicts, names)
    return jsonify({
        "ready": True,
        "insights": _generate_coaching_insights(comparisons, eval_dicts),
        "trends": comparisons.get("trends", {}),
        "action_item_tracking": comparisons.get("action_item_tracking", {}),
    })


def _generate_coaching_insights(comparisons, evaluations):
    """Generate prescriptive coaching insights from trend data."""
    insights = []
    trends = comparisons.get("trends", {})
    meetings = comparisons.get("meetings", [])
    action_tracking = comparisons.get("action_item_tracking", {})

    for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
        trend = trends.get(metric, "stable")
        if trend == "declining":
            advice = {
                "overall": "Overall call quality is declining. Review the root causes in clarity, tension, and compliance.",
                "clarity": "Clarity scores are dropping - the pitch may be rushed or unprepared. Recommend a pre-call prep sheet.",
                "tension": "Tension is rising - hesitation or defensive language is increasing. Review the flagged moments before the next call.",
                "compliance": "Compliance risks are rising - unbacked promises are being made. Add a pre-call commitments checklist.",
                "action_items": "Action items are worsening - fewer items are being captured. Close every call with clear owners.",
            }
            insights.append({
                "type": "trend_declining",
                "metric": metric,
                "message": comparisons["insights"][0] if comparisons["insights"] else "",
                "advice": advice.get(metric, "Investigate and address."),
                "scores": [m["scores"][metric] for m in meetings],
            })
        elif trend == "improving":
            insights.append({
                "type": "trend_improving",
                "metric": metric,
                "message": "Quality is improving - identify what worked and reinforce it.",
                "advice": f"Keep the practices from {meetings[-1]['name']} - they are helping.",
                "scores": [m["scores"][metric] for m in meetings],
            })

    resolved = action_tracking.get("resolved", 0)
    unresolved_list = action_tracking.get("unresolved", [])
    total_items = resolved + len(unresolved_list)
    if total_items > 0:
        rate = round((resolved / total_items) * 100)
        if rate < 50:
            insights.append({
                "type": "action_items_warning",
                "metric": "action_items",
                "message": f"Action item completion rate is {rate}% - too low.",
                "advice": "Commitments are not being closed out. Add a follow-up ritual within 24 hours of each call.",
                "scores": [],
            })
        elif rate < 100:
            insights.append({
                "type": "action_items_ok",
                "metric": "action_items",
                "message": f"Action item completion rate is {rate}% - good progress.",
                "advice": "Keep the current system and push toward 100% closure.",
                "scores": [],
            })

    common = comparisons.get("common_issues", [])
    compliance_recurring = [i for i in common if i["type"] == "compliance_risks"]
    if compliance_recurring:
        insights.append({
            "type": "compliance_recurring",
            "metric": "compliance",
            "message": f"{len(compliance_recurring)} compliance risk type(s) recur across meetings.",
            "advice": "Create a playbook entry for each recurring risk and review it before each call.",
            "scores": [],
        })

    return insights


# ------------------------------------------------------- delivery controls

@app.route("/api/connections/hubspot", methods=["POST", "DELETE"])
def api_connections_hubspot():
    """Connect HubSpot with a private-app token (verified against the real API)."""
    if request.method == "DELETE":
        store.save_setting("hubspot_token", "")
        return jsonify({"success": True, "message": "HubSpot disconnected."})

    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token", "")).strip()
    if not token:
        return jsonify({"success": False, "error": "Paste the HubSpot private-app token."}), 400
    try:
        verify_hubspot(token)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 400
    store.save_setting("hubspot_token", token)
    return jsonify({"success": True, "message": "Connected - the token can create tasks."})


@app.route("/api/connections/hubspot/test", methods=["POST"])
def api_connections_hubspot_test():
    """Create a real test task in the connected HubSpot portal."""
    token = _stored_setting("hubspot_token") or os.environ.get("HUBSPOT_TOKEN")
    if not token:
        return jsonify({"success": False, "error": "HubSpot is not connected yet."}), 400
    try:
        result = deliver_hubspot_task(
            {"overall_score": 0, "summary": "Connection test from CallCoach-AI."},
            "connection-test",
            call_name="Connection test",
            token=token,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 502
    return jsonify({"success": True, "message": f"Test task {result.get('id')} created in HubSpot."})


@app.route("/api/connections/<tool>/auto", methods=["POST"])
def api_connections_auto(tool):
    """Turn auto-delivery on or off for one tool."""
    if tool not in ("slack", "notion", "hubspot"):
        return jsonify({"success": False, "error": "Unknown tool."}), 404
    payload = request.get_json(silent=True) or {}
    enabled = bool(payload.get("enabled", True))
    store.save_setting(f"deliver_auto_{tool}", "1" if enabled else "0")
    return jsonify({"success": True, "auto": enabled})


@app.route("/api/deliver/<job_id>", methods=["POST"])
def api_deliver(job_id):
    """Send one stored scorecard to the connected tools right now."""
    payload = request.get_json(silent=True) or {}
    wanted = payload.get("tools")

    stored = store.get_evaluation(job_id)
    if not stored:
        return jsonify({"success": False, "error": "No stored evaluation for this job."}), 404

    core = _core_eval(stored.get("evaluation"))
    transcript = stored.get("transcript") or {}
    name = stored.get("meeting_name")
    tools = wanted if isinstance(wanted, list) and wanted else ["slack", "notion", "hubspot"]

    connected = {
        "slack": _slack_connection()["connected"],
        "notion": _notion_connection()["connected"],
        "hubspot": _hubspot_connection()["connected"],
    }
    results = {}
    for tool in tools:
        if tool not in connected:
            results[tool] = {"ok": False, "detail": "unknown tool"}
            continue
        if not connected[tool]:
            results[tool] = {"ok": False, "detail": "not connected"}
            continue
        ok, detail = _deliver_scorecard(tool, job_id, core, transcript, name)
        results[tool] = {"ok": ok, "detail": detail}
        try:
            store.save_delivery(job_id, tool, "ok" if ok else "failed", detail or "")
        except Exception:
            pass
    return jsonify({"success": True, "results": results})


# ---------------------------------------------------------------- oauth

def _oauth_redirect_uri(tool):
    base = os.environ.get("OAUTH_REDIRECT_BASE") or request.url_root.rstrip("/")
    return f"{base}/api/oauth/{tool}/callback"


def _oauth_page(tool, ok, message):
    """Tiny landing page for the OAuth popup; notifies the opener and closes."""
    status = "ok" if ok else "error"
    script = (
        "if (window.opener) { window.opener.postMessage("
        f"{{source:'callcoach-oauth',tool:'{tool}',status:'{status}'}}, '*'); }}"
        "setTimeout(function(){window.close();}, 1200);"
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>CallCoach-AI</title></head>"
        f"<body style='font-family:sans-serif;padding:40px;line-height:1.5'>"
        f"<h2>{'Connected' if ok else 'Connection failed'}</h2><p>{message}</p>"
        f"<script>{script}</script>"
        "<p><a href='/connections'>Back to the Connect Center</a></p></body></html>"
    )


@app.route("/api/oauth/slack/url")
def api_oauth_slack_url():
    if not oauth.slack_configured():
        return jsonify({"success": False, "error": "Slack OAuth is not configured on the server."}), 400
    return jsonify({"success": True, "url": oauth.slack_authorize_url(_oauth_redirect_uri("slack"))})


@app.route("/api/oauth/slack/callback")
def api_oauth_slack_callback():
    code = request.args.get("code")
    if not code:
        return _oauth_page("slack", False, f"Slack authorization failed: {request.args.get('error', 'missing code')}")
    try:
        data = oauth.slack_exchange(code, _oauth_redirect_uri("slack"))
        store.save_setting("slack_bot_token", data["access_token"])
        store.save_setting("slack_workspace", data.get("team", ""))
        return _oauth_page("slack", True, "Slack authorized. Pick a channel back in the Connect Center.")
    except Exception as exc:  # noqa: BLE001
        return _oauth_page("slack", False, str(exc))


@app.route("/api/oauth/slack/channels")
def api_oauth_slack_channels():
    token = _stored_setting("slack_bot_token")
    if not token:
        return jsonify({"success": False, "error": "Slack is not authorized yet."}), 400
    try:
        return jsonify({"success": True, "channels": oauth.slack_channels(token)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 502


@app.route("/api/oauth/slack/channel", methods=["POST"])
def api_oauth_slack_channel():
    payload = request.get_json(silent=True) or {}
    channel = str(payload.get("channel", "")).strip()
    token = _stored_setting("slack_bot_token")
    if not channel or not token:
        return jsonify({"success": False, "error": "Authorize Slack and pick a channel first."}), 400
    ok, error = send_via_token(
        token, channel,
        {"text": "CallCoach-AI connected - scorecards will land in this channel."},
    )
    if not ok:
        return jsonify({"success": False, "error": f"Slack rejected the message: {error}. Invite the app to the channel and retry."}), 400
    store.save_setting("slack_channel", channel)
    return jsonify({"success": True, "message": f"Connected to {channel} - test message delivered."})


@app.route("/api/oauth/notion/url")
def api_oauth_notion_url():
    if not oauth.notion_configured():
        return jsonify({"success": False, "error": "Notion OAuth is not configured on the server."}), 400
    return jsonify({"success": True, "url": oauth.notion_authorize_url(_oauth_redirect_uri("notion"))})


@app.route("/api/oauth/notion/callback")
def api_oauth_notion_callback():
    code = request.args.get("code")
    if not code:
        return _oauth_page("notion", False, f"Notion authorization failed: {request.args.get('error', 'missing code')}")
    try:
        data = oauth.notion_exchange(code, _oauth_redirect_uri("notion"))
        store.save_setting("notion_token", data["access_token"])
        store.save_setting("notion_workspace", data.get("workspace", ""))
        return _oauth_page("notion", True, "Notion authorized. Pick a database back in the Connect Center.")
    except Exception as exc:  # noqa: BLE001
        return _oauth_page("notion", False, str(exc))


@app.route("/api/oauth/notion/databases")
def api_oauth_notion_databases():
    token = _stored_setting("notion_token")
    if not token:
        return jsonify({"success": False, "error": "Notion is not authorized yet."}), 400
    try:
        return jsonify({"success": True, "databases": oauth.notion_databases(token)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 502


@app.route("/api/oauth/notion/database", methods=["POST"])
def api_oauth_notion_database():
    payload = request.get_json(silent=True) or {}
    database = _notion_database_id(str(payload.get("database", "")))
    name = str(payload.get("name", "")).strip()
    token = _stored_setting("notion_token")
    if not database or not token:
        return jsonify({"success": False, "error": "Authorize Notion and pick a database first."}), 400
    try:
        result = deliver_report(
            report_md="# Connected\n\nCallCoach-AI will deliver every new scorecard to this database.",
            job_id="connection-test",
            scores={"overall_score": 0},
            notion_token=token,
            database_id=database,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": str(exc)}), 502
    store.save_setting("notion_database_id", database)
    store.save_setting("notion_database_name", name or database)
    return jsonify({"success": True, "message": "Connected - a confirmation page was created.", "page_url": result.get("page_url")})


@app.route("/api/sample/run", methods=["POST"])
def api_sample_run():
    """Transcribe and score the bundled 26-second sample call (real API usage)."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No WhipScribe key configured on the server."}), 401
    sample_path = os.path.join(PROJECT_DIR, "assets", "sample-call.mp3")
    if not os.path.exists(sample_path):
        return jsonify({"success": False, "error": "Sample audio is missing on the server."}), 500
    try:
        job_id = submit_file(api_key, sample_path)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "error": f"WhipScribe rejected the sample upload: {exc}"}), 502
    _set_upload_state(job_id, stage="transcribing", message="WhipScribe is transcribing the sample call.")
    threading.Thread(
        target=_process_upload,
        args=(api_key, job_id),
        kwargs={"name": "Sample call - Sujit's intro"},
        daemon=True,
    ).start()
    return jsonify({"success": True, "job_id": job_id, "stage": "transcribing"})


# --------------------------------------------- ledger, plans, rubrics, export

@app.route("/api/commitments")
def api_commitments():
    """Cross-call commitment ledger built from stored action items."""
    evaluations = store.get_all_evaluations()
    rows = store.get_all_action_items()
    return jsonify({"success": True, **build_ledger(rows, evaluations)})


@app.route("/api/plan")
def api_plan():
    """A coaching plan generated from the stored evaluations."""
    evaluations = store.get_all_evaluations()
    if not evaluations:
        return jsonify({"success": False, "error": "Analyze a call first."}), 400
    eval_dicts, names = _stored_eval_dicts(evaluations)
    comparisons = compare_evaluations(eval_dicts, names)
    generator = CoachingPlanGenerator()
    plan = generator.generate_plan("You", eval_dicts, comparisons)
    return jsonify({"success": True, "plan": plan})


@app.route("/api/rubrics")
def api_rubrics():
    """The built-in rubric presets (weights per category)."""
    return jsonify({
        "success": True,
        "rubrics": [{"key": key, **value} for key, value in DEFAULT_RUBRICS.items()],
    })


@app.route("/api/rubric/score", methods=["POST"])
def api_rubric_score():
    """Rescore a stored call with custom category weights (pure weighted math)."""
    payload = request.get_json(silent=True) or {}
    job_id = str(payload.get("job_id", "")).strip()
    weights = payload.get("weights") or {}

    stored = store.get_evaluation(job_id) if job_id else None
    if not stored:
        return jsonify({"success": False, "error": "No stored evaluation for this job."}), 404

    core = _core_eval(stored.get("evaluation"))
    category_scores = core.get("category_scores") or {}

    cleaned = {}
    for key in ("compliance", "tension", "clarity", "action_items"):
        try:
            value = float(weights.get(key, 0))
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            cleaned[key] = value
    if not cleaned:
        return jsonify({"success": False, "error": "Provide positive weights for at least one category."}), 400

    total = sum(cleaned.values())
    normalized = {key: value / total for key, value in cleaned.items()}
    score = ScoringRubric("Custom", normalized).calculate_score(category_scores)
    return jsonify({
        "success": True,
        "score": round(score, 1),
        "weights": normalized,
        "category_scores": category_scores,
    })


@app.route("/api/export/markdown/<job_id>")
def api_export_markdown(job_id):
    """Download a stored scorecard as Markdown."""
    stored = store.get_evaluation(job_id)
    if not stored:
        return jsonify({"success": False, "error": "No stored evaluation for this job."}), 404
    manager = ExportManager(_core_eval(stored.get("evaluation")), stored.get("transcript") or {})
    markdown = manager.export_markdown()
    return app.response_class(markdown, mimetype="text/markdown")


@app.route("/api/export/notion", methods=["POST"])
def api_export_notion():
    """Export a report to Notion."""
    payload = request.get_json(silent=True) or {}
    job_id = payload.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400

    eval_data = store.get_evaluation(job_id)
    if not eval_data:
        return jsonify({"success": False, "error": "Evaluation not found"}), 404

    try:
        core = eval_data["evaluation"]
        report_md = f"# Meeting QA Report: {job_id}\n\n"
        report_md += f"Overall Score: {core.get('overall_score', 'N/A')}\n\n"
        report_md += "## Key Insights\n"
        for cat, score in core.get("category_scores", {}).items():
            report_md += f"- {cat}: {score}\n"

        notion_token = _stored_setting("notion_token") or os.environ.get("NOTION_TOKEN")
        notion_db_id = _stored_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID")

        result = deliver_report(
            report_md=report_md,
            job_id=job_id,
            scores=core,
            notion_token=notion_token,
            database_id=notion_db_id,
        )
        return jsonify({"success": True, "page_url": result.get("page_url")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export/slack", methods=["POST"])
def api_export_slack():
    """Deliver a report to Slack."""
    payload = request.get_json(silent=True) or {}
    job_id = payload.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400

    eval_data = store.get_evaluation(job_id)
    if not eval_data:
        return jsonify({"success": False, "error": "Evaluation not found"}), 404

    try:
        slack_result = deliver_qa_report_to_slack(
            eval_data["evaluation"],
            eval_data["transcript"],
            job_id,
        )
        if slack_result:
            return jsonify({"success": True, "message": slack_result})
        return jsonify({"success": False, "error": "Slack delivery failed. Connect Slack under Connections."}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export/trends", methods=["POST"])
def api_export_trends():
    """Deliver the cross-meeting trend summary to Slack."""
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        return jsonify({"success": False, "error": "Need at least 2 analyzed meetings for trends."}), 400

    eval_dicts, names = _stored_eval_dicts(evaluations)
    comparisons = compare_evaluations(eval_dicts, names)
    try:
        result = deliver_trend_summary_to_slack(comparisons)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    if result:
        return jsonify({"success": True, "message": result})
    return jsonify({"success": False, "error": "Slack delivery failed. Connect Slack under Connections."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    try:
        from waitress import serve

        print(f"CallCoach-AI API on http://0.0.0.0:{port} - waitress (production WSGI server)")
        serve(app, host="0.0.0.0", port=port, threads=8)
    except ImportError:
        # Only reached if requirements.txt was not installed; gunicorn is used in
        # production (Procfile / backend.Dockerfile).
        print("waitress is missing - install requirements.txt. Falling back to the Flask dev server.")
        app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
