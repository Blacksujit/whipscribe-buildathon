"""Flask web dashboard for Meeting Quality Assurance.

This dashboard analyzes call recordings from WhipScribe to provide
quality insights, trend analysis, and coaching recommendations.

Routes:
  /                    - Landing page (API key setup + analyze all)
  /report/<job_id>     - Single meeting quality report
  /trends              - Multi-meeting trend dashboard
  /coach               - Coaching insights from trend analysis
  /speakers            - Speaker performance analysis
  /settings            - API key + LLM provider configuration
"""

import json
import os
import sys
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import existing core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.api.whip_api import (
    list_jobs, get_transcript, poll_job, submit_file, get_me,
    get_session_summary, get_high_signal_moments,
)
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations, generate_comparison_report
from src.api.notion import deliver_report
from src.database import store

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

# Enable CORS for Next.js frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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


def get_slack_webhook():
    """Get Slack webhook URL from env or DB."""
    return os.environ.get("SLACK_WEBHOOK_URL") or store.get_setting("slack_webhook")


@app.route("/")
def index():
    """Landing page: show account info, job list, and analyze-all button."""
    api_key = get_api_key()
    
    # Check if we have sample data even without API key
    stored_evaluations = store.get_all_evaluations()
    has_sample_data = len(stored_evaluations) > 0
    
    # If no API key and no sample data, redirect to settings
    if not api_key and not has_sample_data:
        return redirect(url_for("settings"))

    # Get account info
    account = None
    if api_key:
        try:
            account = get_me(api_key)
        except Exception as e:
            # Don't show error on initial load, just continue with sample data
            account = None

    # Get all jobs on the account
    jobs = []
    if api_key:
        try:
            all_jobs = list_jobs(api_key, limit=100)
            
            # Handle different response formats
            if isinstance(all_jobs, str):
                # API returned error string - log it but don't crash
                print(f"API Error: {all_jobs}")
                all_jobs = []
            elif isinstance(all_jobs, dict):
                # API might return {jobs: [...]} or similar structure
                all_jobs = all_jobs.get("jobs", [])
            
            # Filter to done jobs only
            if isinstance(all_jobs, list):
                for job in all_jobs:
                    if isinstance(job, dict) and job.get("status") == "done":
                        jobs.append({
                            "job_id": job.get("job_id"),
                            "filename": job.get("filename", "unknown"),
                            "language": job.get("language", "?"),
                            "duration": job.get("audio_duration_seconds", 0),
                            "created_at": job.get("created_at", ""),
                        })
        except Exception as e:
            # Don't crash on API errors, just continue with sample data
            print(f"Error listing jobs: {e}")
            jobs = []

    # Check which evaluations are stored
    stored = store.get_all_evaluations()
    stored_ids = {e["job_id"] for e in stored}

    return render_template("index.html", account=account, jobs=jobs, stored_ids=stored_ids)


@app.route("/analyze-all")
def analyze_all():
    """Analyze ALL meetings on the account at once.

    This pulls every job, evaluates each, stores results, and redirects
    to the trends dashboard for comprehensive team analysis.
    """
    api_key = get_api_key()
    if not api_key:
        flash("Please set your API key in Settings first.", "error")
        return redirect(url_for("settings"))

    provider, llm_key, model = get_eval_settings()

    try:
        all_jobs = list_jobs(api_key, limit=100)
        done_jobs = [j for j in all_jobs if j.get("status") == "done"]
    except Exception as e:
        flash(f"Error listing jobs: {e}", "error")
        return redirect(url_for("index"))

    evaluated = 0
    errors = 0
    for job in done_jobs[:20]:  # Cap at 20 to avoid timeouts
        job_id = job.get("job_id")
        if not job_id:
            continue
        try:
            transcript = get_transcript(api_key, job_id)
            if not transcript.get("speech_detected", True):
                continue
            if len(transcript.get("segments", [])) < 2:
                continue

            evaluation = evaluate(
                transcript,
                api_key=llm_key,
                model=model,
                provider=provider,
            )
            store.save_evaluation(job_id, transcript, evaluation)
            
            # Auto-deliver to Slack if configured
            slack_result = deliver_qa_report_to_slack(evaluation, transcript, job_id)
            if slack_result:
                print(f"  Slack: {slack_result}")
            
            evaluated += 1
        except Exception as e:
            errors += 1

    flash(f"Analyzed {evaluated} meetings ({errors} errors).", "success")
    return redirect(url_for("trends"))


@app.route("/analyze/<job_id>")
def analyze_single(job_id):
    """Analyze a single meeting by job ID."""
    api_key = get_api_key()
    if not api_key:
        return redirect(url_for("settings"))

    provider, llm_key, model = get_eval_settings()

    try:
        transcript = get_transcript(api_key, job_id)
    except Exception as e:
        flash(f"Error fetching transcript: {e}", "error")
        return redirect(url_for("index"))

    evaluation = evaluate(
        transcript,
        api_key=llm_key,
        model=model,
        provider=provider,
    )
    store.save_evaluation(job_id, transcript, evaluation)
    
    # Auto-deliver to Slack if configured
    slack_result = deliver_qa_report_to_slack(evaluation, transcript, job_id)
    if slack_result:
        flash(f"Report delivered to Slack: {slack_result}", "success")

    return redirect(url_for("report", job_id=job_id))


@app.route("/report/<job_id>")
def report(job_id):
    """Show a single meeting's QA report."""
    result = store.get_evaluation(job_id)
    if result is None:
        flash("No evaluation found. Analyze first.", "error")
        return redirect(url_for("index"))

    transcript = result["transcript"]
    evaluation = result["evaluation"]
    report_md = generate_report(evaluation, transcript, job_id)

    # Check if audio URL is available
    audio_url = None
    api_key = get_api_key()
    if api_key:
        try:
            from src.whip_api import get_audio_url
            audio_data = get_audio_url(api_key, job_id)
            audio_url = audio_data.get("url")
        except Exception:
            pass

    return render_template(
        "report.html",
        job_id=job_id,
        transcript=transcript,
        evaluation=evaluation,
        report_md=report_md,
        audio_url=audio_url,
    )


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
            from src.whip_api import get_audio_url
            audio_data = get_audio_url(api_key, job_id)
            audio_url = audio_data.get("url")
        except Exception:
            pass

    return jsonify({
        "success": True,
        "job_id": job_id,
        "transcript": transcript,
        "evaluation": evaluation,
        "audio_url": audio_url
    })


@app.route("/api/speakers")
def api_speakers():
    """JSON endpoint for speaker performance analysis."""
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        return jsonify({"success": False, "error": "Need at least 2 analyzed meetings for speaker analysis."}), 400

    eval_dicts = []
    names = []
    for e in evaluations:
        eval_json = json.loads(e["evaluation"]) if isinstance(e["evaluation"], str) else e["evaluation"]
        core = eval_json.get("evaluation", eval_json) if isinstance(eval_json, dict) else {}
        eval_dicts.append({
            "overall_score": core.get("overall_score", 0),
            "category_scores": core.get("category_scores", {}),
            "action_items": core.get("action_items", []),
            "clarity_issues": core.get("clarity_issues", []),
            "tension_signals": core.get("tension_signals", []),
            "compliance_risks": core.get("compliance_risks", []),
        })
        names.append(e.get("meeting_name") or e["job_id"][:8])

    from src.core.compare import compare_evaluations
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

@app.route("/trends")
def trends():
    """Multi-meeting trend dashboard.

    Shows quality trends across all stored meetings with slope analysis
    and coaching insights.
    """
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        flash("Need at least 2 analyzed meetings for trends. Analyze more meetings.", "info")
        return redirect(url_for("index"))

    # Build evaluation dicts for compare.py
    eval_dicts = []
    names = []
    for e in evaluations:
        eval_dicts.append({
            "overall_score": e["overall_score"],
            "category_scores": {
                "action_items": e["action_items"],
                "clarity": e["clarity"],
                "tension": e["tension"],
                "compliance": e["compliance"],
            },
            "action_items": [],
            "clarity_issues": [],
            "tension_signals": [],
            "compliance_risks": [],
        })
        names.append(e["meeting_name"] or e["job_id"][:8])

    comparisons = compare_evaluations(eval_dicts, names)
    report = generate_comparison_report(comparisons)

    return render_template(
        "trends.html",
        meetings=evaluations,
        comparisons=comparisons,
        report=report,
    )


@app.route("/speakers")
def speakers():
    """Speaker performance analysis page.
    
    NEW FEATURE: Shows which speakers contribute to quality issues,
    identifies high-risk speakers, and tracks individual performance.
    """
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        flash("Need at least 2 analyzed meetings for speaker analysis.", "info")
        return redirect(url_for("index"))

    eval_dicts = []
    names = []
    for e in evaluations:
        eval_dicts.append({
            "overall_score": e["overall_score"],
            "category_scores": {
                "action_items": e["action_items"],
                "clarity": e["clarity"],
                "tension": e["tension"],
                "compliance": e["compliance"],
            },
            "action_items": e.get("action_items_list", []),
            "clarity_issues": e.get("clarity_issues_list", []),
            "tension_signals": e.get("tension_signals_list", []),
            "compliance_risks": e.get("compliance_risks_list", []),
        })
        names.append(e["meeting_name"] or e["job_id"][:8])

    comparisons = compare_evaluations(eval_dicts, names)
    speaker_analysis = comparisons.get("speaker_analysis", {})

    return render_template(
        "speakers.html",
        speaker_analysis=speaker_analysis,
        comparisons=comparisons,
    )


@app.route("/trends/slack")
def trends_to_slack():
    """Deliver trend summary to Slack."""
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        flash("Need at least 2 analyzed meetings for trends.", "error")
        return redirect(url_for("index"))

    eval_dicts = []
    names = []
    for e in evaluations:
        eval_dicts.append({
            "overall_score": e["overall_score"],
            "category_scores": {
                "action_items": e["action_items"],
                "clarity": e["clarity"],
                "tension": e["tension"],
                "compliance": e["compliance"],
            },
            "action_items": [],
            "clarity_issues": [],
            "tension_signals": [],
            "compliance_risks": [],
        })
        names.append(e["meeting_name"] or e["job_id"][:8])

    comparisons = compare_evaluations(eval_dicts, names)
    slack_result = deliver_trend_summary_to_slack(comparisons)
    
    if slack_result:
        flash(f"Trend summary delivered to Slack: {slack_result}", "success")
    else:
        flash("Slack delivery failed. Check webhook configuration.", "error")
    
    return redirect(url_for("trends"))


@app.route("/coach")
def coach():
    """Coaching insights page — prescriptive advice from trends."""
    evaluations = store.get_all_evaluations()
    if len(evaluations) < 2:
        flash("Need at least 2 analyzed meetings for coaching.", "info")
        return redirect(url_for("index"))

    eval_dicts = []
    names = []
    for e in evaluations:
        eval_dicts.append({
            "overall_score": e["overall_score"],
            "category_scores": {
                "action_items": e["action_items"],
                "clarity": e["clarity"],
                "tension": e["tension"],
                "compliance": e["compliance"],
            },
            "action_items": [],
            "clarity_issues": [],
            "tension_signals": [],
            "compliance_risks": [],
        })
        names.append(e["meeting_name"] or e["job_id"][:8])

    comparisons = compare_evaluations(eval_dicts, names)

    # Generate coaching insights
    insights = _generate_coaching_insights(comparisons, evaluations)

    return render_template("coach.html", insights=insights, comparisons=comparisons)


def _generate_coaching_insights(comparisons, evaluations):
    """Generate prescriptive coaching insights from trend data.

    Goes beyond what compare.py does — adds actionable recommendations.
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
                "overall": "Overall meeting quality is declining. Review the root causes in clarity, tension, and compliance.",
                "clarity": "Clarity scores are dropping — reps may be rushing or unprepared. Recommend pre-meeting prep sheets.",
                "tension": "Tension is rising — conflict or defensive language is increasing. Consider a facilitator training session.",
                "compliance": "Compliance risks are rising — someone is making unbacked promises. Add a pre-call compliance checklist.",
                "action_items": "Action items are worsening — fewer items are being captured. Coach reps on closing with clear ownership.",
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
                "message": "Quality is improving — identify what worked and reinforce it.",
                "advice": f"Keep the practices from {meetings[-1]['name']} — they're helping.",
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
                "message": f"Action item completion rate is {rate}% — too low.",
                "advice": "Reps are forgetting to close out tasks. Add a follow-up ritual within 24 hours of each meeting.",
                "scores": [],
            })
        elif rate < 100:
            insights.append({
                "type": "action_items_ok",
                "metric": "action_items",
                "message": f"Action item completion rate is {rate}% — good progress.",
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
            "advice": "Create a team playbook entry for each recurring risk and review before each call.",
            "scores": [],
        })

    return insights


@app.route("/api/upload", methods=["POST"])
def upload():
    """Handle file upload — submit to WhipScribe API."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "API key not configured"}), 401

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    try:
        from src.api.whip_api import submit_file, poll_job, get_transcript as fetch_transcript
        from src.core.evaluator import evaluate
        from src.database import store
        
        job_id = submit_file(api_key, filepath)
        
        # Logic for async processing in a production environment.
        # Here we poll synchronously for the demo flow.
        poll_job(api_key, job_id, timeout=300)
        transcript = fetch_transcript(api_key, job_id)
        
        # THE CLOSING LOOP: Get unresolved promises from previous calls
        pending_items = store.get_unresolved_action_items()
        
        provider, llm_key, model = get_eval_settings()
        evaluation = evaluate(transcript, api_key=llm_key, model=model, provider=provider, pending_items=pending_items)
        
        store.save_evaluation(job_id, transcript, evaluation)
        
        # Update DB: Mark resolved items as delivered
        resolved = evaluation.get("evaluation", {}).get("resolved_items", [])
        for item in resolved:
            store.resolve_action_item(item.get("text", ""))
        
        return jsonify({"success": True, "job_id": job_id, "score": evaluation.get("evaluation", {}).get("overall_score")}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
def settings():
    """Settings page: API key + LLM provider + Slack configuration."""
    if request.method == "POST":
        api_key = request.form.get("whipscribe_api_key", "").strip()
        llm_provider = request.form.get("llm_provider", "")
        llm_api_key = request.form.get("llm_api_key", "").strip()
        llm_model = request.form.get("llm_model", "gpt-4o-mini")
        slack_webhook = request.form.get("slack_webhook", "").strip()

        if api_key:
            store.save_setting("whipscribe_api_key", api_key)
        if llm_provider:
            store.save_setting("llm_provider", llm_provider)
        if llm_api_key:
            store.save_setting("llm_api_key", llm_api_key)
        if llm_model:
            store.save_setting("llm_model", llm_model)
        if slack_webhook:
            store.save_setting("slack_webhook", slack_webhook)

        flash("Settings saved. Note: for production, use environment variables instead.", "success")
        return redirect(url_for("settings"))

    # Load existing settings
    existing = {
        "whipscribe_api_key": store.get_setting("whipscribe_api_key") or "",
        "llm_provider": store.get_setting("llm_provider") or os.environ.get("LLM_PROVIDER", ""),
        "llm_api_key": store.get_setting("llm_api_key") or "",
        "llm_model": store.get_setting("llm_model") or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "slack_webhook": store.get_setting("slack_webhook") or os.environ.get("SLACK_WEBHOOK_URL", ""),
    }

    return render_template("settings.html", settings=existing)


@app.route("/api/health")
def api_health():
    """Health check endpoint for testing."""
    return jsonify({"status": "ok", "message": "Flask backend is running"})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Read or save frontend connection settings without exposing secrets in responses."""
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        api_key = str(payload.get("whipscribe_api_key", "")).strip()
        if not api_key:
            return jsonify({"success": False, "error": "WhipScribe API key is required"}), 400
        
        store.save_setting("whipscribe_api_key", api_key)
        if "llm_model" in payload: store.save_setting("llm_model", payload["llm_model"])
        if "slack_webhook" in payload: store.save_setting("slack_webhook", payload["slack_webhook"])
        if "notion_token" in payload: store.save_setting("notion_token", payload["notion_token"])
        if "notion_database_id" in payload: store.save_setting("notion_database_id", payload["notion_database_id"])
        
        return jsonify({"success": True})

    return jsonify({
        "configured": bool(os.environ.get("WHIPSKRIBE_API_KEY") or store.get_setting("whipscribe_api_key")),
        "api_key": "********",
        "llm_model": store.get_setting("llm_model") or os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "slack_webhook": store.get_setting("slack_webhook") or os.environ.get("SLACK_WEBHOOK_URL", ""),
        "notion_token": store.get_setting("notion_token") or os.environ.get("NOTION_TOKEN", ""),
        "notion_database_id": store.get_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID", "")
    })


@app.route("/api/export/notion", methods=["POST"])
def api_export_notion():
    """Export a report to Notion."""
    job_id = request.json.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400

    eval_data = store.get_evaluation(job_id)
    if not eval_data:
        return jsonify({"success": False, "error": "Evaluation not found"}), 404

    try:
        # Convert eval data to simple MD for Notion
        report_md = f"# Meeting QA Report: {job_id}\n\n"
        report_md += f"Overall Score: {eval_data['evaluation'].get('overall_score', 'N/A')}\n\n"
        report_md += "## Key Insights\n"
        for cat, score in eval_data['evaluation'].get('category_scores', {}).items():
            report_md += f"- {cat}: {score}\n"

        notion_token = store.get_setting("notion_token") or os.environ.get("NOTION_TOKEN")
        notion_db_id = store.get_setting("notion_database_id") or os.environ.get("NOTION_DATABASE_ID")

        result = deliver_report(
            report_md=report_md,
            job_id=job_id,
            scores=eval_data['evaluation'],
            notion_token=notion_token,
            database_id=notion_db_id
        )
        return jsonify({"success": True, "page_url": result.get("page_url")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/export/slack", methods=["POST"])
def api_export_slack():
    """Deliver a report to Slack."""
    job_id = request.json.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400

    eval_data = store.get_evaluation(job_id)
    if not eval_data:
        return jsonify({"success": False, "error": "Evaluation not found"}), 404

    try:
        slack_result = deliver_qa_report_to_slack(
            eval_data['evaluation'], 
            eval_data['transcript'], 
            job_id
        )
        if slack_result:
            return jsonify({"success": True, "message": slack_result})
        return jsonify({"success": False, "error": "Slack delivery failed"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/jobs")
def api_jobs():
    """Return jobs as JSON for Next.js frontend."""
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
                    # Enrich job with stored evaluation score if available
                    stored_eval = store.get_evaluation(job.get("job_id"))
                    score = None
                    if stored_eval:
                        eval_json = stored_eval.get("evaluation", {})
                        if isinstance(eval_json, str):
                            eval_json = json.loads(eval_json)
                        score = eval_json.get("overall_score")
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
            "score": evaluation.get("overall_score", 0),
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


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload one recording from the Next.js drop zone and analyze it."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"success": False, "error": "No WhipScribe API key configured"}), 401

    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"success": False, "error": "Choose an audio or video file"}), 400

    filename = secure_filename(uploaded.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    uploaded.save(filepath)

    try:
        job_id = submit_file(api_key, filepath)
        poll_job(api_key, job_id, timeout=300)
        transcript = get_transcript(api_key, job_id)
        provider, llm_key, model = get_eval_settings()
        evaluation = evaluate(transcript, api_key=llm_key, model=model, provider=provider)
        store.save_evaluation(job_id, transcript, evaluation)
        return jsonify({
            "success": True,
            "job_id": job_id,
            "score": evaluation.get("overall_score", 0),
            "segments": len(transcript.get("segments", [])),
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 502
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass


@app.route("/api/trends-data")
def trends_data():
    """JSON endpoint for Chart.js to render trend charts."""
    from src.core.metrics import calculate_deal_velocity, calculate_momentum_slope
    import json
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
            # Handle both the wrapper { 'evaluation': { ... } } and the direct { ... }
            core_eval = eval_json.get("evaluation", eval_json) if isinstance(eval_json, dict) else {}
            parsed_evals.append({
                "meeting_name": e["meeting_name"] or e["job_id"][:8],
                "overall_score": core_eval.get("overall_score", 0),
                "core": core_eval
            })
        except (json.JSONDecodeError, TypeError):
            continue

    labels = [p["meeting_name"] for p in parsed_evals]
    scores = [p["overall_score"] or 0 for p in parsed_evals]
    
    # Calculate real mathematical metrics
    velocity = calculate_deal_velocity([p["core"] for p in parsed_evals])
    slope = calculate_momentum_slope(scores)
    momentum = "increasing" if slope > 0.5 else "decreasing" if slope < -0.5 else "stable"

    # Extract category scores from the latest quality evaluation (score >= 90)
    # Falls back to latest with any non-zero category scores
    category_scores = {"action_items": 0, "clarity": 0, "tension": 0, "compliance": 0}
    seen_any_nonzero = False
    fallback_scores = category_scores.copy()
    for p in reversed(parsed_evals):
        core = p.get("core", {})
        if not core:
            continue
        score = core.get("overall_score", 0)
        cat = core.get("category_scores", {})
        if not cat or not isinstance(cat, dict):
            continue
        # Check both formats
        if "action_items" in cat:
            ai = int(cat.get("action_items", 0) or 0)
            cl = int(cat.get("clarity", 0) or 0)
            te = int(cat.get("tension", 0) or 0)
            co = int(cat.get("compliance", 0) or 0)
            mapped = {"action_items": ai, "clarity": cl, "tension": te, "compliance": co}
        elif "commitments" in cat:
            ai = int(cat.get("commitments", 0) or 0)
            cl = int(cat.get("narrative", 0) or 0)
            te = int(cat.get("friction", 0) or 0)
            co = int(cat.get("velocity", 0) or 0)
            mapped = {"action_items": ai, "clarity": cl, "tension": te, "compliance": co}
        else:
            continue
        # Track fallback for first non-zero
        if not seen_any_nonzero and any(v > 0 for v in mapped.values()):
            fallback_scores = mapped
            seen_any_nonzero = True
        # Prefer quality evals with score >= 90
        if score and score >= 90 and any(v > 0 for v in mapped.values()):
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

    eval_dicts = []
    names = []
    for item in evaluations:
        eval_json = json.loads(item["evaluation"]) if isinstance(item["evaluation"], str) else item["evaluation"]
        core = eval_json.get("evaluation", eval_json) if isinstance(eval_json, dict) else {}
        eval_dicts.append({
            "overall_score": core.get("overall_score", 0),
            "category_scores": core.get("category_scores", {}),
            "action_items": core.get("action_items", []),
            "clarity_issues": core.get("clarity_issues", []),
            "tension_signals": core.get("tension_signals", []),
            "compliance_risks": core.get("compliance_risks", []),
        })
        names.append(item.get("meeting_name") or item["job_id"][:8])

    comparisons = compare_evaluations(eval_dicts, names)
    return jsonify({
        "ready": True,
        "insights": _generate_coaching_insights(comparisons, eval_dicts),
        "trends": comparisons.get("trends", {}),
        "action_item_tracking": comparisons.get("action_item_tracking", {}),
    })


if __name__ == "__main__":
    store.init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
