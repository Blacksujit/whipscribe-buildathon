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
)
from src.api.notion import NOTION_API, deliver_report
from src.api.slack import (
    deliver_qa_report_to_slack,
    deliver_trend_summary_to_slack,
    send_to_slack,
)
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.database import store

MASK = "********"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
UPLOAD_POLL_TIMEOUT = int(os.environ.get("UPLOAD_POLL_TIMEOUT", "900"))
UPLOAD_URL_POLL_TIMEOUT = int(os.environ.get("UPLOAD_URL_POLL_TIMEOUT", "1800"))

# Create tables at import time so gunicorn / production servers work too.
store.init_db()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24).hex()
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "2048")) * 1024 * 1024

_cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
CORS(app, origins=_cors_origins)


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
    return {
        "connected": bool(stored or env),
        "source": "stored" if stored else ("env" if env else None),
    }


def _notion_connection():
    stored_token = _stored_setting("notion_token")
    env_token = (os.environ.get("NOTION_TOKEN") or "").strip() or None
    database = _stored_setting("notion_database_id") or (os.environ.get("NOTION_DATABASE_ID") or "").strip() or None
    token = stored_token or env_token
    return {
        "connected": bool(token and database),
        "source": "stored" if stored_token else ("env" if env_token else None),
        "database_id": database,
        "token_set": bool(token),
    }


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
    """Integration status. Secrets are never returned, only booleans and sources."""
    api_key = get_api_key()
    whip_env = bool(os.environ.get("WHIPSKRIBE_API_KEY"))
    whip_stored = bool(_stored_setting("whipscribe_api_key"))
    provider, llm_key, model = get_eval_settings()
    return jsonify({
        "whipscribe": {
            "connected": bool(api_key),
            "source": "env" if whip_env else ("stored" if whip_stored else None),
        },
        "slack": _slack_connection(),
        "notion": _notion_connection(),
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
        return jsonify({"success": False, "error": "Slack did not accept the test message. Check the webhook and try again."}), 502

    store.save_setting("slack_webhook", webhook)
    return jsonify({"success": True, "message": "Connected - test message delivered to Slack."})


@app.route("/api/connections/slack/test", methods=["POST"])
def api_connections_slack_test():
    """Send a test message through the configured Slack webhook."""
    webhook = _stored_setting("slack_webhook") or os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK")
    if not webhook:
        return jsonify({"success": False, "error": "Slack is not connected yet."}), 400
    if not send_to_slack(webhook, {"text": "Test from CallCoach-AI - delivery is working."}):
        return jsonify({"success": False, "error": "Slack did not accept the message."}), 502
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


def _process_upload(api_key, job_id, poll_timeout=UPLOAD_POLL_TIMEOUT):
    """Background worker: transcribe, score, store. Updates the live stage."""
    try:
        _set_upload_state(job_id, stage="transcribing", message="WhipScribe is transcribing the recording.")
        poll_job(api_key, job_id, timeout=poll_timeout)
        transcript = get_transcript(api_key, job_id)
        _set_upload_state(job_id, stage="scoring", message="Four agents are reading the transcript.")

        pending_items = store.get_unresolved_action_items()
        provider, llm_key, model = get_eval_settings()
        evaluation = evaluate(
            transcript, api_key=llm_key, model=model,
            provider=provider, pending_items=pending_items,
        )
        store.save_evaluation(job_id, transcript, evaluation)

        core = _core_eval(evaluation)
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
    threading.Thread(target=_process_upload, args=(api_key, job_id), daemon=True).start()

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
        kwargs={"poll_timeout": UPLOAD_URL_POLL_TIMEOUT},
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

    return jsonify({
        "success": True,
        "job_id": job_id,
        "transcript": transcript,
        "evaluation": evaluation,
        "audio_url": audio_url,
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

    return jsonify({
        "success": True,
        "speakers": speakers_list,
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
        evaluation = evaluate(transcript, api_key=llm_key, model=model, provider=provider)
        store.save_evaluation(job_id, transcript, evaluation)
        return jsonify({
            "success": True,
            "job_id": job_id,
            "score": _core_eval(evaluation).get("overall_score", 0),
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

    return jsonify({
        "labels": labels,
        "overall": scores,
        "velocity": round(velocity, 1),
        "momentum": momentum,
        "slope": round(slope, 2),
        "category_scores": category_scores,
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
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
