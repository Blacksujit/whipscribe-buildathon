"""Automated coaching plans for CallCoach-AI.

Generates personalized coaching plans for each rep based on their
specific weaknesses and strengths, with actionable steps and timelines.

Usage:
    python coaching_plan.py --demo
"""

import json
import os
import sys
from typing import Any
from datetime import datetime, timedelta


class CoachingPlanGenerator:
    """Generates personalized coaching plans for reps."""

    def __init__(self):
        self.plans: dict[str, dict[str, Any]] = {}

    def generate_plan(self, rep_name: str, evaluations: list[dict[str, Any]], comparisons: dict[str, Any] = None) -> dict[str, Any]:
        """Generate a personalized coaching plan for a rep.

        Args:
            rep_name: The rep's name
            evaluations: List of evaluation results for this rep
            comparisons: Optional cross-call comparison data

        Returns:
            Personalized coaching plan
        """
        if not evaluations:
            return {"error": "No evaluations provided"}

        # Calculate average scores
        avg_scores = {}
        for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
            scores = [e.get("category_scores", {}).get(metric, 0) for e in evaluations]
            avg_scores[metric] = sum(scores) / len(scores) if scores else 0

        # Identify weaknesses (scores below 70)
        weaknesses = []
        for metric, score in avg_scores.items():
            if score < 70 and metric != "overall":
                weaknesses.append({
                    "metric": metric,
                    "score": score,
                    "gap": 70 - score
                })

        # Sort weaknesses by gap (largest first)
        weaknesses.sort(key=lambda x: x["gap"], reverse=True)

        # Generate action items
        action_items = []
        for weakness in weaknesses:
            action_items.extend(self._generate_actions_for_weakness(weakness))

        # Generate timeline
        timeline = self._generate_timeline(action_items)

        # Create plan
        plan = {
            "rep_name": rep_name,
            "created_at": datetime.now().isoformat(),
            "average_scores": avg_scores,
            "weaknesses": weaknesses,
            "action_items": action_items,
            "timeline": timeline,
            "goals": self._generate_goals(weaknesses),
            "success_metrics": self._generate_success_metrics(weaknesses)
        }

        self.plans[rep_name] = plan
        return plan

    def _generate_actions_for_weakness(self, weakness: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate action items for a specific weakness."""
        metric = weakness["metric"]
        score = weakness["score"]

        actions = {
            "compliance": [
                {
                    "action": "Review compliance checklist",
                    "description": "Go through the compliance checklist and identify areas for improvement",
                    "duration": "30 minutes",
                    "frequency": "Weekly"
                },
                {
                    "action": "Practice qualifying commitments",
                    "description": "Practice making qualified commitments instead of absolute promises",
                    "duration": "15 minutes",
                    "frequency": "Daily"
                },
                {
                    "action": "Shadow top performer",
                    "description": "Listen to a top performer's calls and note their compliance practices",
                    "duration": "1 hour",
                    "frequency": "Bi-weekly"
                }
            ],
            "clarity": [
                {
                    "action": "Use concrete numbers and dates",
                    "description": "Replace vague language with specific numbers and dates",
                    "duration": "15 minutes",
                    "frequency": "Daily"
                },
                {
                    "action": "Practice elevator pitch",
                    "description": "Practice a clear, concise elevator pitch",
                    "duration": "30 minutes",
                    "frequency": "Weekly"
                },
                {
                    "action": "Record and review",
                    "description": "Record practice calls and review for clarity",
                    "duration": "1 hour",
                    "frequency": "Weekly"
                }
            ],
            "tension": [
                {
                    "action": "Acknowledge concerns",
                    "description": "Practice acknowledging concerns before proposing solutions",
                    "duration": "15 minutes",
                    "frequency": "Daily"
                },
                {
                    "action": "Use positive framing",
                    "description": "Frame negative news in a positive context",
                    "duration": "15 minutes",
                    "frequency": "Daily"
                },
                {
                    "action": "Role-play difficult conversations",
                    "description": "Practice difficult conversations with a colleague",
                    "duration": "1 hour",
                    "frequency": "Bi-weekly"
                }
            ],
            "action_items": [
                {
                    "action": "Use action item template",
                    "description": "Use a standard template to capture action items during calls",
                    "duration": "5 minutes",
                    "frequency": "Every call"
                },
                {
                    "action": "Confirm owner and deadline",
                    "description": "Always confirm the owner and deadline for each action item",
                    "duration": "2 minutes",
                    "frequency": "Every call"
                },
                {
                    "action": "Follow up on action items",
                    "description": "Follow up on action items within 24 hours",
                    "duration": "10 minutes",
                    "frequency": "Daily"
                }
            ]
        }

        return actions.get(metric, [])

    def _generate_timeline(self, action_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate a timeline for the coaching plan."""
        timeline = []
        start_date = datetime.now()

        for i, item in enumerate(action_items):
            week = (i // 3) + 1
            timeline.append({
                "week": week,
                "action": item["action"],
                "duration": item["duration"],
                "frequency": item["frequency"],
                "start_date": (start_date + timedelta(weeks=week-1)).isoformat(),
                "status": "pending"
            })

        return timeline

    def _generate_goals(self, weaknesses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate goals based on weaknesses."""
        goals = []

        for weakness in weaknesses:
            goals.append({
                "metric": weakness["metric"],
                "current_score": weakness["score"],
                "target_score": 70,
                "deadline": (datetime.now() + timedelta(weeks=4)).isoformat(),
                "status": "in_progress"
            })

        return goals

    def _generate_success_metrics(self, weaknesses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate success metrics for the coaching plan."""
        metrics = []

        for weakness in weaknesses:
            metrics.append({
                "metric": weakness["metric"],
                "current": weakness["score"],
                "target": 70,
                "measurement": "score improvement",
                "frequency": "weekly"
            })

        return metrics

    def get_plan(self, rep_name: str) -> dict[str, Any] | None:
        """Get a coaching plan for a rep."""
        return self.plans.get(rep_name)

    def generate_plan_report(self, rep_name: str) -> str:
        """Generate a readable coaching plan report."""
        plan = self.get_plan(rep_name)
        if not plan:
            return f"No coaching plan found for {rep_name}"

        lines = [f"# Coaching Plan: {rep_name}", ""]

        lines.append("## Average Scores")
        for metric, score in plan["average_scores"].items():
            lines.append(f"- {metric}: {score:.1f}/100")
        lines.append("")

        lines.append("## Weaknesses")
        for weakness in plan["weaknesses"]:
            lines.append(f"- {weakness['metric']}: {weakness['score']:.1f}/100 (gap: {weakness['gap']:.1f})")
        lines.append("")

        lines.append("## Action Items")
        for i, item in enumerate(plan["action_items"], 1):
            lines.append(f"{i}. {item['action']}")
            lines.append(f"   {item['description']}")
            lines.append(f"   Duration: {item['duration']} | Frequency: {item['frequency']}")
            lines.append("")

        lines.append("## Goals")
        for goal in plan["goals"]:
            lines.append(f"- {goal['metric']}: {goal['current_score']:.1f} -> {goal['target_score']:.1f} by {goal['deadline'][:10]}")
        lines.append("")

        return "\n".join(lines)


def demo_coaching_plan():
    """Demonstrate coaching plan generation."""
    print("=" * 60)
    print("  CallCoach-AI — Automated Coaching Plans")
    print("=" * 60)
    print()

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.main import load_sample_transcript, make_sample_variation
    from src.core.evaluator import evaluate

    generator = CoachingPlanGenerator()

    # Generate plans for multiple reps
    reps = ["Sarah", "Mike", "Priya"]

    for rep_name in reps:
        print(f"  Generating coaching plan for {rep_name}...")

        # Generate sample evaluations
        evaluations = []
        for name in ["Q4 Planning", "Retro", "Sales Call"]:
            t = make_sample_variation(load_sample_transcript(), name)
            e = evaluate(t)
            evaluations.append(e)

        plan = generator.generate_plan(rep_name, evaluations)

        print(f"    Average Score: {plan['average_scores']['overall']:.1f}/100")
        print(f"    Weaknesses: {len(plan['weaknesses'])}")
        print(f"    Action Items: {len(plan['action_items'])}")
        print(f"    Goals: {len(plan['goals'])}")
        print()

    # Generate report for first rep
    print("  Coaching Plan Report (Sarah):")
    print(generator.generate_plan_report("Sarah"))


if __name__ == "__main__":
    demo_coaching_plan()
