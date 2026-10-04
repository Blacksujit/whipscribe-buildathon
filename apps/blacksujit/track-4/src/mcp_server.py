"""CallCoach-AI MCP server.

Exposes the QA pipeline as MCP tools so any assistant (Claude, Cursor, ...)
can analyze meetings, read the cross-meeting deal velocity and export reports.

Run (stdio):
  cd apps/blacksujit/track-4
  python src/mcp_server.py

Env (loaded from the project .env when present):
  WHIPSCRIBE_API_KEY (legacy WHIPSKRIBE_API_KEY also accepted)
  LLM_PROVIDER (groq | openai | anthropic)
  LLM_MODEL
  GROQ_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY / LLM_API_KEY
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from mcp.server.mcpserver import MCPServer

from src.api.whip_api import poll_job, get_transcript
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.reporter import generate_report
from src.api.notion import deliver_report
from src.api.slack import deliver_qa_report_to_slack
from src.database import store

store.init_db()

mcp = MCPServer("CallCoach-AI")

API_KEY = os.environ.get("WHIPSCRIBE_API_KEY") or os.environ.get("WHIPSKRIBE_API_KEY")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
LLM_API_KEY = (
    os.environ.get("GROQ_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or os.environ.get("ANTHROPIC_API_KEY")
    or os.environ.get("LLM_API_KEY")
)


def _core(result):
    """Return the inner evaluation dict whether the input is wrapped or flat."""
    if not isinstance(result, dict):
        return {}
    inner = result.get("evaluation")
    return inner if isinstance(inner, dict) else result


def _load_or_evaluate(job_id):
    """Return (transcript, core_evaluation) from the store or fresh analysis."""
    stored = store.get_evaluation(job_id)
    if stored:
        return stored["transcript"], stored["evaluation"]

    status = poll_job(API_KEY, job_id)
    if status != "done":
        raise RuntimeError(f"Job {job_id} is still {status}. Please wait.")
    transcript = get_transcript(API_KEY, job_id)
    result = evaluate(transcript, api_key=LLM_API_KEY, model=LLM_MODEL, provider=LLM_PROVIDER)
    core = _core(result)
    store.save_evaluation(job_id, transcript, core)
    return transcript, core


@mcp.tool()
async def analyze_meeting(job_id: str) -> str:
    """Analyze a meeting for quality, clarity, tension and compliance. Returns the score summary."""
    try:
        if not API_KEY:
            return "WHIPSCRIBE_API_KEY is not set for this MCP server."
        _, core = _load_or_evaluate(job_id)
        return (
            f"Analysis complete for {job_id}\n"
            f"Overall score: {core.get('overall_score')}/100\n"
            f"Summary: {core.get('summary', '')}\n"
            f"Top risk: {core.get('deal_killer', 'n/a')}\n"
            f"Action items: {len(core.get('action_items', []))} found."
        )
    except Exception as e:
        return f"Error analyzing meeting: {e}"


@mcp.tool()
async def get_deal_velocity(job_ids: list[str]) -> str:
    """Calculate Deal Velocity across several meetings to show momentum."""
    try:
        evaluations = []
        names = []
        for jid in job_ids:
            stored = store.get_evaluation(jid)
            if stored:
                evaluations.append(stored["evaluation"])
            else:
                transcript = get_transcript(API_KEY, jid)
                result = evaluate(transcript, api_key=LLM_API_KEY, model=LLM_MODEL, provider=LLM_PROVIDER)
                core = _core(result)
                store.save_evaluation(jid, transcript, core)
                evaluations.append(core)
            names.append(jid[:8])

        comparison = compare_evaluations(evaluations, names)
        velocity = comparison["deal_velocity"]
        trends = comparison.get("trends", {})
        return (
            f"Deal Velocity: {velocity['velocity']} (score {velocity['score']})\n"
            f"Commitment rate: {velocity['metrics']['commitment_rate']}\n"
            f"Clarity slope: {velocity['metrics']['clarity_slope']}\n"
            f"Overall trend: {trends.get('overall', 'insufficient_data')}"
        )
    except Exception as e:
        return f"Error calculating velocity: {e}"


@mcp.tool()
async def get_coaching_insights() -> str:
    """Summarize cross-meeting trends and action-item completion from stored evaluations."""
    try:
        evals, names = store.get_evaluation_dicts_for_comparison()
        if len(evals) < 2:
            return "Need at least 2 analyzed meetings. Use analyze_meeting first."
        comparisons = compare_evaluations(evals, names)
        velocity = comparisons["deal_velocity"]
        insights = comparisons.get("insights", [])
        tracking = comparisons.get("action_item_tracking", {})
        lines = [
            f"Meetings analyzed: {len(evals)}",
            f"Deal Velocity: {velocity['velocity']} (score {velocity['score']})",
            f"Action item completion: {tracking.get('completion_rate', 0)}% "
            f"({tracking.get('resolved', 0)}/{tracking.get('total', 0)})",
            "Insights:",
        ]
        lines += [f"- {i}" for i in insights[:5]] or ["- (none yet)"]
        return "\n".join(lines)
    except Exception as e:
        return f"Error building insights: {e}"


@mcp.tool()
async def export_meeting_report(job_id: str, target: str) -> str:
    """Export a meeting report to 'notion' or 'slack'."""
    try:
        transcript, core = _load_or_evaluate(job_id)
        report_md = generate_report(core, transcript, job_id)

        if target.lower() == "notion":
            res = deliver_report(report_md, job_id, core)
            return f"Exported to Notion: {res.get('page_url', 'success')}"
        if target.lower() == "slack":
            res = deliver_qa_report_to_slack(core, transcript, job_id)
            return f"Exported to Slack: {res or 'failed - check SLACK_WEBHOOK_URL'}"
        return "Invalid target. Use 'notion' or 'slack'."
    except Exception as e:
        return f"Export failed: {e}"


if __name__ == "__main__":
    mcp.run()
