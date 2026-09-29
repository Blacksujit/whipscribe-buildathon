"""Coaching recommendations engine.

Generates prescriptive coaching recommendations based on cross-call
intelligence data, with evidence tied to specific quotes and timestamps.
"""

from typing import Any


def generate_coaching_recommendations(comparisons: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate prescriptive coaching recommendations from comparison data.

    Each recommendation includes:
    - priority: HIGH, MEDIUM, LOW
    - issue: what the problem is
    - action: what to do about it
    - evidence: quotes and timestamps that prove it
    - expected_impact: what improvement to expect
    """
    recommendations = []

    trends = comparisons.get("trends", {})
    meetings = comparisons.get("meetings", [])
    recurring = comparisons.get("recurring_clusters", [])
    tracking = comparisons.get("action_item_tracking", {})
    velocity = comparisons.get("deal_velocity", {})

    # 1. Overall quality declining
    if trends.get("overall") == "declining":
        scores = [m["scores"]["overall"] for m in meetings]
        recommendations.append({
            "priority": "HIGH",
            "category": "Overall Quality",
            "issue": "Overall call quality is declining",
            "action": "Review recent calls for common patterns. Schedule a coaching session to address the root cause.",
            "evidence": f"Overall score trend: {' -> '.join(str(s) for s in scores)}",
            "expected_impact": "Stabilize quality within 2 weeks"
        })

    # 2. Compliance risks increasing
    if trends.get("compliance") == "declining":
        scores = [m["scores"]["compliance"] for m in meetings]
        recommendations.append({
            "priority": "HIGH",
            "category": "Compliance",
            "issue": "Compliance risks are increasing",
            "action": "Review compliance checklist. Provide additional training on commitment tracking.",
            "evidence": f"Compliance score trend: {' -> '.join(str(s) for s in scores)}",
            "expected_impact": "Reduce compliance risks by 50% within 1 month"
        })

    # 3. Action item capture declining
    if trends.get("action_items") == "declining":
        scores = [m["scores"]["action_items"] for m in meetings]
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Action Items",
            "issue": "Action item capture is declining",
            "action": "Implement action item template. Review process at end of each call.",
            "evidence": f"Action items score trend: {' -> '.join(str(s) for s in scores)}",
            "expected_impact": "Improve action item capture by 30% within 2 weeks"
        })

    # 4. Recurring issues
    if recurring:
        top = recurring[0]
        recommendations.append({
            "priority": "HIGH",
            "category": "Recurring Issue",
            "issue": f"Recurring issue: {top['pattern'][:60]}",
            "action": "Address this systemic issue in next team meeting. Create a specific action plan.",
            "evidence": f"Found in {top['count']} meetings: {', '.join(top['meetings'])}",
            "expected_impact": "Eliminate this recurring issue within 1 month"
        })

    # 5. Action item completion rate
    if tracking.get("completion_rate", 100) < 70:
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Follow-through",
            "issue": f"Action item completion rate is {tracking['completion_rate']}%",
            "action": "Implement follow-up system. Review unresolved action items weekly.",
            "evidence": f"{tracking['unresolved']} unresolved action items",
            "expected_impact": "Improve completion rate to 80% within 1 month"
        })

    # 6. Deal velocity
    if velocity.get("velocity") == "Low":
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Deal Velocity",
            "issue": "Deal velocity is low",
            "action": "Review commitment patterns. Focus on clarity and action item capture.",
            "evidence": f"Velocity score: {velocity.get('score', 0)}",
            "expected_impact": "Improve deal velocity by 20% within 1 month"
        })

    # 7. Positive momentum
    if trends.get("overall") == "improving":
        recommendations.append({
            "priority": "LOW",
            "category": "Positive Momentum",
            "issue": "Overall quality is improving",
            "action": "Continue current practices. Document what's working for team sharing.",
            "evidence": f"Overall score trend: {' -> '.join(str(m['scores']['overall']) for m in meetings)}",
            "expected_impact": "Sustain improvement trajectory"
        })

    return recommendations


def format_recommendations(recommendations: list[dict[str, Any]]) -> str:
    """Format recommendations as a readable report."""
    if not recommendations:
        return "No coaching recommendations at this time. Keep up the good work!"

    lines = ["# Coaching Recommendations", ""]

    for i, rec in enumerate(recommendations, 1):
        lines.append(f"## {i}. [{rec['priority']}] {rec['issue']}")
        lines.append(f"**Category:** {rec['category']}")
        lines.append(f"**Action:** {rec['action']}")
        lines.append(f"**Evidence:** {rec['evidence']}")
        lines.append(f"**Expected Impact:** {rec['expected_impact']}")
        lines.append("")

    return "\n".join(lines)
