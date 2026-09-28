"""CallCoach-AI Flask API.

JSON API behind the Next.js dashboard. The server-rendered Jinja dashboard
was retired in favor of the Next.js app in `frontend/` (see README).

Routes:
  /                       Service info (points at the dashboard URL)
  /api/health             Health check
  /api/settings           GET/POST connection settings (secrets masked)
  /api/jobs               GET WhipScribe jobs, enriched with stored scores
  /api/report/<job_id>    GET one stored report (transcript + evaluation)
  /api/speakers           GET speaker-level issue analysis
  /api/analyze/<job_id>   POST evaluate one existing job
  /api/analyze-all        POST evaluate every finished job on the account
  /api/upload             POST upload a file, transcribe and evaluate it
  /api/trends-data        GET cross-meeting trend metrics for charts
  /api/coach-data         GET prescriptive coaching insights
  /api/export/notion      POST push a report to Notion
  /api/export/slack       POST push a report to Slack
  /api/export/trends      POST push the trend summary to Slack
"""

import json
import os
import sys
import uuid

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.whip_api import (
    list_jobs, get_transcript, poll_job, submit_file, get_audio_url,
)
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.api.notion import deliver_report
from src.api.slack import deliver_qa_report_to_slack, deliver_trend_summary_to_slack
from src.database import store

MASK = "********"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
UPLOAD_POLL_TIMEOUT = int(os.environ.get("UPLOAD_POLL_TIMEOUT", "300"))

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

    # Resolve API key based on provider
    api_key = None
    if provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY") or store.get_setting("groq_api_key")
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or store.get_setting("llm_api_key")
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY") or store.get_setting("llm_api_key")
    else:
        api_key = os.environ.get("LLM_API_KEY") or store.get_setting("llm_api_key")

    # Override model based on provider defaults
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


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Read or save connection settings without exposing secrets in responses."""
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        updated = []

        def _save_if_set(field, value):
            value = str(value or "").strip()
            if value and value != MASK:
                store.save_setting(field, value)
                updated.append(field)

        _save_if_set("whipscribe_api_key", payload.get("whipscribe_api_key"))
        for field in ("llm_provider", "llm_model", "llm_api_key", "slack_webhook",
                      "notion_token", "notion_database_id"):
            if field in payload:
                _save_if_set(field, payload.get(field))

        return jsonify({"success": True, "updated": updated})

    api_key_set = bool(os.environ.get("WHIPSKRIBE_API_KEY") or store.get_setting("whipscribe_api_key"))
    slack_set = bool(store.get_setting("slack_webhook") or os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK"))
    notion_set = bool(store.get_setting("notion_token") or os.environ.get("NOTION_TOKEN"))
    llm_key_set = bool(
        os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY") or store.get_setting("llm_api_key")
    )

    return jsonify({
        "configured": api_key_set,
        "api_key": MASK if api_key_set else "",
        "api_key_set": api_key_set,
        "llm_provider": store.get_setting("llm_provider") or os.environ.get("LLM_PROVIDER", ""),
        "llm_model": store.get_setting("llm_model") or os.environ.get("LLM_MODEL", ""),
        "llm_api_key_set": llm_key_set,
        "slack_webhook": MASK if slack_set else "",
        "slack_webhook_set": slack_set,
        "notion_token": MASK if notion_set else "",
        "notion_token_set": notion_set,
        "notion_database_id": store.get_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID", ""),
    })


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload a recording: transcribe on WhipScribe, evaluate, store."""
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

        # Synchronous polling keeps the demo flow simple. Production would
        # queue this and let the client poll /api/report/<job_id> instead.
        poll_job(api_key, job_id, timeout=UPLOAD_POLL_TIMEOUT)
        transcript = get_transcript(api_key, job_id)

        # Close the loop: feed unresolved items from previous meetings in.
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

        return jsonify({
            "success": True,
            "job_id": job_id,
            "score": core.get("overall_score", 0),
            "segments": len(transcript.get("segments", [])),
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass


@app.route("/api/jobs")
def api_jobs():
    """Return jobs as JSON for the Next.js frontend."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"jobs": [], "success": False, "error": "No API key configured"}), 401

    try:
        all_jobs = list_jobs(api_key, limit=100)
        jobs = []

        # Handle different response formats
        if isinstance(all_jobs, str):
            return jsonify({"jobs": [], "success": False, "error": all_jobs}), 500
        elif isinstance(all_jobs, dict):
            all_jobs = all_jobs.get("jobs", [])

        # Filter to done jobs only
        if isinstance(all_jobs, list):
            for job in all_jobs:
                if isinstance(job, dict) and job.get("status") == "done":
                    # Enrich the job with its stored evaluation score if available
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

    # Sort by created_at for chronological slope calculation
    sorted_evals = sorted(evaluations, key=lambda e: e["created_at"])

    parsed_evals = []
    for e in sorted_evals:
        try:
            # The 'evaluation' column is a JSON string
            eval_json = json.loads(e["evaluation"])
            core_eval = _core_eval(eval_json)
            parsed_evals.append({
                "meeting_name": e["meeting_name"] or e["job_id"][:8],
                "overall_score": core_eval.get("overall_score", 0),
                "core": core_eval,
            })
        except (json.JSONDecodeError, TypeError):
            continue

    labels = [p["meeting_name"] for p in parsed_evals]
    scores = [p["overall_score"] or 0 for p in parsed_evals]

    # Calculate real mathematical metrics
    velocity = calculate_deal_velocity([p["core"] for p in parsed_evals])
    slope = calculate_momentum_slope(scores)
    momentum = "increasing" if slope > 0.5 else "decreasing" if slope < -0.5 else "stable"

    # Latest non-zero category scores for the category panel
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
    """Generate prescriptive coaching insights from trend data.

    Goes beyond what compare.py does - adds actionable recommendations.
    """
    insights = []
    trends = comparisons.get("trends", {})
    meetings = comparisons.get("meetings", [])
    action_tracking = comparisons.get("action_item_tracking", {})

    # Trend direction insights with prescriptive advice
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

    # Action item tracking insights
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

    # Recurring compliance insights
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

        notion_token = store.get_setting("notion_token") or os.environ.get("NOTION_TOKEN")
        notion_db_id = store.get_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID")

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
        return jsonify({"success": False, "error": "Slack delivery failed. Check the webhook in settings."}), 500
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
    return jsonify({"success": False, "error": "Slack delivery failed. Check the webhook in settings."}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
