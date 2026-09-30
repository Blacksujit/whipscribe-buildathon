"""Multi-meeting trend analysis and comparison.

This module analyzes quality trends across multiple meetings to provide
coaching insights and performance tracking.

Architecture:
  - Depends ONLY on the evaluation data contract (dict shape).
  - Does NOT import whip_api, reporter, or notion  no external dependencies.
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
from functools import lru_cache
from difflib import SequenceMatcher
import numpy as np


def _core_eval(eval_data: dict) -> dict:
    """Return the inner evaluation dict whether the input is wrapped or flat.

    Accepts either {"success": ..., "evaluation": {...}} (LLM pipeline output)
    or a bare evaluation dict (rows already unwrapped by the store / callers).
    """
    if not isinstance(eval_data, dict):
        return {}
    inner = eval_data.get("evaluation")
    return inner if isinstance(inner, dict) else eval_data


def _calculate_deal_velocity(evaluations: list[dict]) -> dict[str, Any]:
    """
    Calculates Deal Velocity using a grounded mathematical model:
    Velocity = (Commitment Rate * Clarity Slope) / (1 + Tension Variance)
    """
    if not evaluations:
        return {"velocity": "N/A", "score": 0, "trend": "Stable"}

    # 1. Commitment Rate: Action items per meeting
    total_items = sum(len(_core_eval(e).get("action_items", [])) for e in evaluations)
    commitment_rate = total_items / len(evaluations)

    # 2. Clarity Slope: Linear regression of clarity scores
    clarity_scores = [_core_eval(e).get("category_scores", {}).get("clarity", 50) for e in evaluations]
    if len(clarity_scores) > 1:
        x = np.arange(len(clarity_scores))
        slope = np.polyfit(x, clarity_scores, 1)[0]
    else:
        slope = 0

    # 3. Tension Variance: Stability of emotional state
    tension_scores = [_core_eval(e).get("category_scores", {}).get("tension", 50) for e in evaluations]
    variance = np.var(tension_scores) if len(tension_scores) > 1 else 0

    # Calculate Final Velocity
    norm_slope = max(0, slope) / 10.0
    norm_variance = variance / 100.0
    velocity_score = (commitment_rate * (1 + norm_slope)) / (1 + norm_variance)
    
    if velocity_score > 3: label = "High"
    elif velocity_score > 1.5: label = "Moderate"
    else: label = "Low"

    return {
        "velocity": label,
        "score": round(velocity_score, 2),
        "metrics": {
            "commitment_rate": round(commitment_rate, 2),
            "clarity_slope": round(slope, 2),
            "tension_variance": round(variance, 2)
        }
    }

def compare_evaluations(
    evaluations: list[dict[str, Any]],
    names: list[str],
    dates: list[str] | None = None,
) -> dict[str, Any]:
    """Compare multiple meeting evaluations and produce trend analysis."""
    if dates is None:
        from datetime import date, timedelta
        base = date.today()
        dates = [(base - timedelta(days=len(evaluations) - 1 - i)).isoformat()
                 for i in range(len(evaluations))]

    meetings: list[dict[str, Any]] = []
    for i, (eval_data, name) in enumerate(zip(evaluations, names)):
        core = _core_eval(eval_data)
        scores = core.get("category_scores", {})
        meeting = {
            "name": name,
            "date": dates[i],
            "scores": {
                "overall": int(core.get("overall_score", 0) or 0),
                "action_items": int(scores.get("action_items", 0) or 0),
                "clarity": int(scores.get("clarity", 0) or 0),
                "tension": int(scores.get("tension", 0) or 0),
                "compliance": int(scores.get("compliance", 0) or 0),
            },
            "issues": _collect_all_issues(eval_data)[:60],
        }
        meetings.append(meeting)

    meetings.sort(key=lambda m: m["date"])

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

    common_issues = _find_common_issues(meetings)
    recurring_clusters = _cluster_recurring_issues(meetings)
    action_tracking = _track_action_items(meetings)
    speaker_analysis = _analyze_speaker_patterns(evaluations, names)
    insights = _generate_insights(meetings, trends, common_issues, action_tracking, recurring_clusters)

    return {
        "meetings": meetings,
        "trends": trends,
        "common_issues": common_issues,
        "recurring_clusters": recurring_clusters,
        "action_item_tracking": action_tracking,
        "speaker_analysis": speaker_analysis,
        "insights": insights,
        "deal_velocity": _calculate_deal_velocity(evaluations),
    }

def _collect_all_issues(eval_data: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    # Support both raw evaluation and wrapped evaluation
    data = _core_eval(eval_data)
    for issue_type in ("clarity_issues", "tension_signals", "compliance_risks", "action_items"):
        for item in data.get(issue_type, []):
            issue = {"type": issue_type}
            issue.update(item)
            issues.append(issue)
    return issues

def _normalize_text(text: str) -> str:
    return text.lower().strip()[:60]

@lru_cache(maxsize=50000)
def _fuzzy_match(text1: str, text2: str, threshold: float = 0.7) -> bool:
    a, b = text1[:140].lower(), text2[:140].lower()
    if not a or not b:
        return False
    longest = max(len(a), len(b))
    if abs(len(a) - len(b)) > 0.35 * longest:
        # SequenceMatcher ratio cannot reach the threshold from this length gap.
        return False
    tokens_a, tokens_b = set(a.split()), set(b.split())
    if tokens_a and tokens_b and not (tokens_a & tokens_b):
        # No shared vocabulary at all: the ratio stays near zero.
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold

def _find_common_issues(meetings: list[dict]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for meeting in meetings:
        for issue in meeting["issues"]:
            text = _normalize_text(issue.get("text", "") or
                                   issue.get("text_a", "") + " " +
                                   issue.get("text_b", ""))
            if not text: continue
            key = f"{issue['type']}:{text}"
            if key not in groups:
                groups[key] = {
                    "type": issue["type"],
                    "text": issue.get("text", "") or f"{issue.get('text_a','')} / {issue.get('text_b','')}",
                    "count": 0,
                    "meetings": [],
                }
            groups[key]["count"] += 1
            if meeting["name"] not in groups[key]["meetings"]:
                groups[key]["meetings"].append(meeting["name"])
    result = [v for v in groups.values() if v["count"] >= 2]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result

def _cluster_recurring_issues(meetings: list[dict]) -> list[dict[str, Any]]:
    all_issues: list[dict[str, Any]] = []
    seen_keys = set()
    for meeting in meetings:
        for issue in meeting["issues"]:
            text = issue.get("text", "") or f"{issue.get('text_a','')} / {issue.get('text_b','')}"
            if not text:
                continue
            # Exact repeats collapse first: the fuzzy pass only compares distinct variants.
            key = f"{issue['type']}:{_normalize_text(text)}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            all_issues.append({"type": issue["type"], "text": text, "meeting": meeting["name"], "date": meeting["date"]})

    # The clustering pass is pairwise; bound it so a long recording cannot stall a request.
    all_issues = all_issues[:150]

    clusters: list[dict[str, Any]] = []
    used_indices = set()
    for i, issue1 in enumerate(all_issues):
        if i in used_indices: continue
        cluster = {"type": issue1["type"], "pattern": issue1["text"], "count": 1, "meetings": [issue1["meeting"]], "variations": [issue1["text"]]}
        used_indices.add(i)
        for j, issue2 in enumerate(all_issues):
            if j <= i or j in used_indices: continue
            if issue1["type"] != issue2["type"]: continue
            if _fuzzy_match(issue1["text"], issue2["text"], threshold=0.6):
                cluster["count"] += 1
                if issue2["meeting"] not in cluster["meetings"]: cluster["meetings"].append(issue2["meeting"])
                if issue2["text"] not in cluster["variations"]: cluster["variations"].append(issue2["text"])
                used_indices.add(j)
        if cluster["count"] >= 2: clusters.append(cluster)
    clusters.sort(key=lambda x: x["count"], reverse=True)
    return clusters

def _track_action_items(meetings: list[dict]) -> dict[str, Any]:
    all_items: list[dict[str, Any]] = []
    for meeting in meetings:
        for issue in meeting["issues"]:
            if issue["type"] == "action_items":
                all_items.append({"text": issue.get("text", ""), "from": meeting["name"], "date": meeting["date"]})
    resolved = 0
    unresolved: list[dict[str, Any]] = []
    last_index: dict[str, int] = {}
    for index, item in enumerate(all_items):
        last_index[_normalize_text(item["text"])] = index
    for i, item in enumerate(all_items):
        normalized = _normalize_text(item["text"])
        # Resolved when the same commitment never appears again later in the history.
        if last_index.get(normalized, i) <= i:
            resolved += 1
        else:
            unresolved.append(item)
    total = len(all_items)
    completion_rate = round((resolved / total) * 100, 1) if total else 0.0
    return {"total": total, "resolved": resolved, "unresolved": unresolved, "completion_rate": completion_rate}

def _generate_insights(meetings, trends, common_issues, action_tracking, recurring_clusters) -> list[str]:
    insights = []
    if trends.get("overall") == "improving": insights.append("Overall meeting quality is trending upwards.")
    if trends.get("overall") == "declining": insights.append("Warning: Overall meeting quality is declining.")
    if common_issues: insights.append(f"Recurring pattern detected: {common_issues[0]['text']} appearing in multiple calls.")
    if recurring_clusters: insights.append(f"Cluster found: {recurring_clusters[0]['pattern']} is a systemic issue.")
    if action_tracking["resolved"] > 0: insights.append(f"Positive momentum: {action_tracking['resolved']} action items resolved.")
    return insights

def _analyze_speaker_patterns(evaluations: list[dict], names: list[str]) -> dict[str, Any]:
    speaker_stats = {}
    for eval_data in evaluations:
        data = _core_eval(eval_data)
        for issue_type in ("clarity_issues", "tension_signals", "compliance_risks"):
            for issue in data.get(issue_type, []):
                speaker = issue.get("speaker", "Unknown")
                if speaker not in speaker_stats: speaker_stats[speaker] = {"count": 0, "types": set()}
                speaker_stats[speaker]["count"] += 1
                speaker_stats[speaker]["types"].add(issue_type)
    return speaker_stats

def generate_comparison_report(comparisons: dict[str, Any]) -> str:
    lines = ["# Meeting Intelligence Comparison Report", ""]
    lines.append(f"## Deal Velocity: {comparisons['deal_velocity']['velocity']} (Score: {comparisons['deal_velocity']['score']})")
    lines.append("\n### Metrics")
    for k, v in comparisons['deal_velocity']['metrics'].items():
        lines.append(f"- {k.replace('_', ' ').title()}: {v}")
    lines.append("\n## Trends")
    for m, t in comparisons['trends'].items():
        lines.append(f"- {m.title()}: {t}")
    return "\n".join(lines)

def save_comparison_report(report: str, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
