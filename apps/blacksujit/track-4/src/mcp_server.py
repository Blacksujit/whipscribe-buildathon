import asyncio
from mcp.server.fastmcp import FastMCP
from src.api.whip_api import poll_job, get_transcript
from src.core.evaluator import evaluate
from src.core.compare import compare_evaluations
from src.api.notion import deliver_report
from src.api.slack import deliver_report as deliver_slack
import os

# Initialize FastMCP server
mcp = FastMCP("WhipScribe-Intelligence")

# Load settings from environment
API_KEY = os.environ.get("WHIPSKRIBE_API_KEY")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
LLM_API_KEY = (
    os.environ.get("GROQ_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or os.environ.get("ANTHROPIC_API_KEY")
    or os.environ.get("LLM_API_KEY")
)
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")

@mcp.tool()
async def analyze_meeting(job_id: str) -> str:
    """Analyze a meeting for quality, clarity, and compliance. Returns a summary report."""
    try:
        # 1. Poll for completion
        status = poll_job(job_id)
        if status != "done":
            return f"Job {job_id} is still {status}. Please wait."
        
        # 2. Get transcript
        transcript = get_transcript(job_id)
        
        # 3. Run multi-agent evaluation
        result = evaluate(transcript, LLM_API_KEY, LLM_MODEL, LLM_PROVIDER)
        
        if not result["success"]:
            return f"Evaluation failed: {result.get('error', 'Unknown error')}"
        
        eval_data = result["evaluation"]
        return (
            f"Analysis Complete for {job_id}\\n"
            f"Overall Score: {eval_data['overall_score']}/100\\n"
            f"Summary: {eval_data['summary']}\\n"
            f"Action Items: {len(eval_data['action_items'])} found."
        )
    except Exception as e:
        return f"Error analyzing meeting: {str(e)}"

@mcp.tool()
async def get_deal_velocity(job_ids: list[str]) -> str:
    """Calculate Deal Velocity across multiple meetings to determine momentum."""
    try:
        evaluations = []
        for jid in job_ids:
            t = get_transcript(jid)
            res = evaluate(t, LLM_API_KEY, LLM_MODEL, LLM_PROVIDER)
            evaluations.append(res)
        
        comparison = compare_evaluations(evaluations, job_ids)
        velocity = comparison["deal_velocity"]
        
        return (
            f"Deal Velocity: {velocity['velocity']} (Score: {velocity['score']})\\n"
            f"Commitment Rate: {velocity['metrics']['commitment_rate']}\\n"
            f"Clarity Slope: {velocity['metrics']['clarity_slope']}"
        )
    except Exception as e:
        return f"Error calculating velocity: {str(e)}"

@mcp.tool()
async def export_meeting_report(job_id: str, target: str) -> str:
    """Export a meeting report to 'notion' or 'slack'."""
    try:
        if target.lower() == "notion":
            res = deliver_report(job_id)
            return f"Exported to Notion: {res.get('page_url', 'Success')}"
        elif target.lower() == "slack":
            res = deliver_slack(job_id)
            return f"Exported to Slack: {res.get('message', 'Success')}"
        else:
            return "Invalid target. Use 'notion' or 'slack'."
    except Exception as e:
        return f"Export failed: {str(e)}"

if __name__ == "__main__":
    mcp.run()
