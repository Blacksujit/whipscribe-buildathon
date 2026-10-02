"""Team performance benchmarking for CallCoach-AI.

Aggregates scores across all reps, compares reps against each other,
and identifies top performers and those who need coaching.
"""

import json
from typing import Any
from collections import defaultdict


class TeamBenchmark:
    """Team performance benchmarking and comparison."""

    def __init__(self):
        self.reps: dict[str, dict[str, Any]] = {}
        self.team_averages: dict[str, float] = {}

    def add_rep_data(self, rep_name: str, evaluations: list[dict[str, Any]]):
        """Add evaluation data for a rep.

        Args:
            rep_name: The rep's name
            evaluations: List of evaluation results for this rep
        """
        if not evaluations:
            return

        # Calculate averages
        avg_scores = {}
        for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
            scores = [e.get("category_scores", {}).get(metric, 0) for e in evaluations]
            avg_scores[metric] = sum(scores) / len(scores) if scores else 0

        # Calculate trend
        overall_scores = [e.get("overall_score", 0) for e in evaluations]
        trend = "stable"
        if len(overall_scores) >= 2:
            diff = overall_scores[-1] - overall_scores[0]
            if diff > 4:
                trend = "improving"
            elif diff < -4:
                trend = "declining"

        self.reps[rep_name] = {
            "evaluation_count": len(evaluations),
            "average_scores": avg_scores,
            "trend": trend,
            "overall_average": avg_scores.get("overall", 0)
        }

    def calculate_team_averages(self):
        """Calculate team-wide averages."""
        if not self.reps:
            return

        for metric in ["overall", "action_items", "clarity", "tension", "compliance"]:
            scores = [rep["average_scores"].get(metric, 0) for rep in self.reps.values()]
            self.team_averages[metric] = sum(scores) / len(scores) if scores else 0

    def get_rankings(self) -> list[dict[str, Any]]:
        """Get rep rankings by overall score."""
        self.calculate_team_averages()

        rankings = []
        for rep_name, data in self.reps.items():
            rankings.append({
                "rep_name": rep_name,
                "overall_score": data["overall_average"],
                "trend": data["trend"],
                "evaluation_count": data["evaluation_count"],
                "vs_team_average": data["overall_average"] - self.team_averages.get("overall", 0)
            })

        rankings.sort(key=lambda x: x["overall_score"], reverse=True)
        return rankings

    def get_top_performers(self, n: int = 3) -> list[dict[str, Any]]:
        """Get top N performers."""
        rankings = self.get_rankings()
        return rankings[:n]

    def get_needs_coaching(self, n: int = 3) -> list[dict[str, Any]]:
        """Get reps who need coaching (lowest scores)."""
        rankings = self.get_rankings()
        return rankings[-n:]

    def get_team_summary(self) -> dict[str, Any]:
        """Get team summary statistics."""
        self.calculate_team_averages()

        rankings = self.get_rankings()

        return {
            "team_size": len(self.reps),
            "team_averages": self.team_averages,
            "top_performers": self.get_top_performers(),
            "needs_coaching": self.get_needs_coaching(),
            "rankings": rankings,
            "overall_trend": self._calculate_team_trend()
        }

    def _calculate_team_trend(self) -> str:
        """Calculate overall team trend."""
        if not self.reps:
            return "stable"

        trends = [rep["trend"] for rep in self.reps.values()]
        improving_count = trends.count("improving")
        declining_count = trends.count("declining")

        if improving_count > declining_count:
            return "improving"
        elif declining_count > improving_count:
            return "declining"
        else:
            return "stable"

    def compare_reps(self, rep1: str, rep2: str) -> dict[str, Any]:
        """Compare two reps against each other."""
        if rep1 not in self.reps or rep2 not in self.reps:
            return {"error": "One or both reps not found"}

        r1 = self.reps[rep1]
        r2 = self.reps[rep2]

        comparison = {
            "rep1": rep1,
            "rep2": rep2,
            "overall_diff": r1["overall_average"] - r2["overall_average"],
            "category_diffs": {}
        }

        for metric in ["action_items", "clarity", "tension", "compliance"]:
            diff = r1["average_scores"].get(metric, 0) - r2["average_scores"].get(metric, 0)
            comparison["category_diffs"][metric] = diff

        return comparison

    def generate_benchmark_report(self) -> str:
        """Generate a team benchmark report."""
        summary = self.get_team_summary()

        lines = ["# Team Performance Benchmark Report", ""]

        lines.append(f"## Team Overview")
        lines.append(f"- Team Size: {summary['team_size']}")
        lines.append(f"- Overall Trend: {summary['overall_trend']}")
        lines.append("")

        lines.append("## Team Averages")
        for metric, score in summary["team_averages"].items():
            lines.append(f"- {metric}: {score:.1f}/100")
        lines.append("")

        lines.append("## Top Performers")
        for i, rep in enumerate(summary["top_performers"], 1):
            lines.append(f"{i}. {rep['rep_name']} - {rep['overall_score']:.1f}/100 ({rep['trend']})")
        lines.append("")

        lines.append("## Needs Coaching")
        for i, rep in enumerate(summary["needs_coaching"], 1):
            lines.append(f"{i}. {rep['rep_name']} - {rep['overall_score']:.1f}/100 ({rep['trend']})")
        lines.append("")

        lines.append("## Full Rankings")
        for i, rep in enumerate(summary["rankings"], 1):
            vs_avg = rep["vs_team_average"]
            vs_str = f"+{vs_avg:.1f}" if vs_avg >= 0 else f"{vs_avg:.1f}"
            lines.append(f"{i}. {rep['rep_name']} - {rep['overall_score']:.1f}/100 ({vs_str} vs avg)")

        return "\n".join(lines)


def benchmark_team(rep_evaluations: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Benchmark a team's performance.

    Args:
        rep_evaluations: Dict mapping rep names to their evaluation lists

    Returns:
        Team benchmark summary
    """
    benchmark = TeamBenchmark()

    for rep_name, evaluations in rep_evaluations.items():
        benchmark.add_rep_data(rep_name, evaluations)

    return benchmark.get_team_summary()
