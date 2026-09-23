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

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import existing core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.whip_api import (
    list_jobs, get_transcript, poll_job, submit_file, get_me,
    get_session_summary, get_high_signal_moments,
)
from src.evaluator import evaluate
from src.reporter import generate_report
from src.compare import compare_evaluations, generate_comparison_report
from src.slack import deliver_qa_report_to_slack, deliver_trend_summary_to_slack
import store

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

# Enable CORS for Next.js frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_api_key():
    """Get API key from env or DB settings."""
    return os.environ.get("WHIPSKRIBE_API_KEY") or store.get_setting("whipscribe_api_key")


def get_eval_settings():
    """Get LLM settings from env or DB."""
    provider = os.environ.get("LLM_PROVIDER") or store.get_setting("llm_provider")
    api_key = os.environ.get("LLM_API_KEY") or store.get_setting("llm_api_key")
    model = os.environ.get("LLM_MODEL") or store.get_setting("llm_model") or "gpt-4o-mini"
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
    total = action_tracking.get("total", 0)
    rate = action_tracking.get("completion_rate", 0)
    if total > 0:
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


@app.route("/upload", methods=["POST"])
def upload():
    """Handle file upload — submit to WhipScribe API."""
    api_key = get_api_key()
    if not api_key:
        return redirect(url_for("settings"))

    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    try:
        from src.whip_api import submit_file, poll_job, get_transcript as fetch_transcript
        job_id = submit_file(api_key, filepath)
        flash(f"File uploaded. Job {job_id} submitted. Polling...", "info")

        # Store a marker that this job is being processed
        # In production, use a background task queue
        try:
            poll_job(api_key, job_id, timeout=300)
            transcript = fetch_transcript(api_key, job_id)
            provider, llm_key, model = get_eval_settings()
            evaluation = evaluate(transcript, api_key=llm_key, model=model, provider=provider)
            store.save_evaluation(job_id, transcript, evaluation)
            flash(f"Analysis complete! Score: {evaluation['overall_score']}/100", "success")
            return redirect(url_for("report", job_id=job_id))
        except Exception as e:
            flash(f"Error during transcription: {e}", "error")

    finally:
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except OSError:
            pass

    return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
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
                    jobs.append({
                        "job_id": job.get("job_id"),
                        "filename": job.get("filename", "unknown"),
                        "status": job.get("status"),
                        "duration": job.get("audio_duration_seconds", 0),
                        "created_at": job.get("created_at", ""),
                    })
        
        return jsonify({"jobs": jobs, "success": True})
    except Exception as e:
        return jsonify({"jobs": [], "success": False, "error": str(e)}), 500


@app.route("/api/trends-data")
def trends_data():
    """JSON endpoint for Chart.js to render trend charts."""
    evaluations = store.get_all_evaluations()
    if not evaluations:
        return jsonify({"meetings": [], "metrics": []})

    # Sort by created_at
    evals = sorted(evaluations, key=lambda e: e["created_at"])
    labels = [e["meeting_name"] or e["job_id"][:8] for e in evals]

    return jsonify({
        "labels": labels,
        "overall": [e["overall_score"] for e in evals],
        "action_items": [e["action_items"] for e in evals],
        "clarity": [e["clarity"] for e in evals],
        "tension": [e["tension"] for e in evals],
        "compliance": [e["compliance"] for e in evals],
    })


if __name__ == "__main__":
    store.init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
