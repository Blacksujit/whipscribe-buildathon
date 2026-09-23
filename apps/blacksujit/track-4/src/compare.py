"""Multi-meeting trend analysis and comparison.

This module analyzes quality trends across multiple meetings to provide
coaching insights and performance tracking.

Architecture:
  - Depends ONLY on the evaluation data contract (dict shape).
  - Does NOT import whip_api, reporter, or notion — no external dependencies.
  - Functions are pure: same input always produces same output.
  - Designed to be callable both from CLI and web service.

Data contract (evaluation dict shape):
  {
    "overall_score": int,
    "category_scores": {"action_items": int, "clarity": int,
                        "tension": int, "compliance": int},
    "action_items": [{"text": str, "start": float, ...}],
    "clarity_issues": [{"text": str, "speaker": str, ...}],
    "tension_signals": [{"text_a": str, "text_b": str, ...}],
    "compliance_risks": [{"text": str, "speaker": str, ...}],
  }
"""

import copy
import time
from typing import Any
from difflib import SequenceMatcher


def compare_evaluations(
    evaluations: list[dict[str, Any]],
    names: list[str],
    dates: list[str] | None = None,
) -> dict[str, Any]:
    """Compare multiple meeting evaluations and produce trend analysis.

    Args:
        evaluations: List of evaluation result dicts (from evaluator.evaluate).
        names: Descriptive names for each meeting (e.g. "Q4 Planning #1").
        dates: Optional list of ISO date strings (YYYY-MM-DD).
            Defaults to sequential dates.

    Returns:
        Dict with: meetings, trends, common_issues, action_item_tracking, insights.
    """
    if dates is None:
        from datetime import date, timedelta
        base = date.today()
        dates = [(base - timedelta(days=len(evaluations) - 1 - i)).isoformat()
                 for i in range(len(evaluations))]

    # --- Build per-meeting summary ---
    meetings: list[dict[str, Any]] = []
    for i, (eval_data, name) in enumerate(zip(evaluations, names)):
        scores = eval_data.get("category_scores", {})
        meeting = {
            "name": name,
            "date": dates[i],
            "scores": {
                "overall": eval_data.get("overall_score", 0),
                "action_items": scores.get("action_items", 0),
                "clarity": scores.get("clarity", 0),
                "tension": scores.get("tension", 0),
                "compliance": scores.get("compliance", 0),
            },
            "issues": _collect_all_issues(eval_data),
        }
        meetings.append(meeting)

    # Sort by date so trends are chronological
    meetings.sort(key=lambda m: m["date"])

    # --- Trend analysis (simple linear slope per metric) ---
    metrics = ["overall", "action_items", "clarity", "tension", "compliance"]
    trends: dict[str, str] = {}
    for metric in metrics:
        scores = [m["scores"][metric] for m in meetings]
        if len(scores) < 2:
            trends[metric] = "insufficient_data"
            continue
        slope = scores[-1] - scores[0]
        if slope > 4:
            trends[metric] = "improving"
        elif slope < -4:
            trends[metric] = "declining"
        else:
            trends[metric] = "stable"

    # --- Common issues across meetings ---
    common_issues = _find_common_issues(meetings)
    
    # --- Advanced recurring issue clustering ---
    recurring_clusters = _cluster_recurring_issues(meetings)

    # --- Action item tracking ---
    action_tracking = _track_action_items(meetings)
    
    # --- Advanced recurring issue clustering ---
    recurring_clusters = _cluster_recurring_issues(meetings)
    
    # --- Speaker analysis (team vs individual patterns) ---
    speaker_analysis = _analyze_speaker_patterns(evaluations, names)

    # --- Human-readable insights ---
    insights = _generate_insights(meetings, trends, common_issues, action_tracking, recurring_clusters)

    return {
        "meetings": meetings,
        "trends": trends,
        "common_issues": common_issues,
        "recurring_clusters": recurring_clusters,
        "action_item_tracking": action_tracking,
        "speaker_analysis": speaker_analysis,
        "insights": insights,
    }


def _collect_all_issues(eval_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract all issues from an evaluation dict into a flat list with type tags."""
    issues: list[dict[str, Any]] = []
    for issue_type in ("clarity_issues", "tension_signals",
                       "compliance_risks", "action_items"):
        for item in eval_data.get(issue_type, []):
            issue = {"type": issue_type}
            issue.update(item)
            issues.append(issue)
    return issues


def _normalize_text(text: str) -> str:
    """Normalize issue text for grouping (lowercase, strip, first 60 chars)."""
    return text.lower().strip()[:60]


def _fuzzy_match(text1: str, text2: str, threshold: float = 0.7) -> bool:
    """Check if two texts are similar using fuzzy matching."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() >= threshold


def _find_common_issues(meetings: list[dict]) -> list[dict[str, Any]]:
    """Find issues that appear in more than one meeting, ranked by frequency."""
    groups: dict[str, dict[str, Any]] = {}
    for meeting in meetings:
        for issue in meeting["issues"]:
            text = _normalize_text(issue.get("text", "") or
                                   issue.get("text_a", "") + " " +
                                   issue.get("text_b", ""))
            if not text:
                continue
            key = f"{issue['type']}:{text}"
            if key not in groups:
                groups[key] = {
                    "type": issue["type"],
                    "text": issue.get("text", "") or
                            f"{issue.get('text_a','')} / {issue.get('text_b','')}",
                    "count": 0,
                    "meetings": [],
                }
            groups[key]["count"] += 1
            if meeting["name"] not in groups[key]["meetings"]:
                groups[key]["meetings"].append(meeting["name"])

    # Only keep issues that appear in 2+ meetings
    result = [v for v in groups.values() if v["count"] >= 2]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result


def _cluster_recurring_issues(meetings: list[dict]) -> list[dict[str, Any]]:
    """Advanced clustering of similar issues using fuzzy matching.
    
    This goes beyond exact text matching to find patterns like:
    - "I think we should launch" vs "I believe we should launch"
    - "Not sure about timeline" vs "Uncertain about schedule"
    """
    all_issues: list[dict[str, Any]] = []
    for meeting in meetings:
        for issue in meeting["issues"]:
            text = issue.get("text", "") or f"{issue.get('text_a','')} / {issue.get('text_b','')}"
            if text:
                all_issues.append({
                    "type": issue["type"],
                    "text": text,
                    "meeting": meeting["name"],
                    "date": meeting["date"],
                })
    
    clusters: list[dict[str, Any]] = []
    used_indices = set()
    
    for i, issue1 in enumerate(all_issues):
        if i in used_indices:
            continue
            
        cluster = {
            "type": issue1["type"],
            "pattern": issue1["text"],
            "count": 1,
            "meetings": [issue1["meeting"]],
            "variations": [issue1["text"]],
        }
        used_indices.add(i)
        
        # Find similar issues
        for j, issue2 in enumerate(all_issues):
            if j <= i or j in used_indices:
                continue
            if issue1["type"] != issue2["type"]:
                continue
                
            if _fuzzy_match(issue1["text"], issue2["text"], threshold=0.6):
                cluster["count"] += 1
                if issue2["meeting"] not in cluster["meetings"]:
                    cluster["meetings"].append(issue2["meeting"])
                if issue2["text"] not in cluster["variations"]:
                    cluster["variations"].append(issue2["text"])
                used_indices.add(j)
        
        if cluster["count"] >= 2:
            clusters.append(cluster)
    
    clusters.sort(key=lambda x: x["count"], reverse=True)
    return clusters


def _track_action_items(meetings: list[dict]) -> dict[str, Any]:
    """Track action items across meetings.

    Heuristic: if an action item's text (normalized) from meeting N
    does not appear in the issues of meeting N+1, it is considered
    resolved. If it does appear again, it is still open.
    """
    all_items: list[dict[str, Any]] = []
    for meeting in meetings:
        for issue in meeting["issues"]:
            if issue["type"] == "action_items":
                all_items.append({
                    "text": issue.get("text", ""),
                    "from": meeting["name"],
                    "date": meeting["date"],
                })

    resolved = 0
    unresolved: list[dict[str, Any]] = []
    for i, item in enumerate(all_items):
        normalized = _normalize_text(item["text"])
        is_resolved = True
        # Check if the same action item appears in subsequent meetings
        for later in all_items[i + 1:]:
            if _normalize_text(later["text"]) == normalized:
                is_resolved = False
                break
        if is_resolved:
            resolved += 1
        else:
            unresolved.append(item)

    total = len(all_items)
    return {
        "total": total,
        "resolved": resolved,
        "completion_rate": round(resolved / total * 100) if total > 0 else 0,
        "unresolved": unresolved,
    }


def _generate_insights(
    meetings: list[dict],
    trends: dict[str, str],
    common_issues: list[dict],
    action_tracking: dict,
    recurring_clusters: list[dict],
) -> list[str]:
    """Generate human-readable insights from the comparison data."""
    insights: list[str] = []

    if len(meetings) >= 2:
        first = meetings[0]["scores"]["overall"]
        last = meetings[-1]["scores"]["overall"]
        delta = last - first
        if delta < -4:
            insights.append(
                f"Overall quality declined from {first} to {last} "
                f"({delta:+d}) over {len(meetings)} meetings - investigate root cause."
            )
        elif delta > 4:
            insights.append(
                f"Overall quality improved from {first} to {last} "
                f"({delta:+d}) over {len(meetings)} meetings - "
                f"identify what worked."
            )
        else:
            insights.append(
                f"Overall quality is stable at {last} across "
                f"{len(meetings)} meetings."
            )

    # Insight: compliance risk patterns
    compliance_issues = [i for i in common_issues if i["type"] == "compliance_risks"]
    if compliance_issues:
        insights.append(
            f"{len(compliance_issues)} compliance risk type(s) recurred across "
            f"multiple meetings - add to team playbook."
        )

    # Insight: action item completion
    if action_tracking["total"] > 0:
        rate = action_tracking["completion_rate"]
        if rate < 50:
            insights.append(
                f"Action item completion rate is {rate}% - too many items "
                f"slip through. Try assigning owners explicitly."
            )
        elif rate < 100:
            insights.append(
                f"Action item completion rate improved to {rate}% - "
                f"good progress, keep it up."
            )
        else:
            insights.append(
                f"All action items ({action_tracking['total']}) resolved - "
                f"excellent follow-through."
            )

    # Insight: clarity declining
    if trends.get("clarity") == "declining":
        insights.append(
            "Clarity scores are declining - reps may be rushed or unprepared."
        )
    
    # Insight: recurring issue clusters (new feature)
    if recurring_clusters:
        top_cluster = recurring_clusters[0]
        insights.append(
            f"Pattern detected: '{top_cluster['pattern'][:50]}...' "
            f"appears {top_cluster['count']} times across {len(top_cluster['meetings'])} meetings."
        )

    return insights


def _analyze_speaker_patterns(evaluations: list[dict], names: list[str]) -> dict[str, Any]:
    """Analyze speaker-specific patterns across meetings.
    
    This identifies which speakers contribute to quality issues:
    - Who creates compliance risks most often?
    - Who tends to use unclear language?
    - Who generates the most action items?
    """
    speaker_stats: dict[str, dict[str, Any]] = {}
    
    for eval_data, meeting_name in zip(evaluations, names):
        for issue_type in ("clarity_issues", "tension_signals", 
                          "compliance_risks", "action_items"):
            for item in eval_data.get(issue_type, []):
                speaker = item.get("speaker", "Unknown")
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {
                        "meetings": set(),
                        "clarity_count": 0,
                        "tension_count": 0,
                        "compliance_count": 0,
                        "action_count": 0,
                    }
                
                speaker_stats[speaker]["meetings"].add(meeting_name)
                
                if issue_type == "clarity_issues":
                    speaker_stats[speaker]["clarity_count"] += 1
                elif issue_type == "tension_signals":
                    speaker_stats[speaker]["tension_count"] += 1
                elif issue_type == "compliance_risks":
                    speaker_stats[speaker]["compliance_count"] += 1
                elif issue_type == "action_items":
                    speaker_stats[speaker]["action_count"] += 1
    
    # Convert sets to counts and identify patterns
    results = []
    for speaker, stats in speaker_stats.items():
        results.append({
            "speaker": speaker,
            "meetings": len(stats["meetings"]),
            "clarity_count": stats["clarity_count"],
            "tension_count": stats["tension_count"],
            "compliance_count": stats["compliance_count"],
            "action_count": stats["action_count"],
            "risk_score": (
                stats["compliance_count"] * 3 + 
                stats["tension_count"] * 2 + 
                stats["clarity_count"]
            )  # Weighted risk score
        })
    
    # Sort by risk score
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return {
        "speakers": results,
        "high_risk_speakers": [s for s in results if s["risk_score"] >= 3],
        "top_action_generators": sorted(results, key=lambda x: x["action_count"], reverse=True)[:3],
    }


def make_sample_variation(base_transcript, name):
    """Create a slightly different sample transcript for comparison demos.

    Each variation has different quality characteristics so the
    comparison produces meaningful trends.
    """
    variation = copy.deepcopy(base_transcript)

    if "Retro" in name:
        for seg in variation.get("segments", []):
            text = seg.get("text", "")
            if "I think we should launch" in text:
                seg["text"] = text.replace(
                    "I think we should launch in November.",
                    "I am frustrated that we missed the October deadline again."
                )
            if "Let me circle back" in text:
                seg["text"] = "We will figure it out eventually"

    elif "Sales" in name:
        for seg in variation.get("segments", []):
            text = seg.get("text", "")
            if "Good morning" in text:
                seg["text"] = "Good morning! I am super excited about this partnership!"

    return variation


def generate_comparison_report(comparisons: dict[str, Any]) -> str:
    """Generate a Markdown comparison report from comparison data."""
    lines: list[str] = []
    meetings = comparisons["meetings"]

    lines.append("# Multi-Meeting Quality Comparison Report")
    lines.append("")
    lines.append("## Trend Summary")
    lines.append("")
    lines.append("| Metric | " + " | ".join(m["name"] for m in meetings) + " | Trend |")
    lines.append("|---|" + "|".join(["---"] * len(meetings)) + "||---|")

    metrics = ["overall", "action_items", "clarity", "tension", "compliance"]
    metric_labels = {"overall": "Overall", "action_items": "Action Items",
                     "clarity": "Clarity", "tension": "Tension", "compliance": "Compliance"}
    for metric in metrics:
        scores = [str(m["scores"][metric]) for m in meetings]
        trend = comparisons["trends"].get(metric, "stable")
        lines.append(f"| {metric_labels[metric]} | " + " | ".join(scores) + f" | {trend} |")

    lines.append("")
    lines.append("## Key Insights")
    lines.append("")
    for insight in comparisons["insights"]:
        lines.append(f"- {insight}")
    lines.append("")

    # Common issues
    common = comparisons["common_issues"]
    if common:
        lines.append("## Recurring Issues (across multiple meetings)")
        lines.append("")
        lines.append("| Issue | Type | Meetings | Count |")
        lines.append("|---|---|---|---|")
        for issue in common:
            short_text = (issue.get("text", "") or "")[:70]
            if len(short_text) > 67:
                short_text = short_text[:67] + "..."
            lines.append(
                f"| {short_text} | {issue['type']} | "
                f"{', '.join(issue['meetings'])} | {issue['count']} |"
            )
        lines.append("")
    
    # Advanced recurring issue clusters (new feature)
    clusters = comparisons.get("recurring_clusters", [])
    if clusters:
        lines.append("## Pattern Clusters (Advanced Analysis)")
        lines.append("")
        lines.append("Using fuzzy matching to detect similar issues across meetings:")
        lines.append("")
        for cluster in clusters[:3]:  # Show top 3 clusters
            lines.append(f"### Pattern: {cluster['pattern'][:60]}...")
            lines.append(f"- **Frequency**: {cluster['count']} occurrences")
            lines.append(f"- **Meetings**: {', '.join(cluster['meetings'])}")
            lines.append(f"- **Variations detected**: {len(cluster['variations'])}")
            lines.append("")

    # Speaker analysis (new feature)
    speaker_analysis = comparisons.get("speaker_analysis", {})
    if speaker_analysis.get("speakers"):
        lines.append("## Speaker Performance Analysis")
        lines.append("")
        lines.append("Individual speaker contribution to meeting quality:")
        lines.append("")
        lines.append("| Speaker | Meetings | Compliance Risks | Tension | Clarity Issues | Action Items | Risk Score |")
        lines.append("|---|---|---|---|---|---|---|")
        for speaker in speaker_analysis["speakers"][:5]:  # Top 5 speakers
            lines.append(
                f"| {speaker['speaker']} | {speaker['meetings']} | "
                f"{speaker['compliance_count']} | {speaker['tension_count']} | "
                f"{speaker['clarity_count']} | {speaker['action_count']} | "
                f"{speaker['risk_score']} |"
            )
        lines.append("")
        
        if speaker_analysis.get("high_risk_speakers"):
            lines.append("### High-Risk Speakers (requiring coaching)")
            lines.append("")
            for speaker in speaker_analysis["high_risk_speakers"]:
                lines.append(f"- **{speaker['speaker']}**: Risk score {speaker['risk_score']} - "
                            f"compliance: {speaker['compliance_count']}, tension: {speaker['tension_count']}")
            lines.append("")

    # Action item tracking
    tracking = comparisons["action_item_tracking"]
    lines.append("## Action Item Tracking")
    lines.append("")
    lines.append(f"- **Total items**: {tracking['total']}")
    lines.append(f"- **Resolved**: {tracking['resolved']}")
    lines.append(f"- **Completion rate**: {tracking['completion_rate']}%")
    if tracking["unresolved"]:
        lines.append(f"- **Still open**: {len(tracking['unresolved'])}")
        lines.append("")
        for item in tracking["unresolved"]:
            lines.append(f"  - {item['text'][:80]}... (from: {item['from']})")
    lines.append("")

    # Per-meeting detail
    lines.append("## Meeting Details")
    lines.append("")
    for meeting in meetings:
        lines.append(f"### {meeting['name']} ({meeting['date']})")
        scores = meeting["scores"]
        lines.append(f"- Overall: {scores['overall']}/100")
        lines.append(f"- Action Items: {scores['action_items']}/100")
        lines.append(f"- Clarity: {scores['clarity']}/100")
        lines.append(f"- Tension: {scores['tension']}/100")
        lines.append(f"- Compliance: {scores['compliance']}/100")
        lines.append("")

    lines.append("---")
    lines.append("*Analyzed from WhipScribe transcripts with advanced pattern detection.*")

    return "\n".join(lines)


def save_comparison_report(report: str, output_path: str) -> None:
    """Save a comparison report to a file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


__all__ = [
    "compare_evaluations",
    "generate_comparison_report",
    "save_comparison_report",
]
