"""Report generation: produce a Markdown QA report from evaluation results."""

from datetime import datetime


def fmt_time(seconds):
    """Format seconds as M:SS."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def generate_report(evaluation, transcript, job_id=None):
    """Generate a Markdown QA report from evaluation results."""
    lines = []

    # Header
    overall = evaluation.get("overall_score", 0)
    scores = evaluation.get("category_scores", {})
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# Meeting Quality Report")
    lines.append(f"")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Overall Score:** {overall}/100")

    # Category scores
    lines.append(f"\n## Category Scores\n")
    lines.append(f"| Metric | Score |")
    lines.append(f"|---|---|")
    for cat, score in scores.items():
        lines.append(f"| {cat.replace('_', ' ').title()} | {score}/100 |")

    # Top issues
    all_issues = []
    for item in evaluation.get("action_items", []):
        all_issues.append(("Action Item", item))
    for item in evaluation.get("clarity_issues", []):
        all_issues.append(("Clarity", item))
    for item in evaluation.get("tension_signals", []):
        all_issues.append(("Tension", item))
    for item in evaluation.get("compliance_risks", []):
        all_issues.append(("Compliance", item))

    lines.append(f"\n## Top Issues\n")
    if not all_issues:
        lines.append(f"No significant issues detected.")
    else:
        # Sort by category priority: compliance > tension > clarity > action_items
        priority = {"Compliance": 0, "Tension": 1, "Clarity": 2, "Action Item": 3}
        all_issues.sort(key=lambda x: priority.get(x[0], 99))
        for label, item in all_issues[:5]:
            speaker = item.get("speaker") or "UNKNOWN"
            start = item.get("start", 0)
            end = item.get("end", 0)
            text = item.get("text", item.get("text_a", ""))
            issue_desc = item.get("issue", item.get("risk", item.get("signal", "")))

            audio_link = ""
            if job_id:
                audio_link = f" at [{fmt_time(start)} - {fmt_time(end)}](https://whipscribe.com/transcript/{job_id}?t={int(start)})"

            lines.append(f"**{label}** - {speaker}{audio_link}")
            lines.append(f"> {text}")
            if issue_desc:
                lines.append(f"")
                lines.append(f"*{issue_desc}*")
            lines.append(f"")

    # Action items
    ais = evaluation.get("action_items", [])
    lines.append(f"## Action Items ({len(ais)} found)\n")
    if ais:
        for item in ais:
            speaker = item.get("speaker") or "UNKNOWN"
            start = item.get("start", 0)
            text = item.get("text", "")
            owner = item.get("owner", "unspecified")
            deadline = item.get("deadline", "unspecified")
            audio_link = ""
            if job_id:
                audio_link = f" ([at {fmt_time(start)}](https://whipscribe.com/transcript/{job_id}?t={int(start)}))"
            lines.append(f"- **Owner:** {owner} **Deadline:** {deadline}{audio_link}")
            lines.append(f"  {speaker}: \"{text}\"")
    else:
        lines.append(f"No action items detected.")

    lines.append(f"\n---")
    lines.append(f"*Analyzed from WhipScribe transcript.*")

    return "\n".join(lines)


def save_report(content, output_path):
    """Save the report to a file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path
