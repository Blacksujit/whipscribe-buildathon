"""Sentiment analysis over time for CallCoach-AI.

Tracks sentiment trends across multiple calls, identifies patterns,
and provides coaching recommendations based on sentiment.

Usage:
    python sentiment.py --demo
"""

import json
import os
import sys
from typing import Any
from collections import defaultdict


class SentimentTracker:
    """Tracks sentiment trends across multiple calls."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []
        self.sentiment_history: list[dict[str, Any]] = []

    def add_call(self, call_name: str, segments: list[dict[str, Any]]):
        """Add a call with its sentiment data.

        Args:
            call_name: The call name
            segments: List of segments with sentiment data
        """
        sentiments = []
        for segment in segments:
            sentiment = self._analyze_sentiment(segment.get("text", ""))
            sentiments.append({
                "text": segment.get("text", ""),
                "speaker": segment.get("speaker", "Unknown"),
                "start": segment.get("start", 0),
                "sentiment": sentiment
            })

        self.calls.append({
            "name": call_name,
            "segments": sentiments,
            "overall_sentiment": self._calculate_overall_sentiment(sentiments)
        })

    def _analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze sentiment of text."""
        positive_words = ["great", "excellent", "good", "happy", "excited", "love", "best", "awesome", "fantastic", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "poor", "disappointing", "frustrated", "angry", "upset"]

        text_lower = text.lower()
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)

        if positive_count > negative_count:
            return {"label": "positive", "score": min(1.0, positive_count * 0.2)}
        elif negative_count > positive_count:
            return {"label": "negative", "score": min(1.0, negative_count * 0.2)}
        else:
            return {"label": "neutral", "score": 0.5}

    def _calculate_overall_sentiment(self, sentiments: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate overall sentiment for a call."""
        if not sentiments:
            return {"label": "neutral", "score": 0.5}

        scores = [s["sentiment"]["score"] for s in sentiments]
        avg_score = sum(scores) / len(scores)

        if avg_score > 0.6:
            label = "positive"
        elif avg_score < 0.4:
            label = "negative"
        else:
            label = "neutral"

        return {"label": label, "score": round(avg_score, 2)}

    def get_sentiment_trend(self) -> dict[str, Any]:
        """Get sentiment trend across all calls."""
        if not self.calls:
            return {"trend": "insufficient_data", "calls": []}

        sentiments = [c["overall_sentiment"]["score"] for c in self.calls]

        if len(sentiments) < 2:
            trend = "insufficient_data"
        else:
            diff = sentiments[-1] - sentiments[0]
            if diff > 0.1:
                trend = "improving"
            elif diff < -0.1:
                trend = "declining"
            else:
                trend = "stable"

        return {
            "trend": trend,
            "calls": [
                {
                    "name": c["name"],
                    "sentiment": c["overall_sentiment"]["label"],
                    "score": c["overall_sentiment"]["score"]
                }
                for c in self.calls
            ],
            "average_score": round(sum(sentiments) / len(sentiments), 2) if sentiments else 0
        }

    def get_sentiment_by_speaker(self) -> dict[str, Any]:
        """Get sentiment breakdown by speaker."""
        speaker_sentiments = defaultdict(list)

        for call in self.calls:
            for segment in call["segments"]:
                speaker = segment["speaker"]
                speaker_sentiments[speaker].append(segment["sentiment"]["score"])

        result = {}
        for speaker, scores in speaker_sentiments.items():
            avg = sum(scores) / len(scores) if scores else 0
            result[speaker] = {
                "average_score": round(avg, 2),
                "segment_count": len(scores),
                "label": "positive" if avg > 0.6 else "negative" if avg < 0.4 else "neutral"
            }

        return result

    def get_sentiment_patterns(self) -> list[dict[str, Any]]:
        """Identify sentiment patterns across calls."""
        patterns = []

        # Check for improving trend
        trend = self.get_sentiment_trend()
        if trend["trend"] == "improving":
            patterns.append({
                "type": "improving_sentiment",
                "description": "Sentiment is improving across calls",
                "recommendation": "Continue current practices"
            })
        elif trend["trend"] == "declining":
            patterns.append({
                "type": "declining_sentiment",
                "description": "Sentiment is declining across calls",
                "recommendation": "Investigate root causes and address concerns"
            })

        # Check for speaker-specific patterns
        speaker_sentiments = self.get_sentiment_by_speaker()
        for speaker, data in speaker_sentiments.items():
            if data["label"] == "negative":
                patterns.append({
                    "type": "negative_speaker",
                    "speaker": speaker,
                    "description": f"{speaker} has consistently negative sentiment",
                    "recommendation": f"Schedule coaching session with {speaker}"
                })

        return patterns

    def generate_sentiment_report(self) -> str:
        """Generate a sentiment analysis report."""
        trend = self.get_sentiment_trend()
        speaker_sentiments = self.get_sentiment_by_speaker()
        patterns = self.get_sentiment_patterns()

        lines = ["# Sentiment Analysis Report", ""]

        lines.append("## Overall Trend")
        lines.append(f"- Trend: {trend['trend']}")
        lines.append(f"- Average Score: {trend['average_score']}")
        lines.append("")

        lines.append("## Sentiment by Call")
        for call in trend["calls"]:
            lines.append(f"- {call['name']}: {call['sentiment']} ({call['score']})")
        lines.append("")

        lines.append("## Sentiment by Speaker")
        for speaker, data in speaker_sentiments.items():
            lines.append(f"- {speaker}: {data['label']} ({data['average_score']})")
        lines.append("")

        lines.append("## Patterns")
        for pattern in patterns:
            lines.append(f"- {pattern['type']}: {pattern['description']}")
            lines.append(f"  Recommendation: {pattern['recommendation']}")
        lines.append("")

        return "\n".join(lines)


def demo_sentiment_analysis():
    """Demonstrate sentiment analysis over time."""
    print("=" * 60)
    print("  CallCoach-AI — Sentiment Analysis Over Time")
    print("=" * 60)
    print()

    tracker = SentimentTracker()

    # Add sample calls
    calls = [
        ("Q4 Planning", [
            {"text": "I think we should launch in November.", "speaker": "Sarah", "start": 0},
            {"text": "The engineering team isn't ready yet.", "speaker": "Priya", "start": 5},
            {"text": "We'll definitely deliver by Q1.", "speaker": "Mike", "start": 10},
        ]),
        ("Retro", [
            {"text": "I'm frustrated that we missed the deadline.", "speaker": "Sarah", "start": 0},
            {"text": "The timeline was unrealistic.", "speaker": "Mike", "start": 5},
            {"text": "We need to improve our planning.", "speaker": "Priya", "start": 10},
        ]),
        ("Sales Call", [
            {"text": "I'm super excited about this partnership!", "speaker": "Mike", "start": 0},
            {"text": "This is a great opportunity for us.", "speaker": "Sarah", "start": 5},
            {"text": "I love the direction we're heading.", "speaker": "Priya", "start": 10},
        ]),
    ]

    for call_name, segments in calls:
        tracker.add_call(call_name, segments)

    # Get trend
    print("  Sentiment Trend:")
    trend = tracker.get_sentiment_trend()
    print(f"    Trend: {trend['trend']}")
    print(f"    Average Score: {trend['average_score']}")
    print()

    # Get speaker sentiments
    print("  Sentiment by Speaker:")
    speaker_sentiments = tracker.get_sentiment_by_speaker()
    for speaker, data in speaker_sentiments.items():
        print(f"    {speaker}: {data['label']} ({data['average_score']})")
    print()

    # Get patterns
    print("  Patterns:")
    patterns = tracker.get_sentiment_patterns()
    for pattern in patterns:
        print(f"    - {pattern['type']}: {pattern['description']}")
    print()

    # Generate report
    print("  Report:")
    report = tracker.generate_sentiment_report()
    print(report)


if __name__ == "__main__":
    demo_sentiment_analysis()
