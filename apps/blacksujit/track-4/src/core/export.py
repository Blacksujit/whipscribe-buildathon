"""Export functionality for CallCoach-AI.

Export coaching insights to multiple formats:
- Markdown (.md)
- JSON (.json)
- Slack message
- Notion page
- CSV (.csv)

Usage:
    python export.py --format markdown --output report.md
    python export.py --format json --output report.json
    python export.py --format slack
    python export.py --format notion
"""

import argparse
import csv
import json
import os
import sys
from typing import Any


class ExportManager:
    """Manages export of coaching insights to multiple formats."""

    def __init__(self, evaluation: dict[str, Any], transcript: dict[str, Any], comparisons: dict[str, Any] = None):
        self.evaluation = evaluation
        self.transcript = transcript
        self.comparisons = comparisons

    def export_markdown(self) -> str:
        """Export to Markdown format."""
        lines = ["# CallCoach-AI Report", ""]

        # Overall score
        lines.append(f"## Overall Score: {self.evaluation.get('overall_score', 0)}/100")
        lines.append("")

        # Category scores
        lines.append("## Category Scores")
        for cat, score in self.evaluation.get('category_scores', {}).items():
            lines.append(f"- {cat}: {score}/100")
        lines.append("")

        # Action items
        lines.append("## Action Items")
        for item in self.evaluation.get('action_items', []):
            lines.append(f"- {item.get('text', '')} (speaker: {item.get('speaker', 'Unknown')})")
        lines.append("")

        # Compliance risks
        lines.append("## Compliance Risks")
        for risk in self.evaluation.get('compliance_risks', []):
            lines.append(f"- {risk.get('text', '')} (speaker: {risk.get('speaker', 'Unknown')})")
        lines.append("")

        # Cross-call intelligence
        if self.comparisons:
            lines.append("## Cross-Call Intelligence")
            lines.append(f"- Deal Velocity: {self.comparisons.get('deal_velocity', {}).get('velocity', 'N/A')}")
            lines.append(f"- Recurring Issues: {len(self.comparisons.get('recurring_clusters', []))}")
            lines.append(f"- Action Item Completion: {self.comparisons.get('action_item_tracking', {}).get('completion_rate', 0)}%")
            lines.append("")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export to JSON format."""
        data = {
            "evaluation": self.evaluation,
            "transcript": {
                "segments": self.transcript.get("segments", []),
                "speaker_count": len(set(s.get("speaker", "Unknown") for s in self.transcript.get("segments", [])))
            },
            "comparisons": self.comparisons
        }
        return json.dumps(data, indent=2)

    def export_slack(self) -> dict[str, Any]:
        """Export to Slack message format."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "CallCoach-AI Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Overall Score:* {self.evaluation.get('overall_score', 0)}/100"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Category Scores:*\n" + "\n".join(
                        f"• {cat}: {score}/100"
                        for cat, score in self.evaluation.get('category_scores', {}).items()
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Action Items:*\n" + "\n".join(
                        f"• {item.get('text', '')}"
                        for item in self.evaluation.get('action_items', [])
                    )
                }
            }
        ]

        return {
            "blocks": blocks,
            "text": f"CallCoach-AI Report: {self.evaluation.get('overall_score', 0)}/100"
        }

    def export_notion(self) -> dict[str, Any]:
        """Export to Notion page format."""
        return {
            "parent": {
                "database_id": "coaching_reports"
            },
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": f"CallCoach-AI Report - {self.evaluation.get('overall_score', 0)}/100"
                            }
                        }
                    ]
                },
                "Score": {
                    "number": self.evaluation.get('overall_score', 0)
                },
                "Compliance": {
                    "number": self.evaluation.get('category_scores', {}).get('compliance', 0)
                },
                "Clarity": {
                    "number": self.evaluation.get('category_scores', {}).get('clarity', 0)
                },
                "Action Items": {
                    "number": len(self.evaluation.get('action_items', []))
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Action Items"
                                }
                            }
                        ]
                    }
                }
            ] + [
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": item.get('text', '')
                                }
                            }
                        ]
                    }
                }
                for item in self.evaluation.get('action_items', [])
            ]
        }

    def export_csv(self) -> str:
        """Export to CSV format."""
        output = []
        writer = csv.writer(output)

        # Header
        writer.writerow(["Type", "Text", "Speaker", "Start", "End"])

        # Action items
        for item in self.evaluation.get('action_items', []):
            writer.writerow([
                "Action Item",
                item.get('text', ''),
                item.get('speaker', 'Unknown'),
                item.get('start', 0),
                item.get('end', 0)
            ])

        # Compliance risks
        for risk in self.evaluation.get('compliance_risks', []):
            writer.writerow([
                "Compliance Risk",
                risk.get('text', ''),
                risk.get('speaker', 'Unknown'),
                risk.get('start', 0),
                risk.get('end', 0)
            ])

        return "\n".join(output)

    def export(self, format: str, output_path: str = None) -> str:
        """Export to the specified format.

        Args:
            format: The export format (markdown, json, slack, notion, csv)
            output_path: The output file path (optional)

        Returns:
            The exported content
        """
        if format == "markdown":
            content = self.export_markdown()
        elif format == "json":
            content = self.export_json()
        elif format == "slack":
            content = json.dumps(self.export_slack(), indent=2)
        elif format == "notion":
            content = json.dumps(self.export_notion(), indent=2)
        elif format == "csv":
            content = self.export_csv()
        else:
            raise ValueError(f"Unsupported format: {format}")

        if output_path:
            with open(output_path, "w") as f:
                f.write(content)
            print(f"  Exported to: {output_path}")

        return content


def main():
    parser = argparse.ArgumentParser(description="Export CallCoach-AI insights")
    parser.add_argument("--format", choices=["markdown", "json", "slack", "notion", "csv"], required=True)
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")

    args = parser.parse_args()

    if args.demo:
        # Run demo with sample data
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from src.main import load_sample_transcript
        from src.core.evaluator import evaluate

        transcript = load_sample_transcript()
        evaluation = evaluate(transcript)

        exporter = ExportManager(evaluation, transcript)
        content = exporter.export(args.format, args.output)

        if not args.output:
            print(content)
    else:
        print("  Use --demo flag to run with sample data")


if __name__ == "__main__":
    main()
