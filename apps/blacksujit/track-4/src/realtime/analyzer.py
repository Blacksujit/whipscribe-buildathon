"""Real-time speech analyzer for live call coaching.

Analyzes speech segments as they arrive and provides real-time coaching
prompts based on the content, tone, and context of the conversation.
"""

import json
import time
from typing import Any
from collections import deque


class RealtimeAnalyzer:
    """Analyzes speech in real-time and generates coaching prompts.

    Features:
    - Live sentiment analysis
    - Compliance risk detection
    - Action item extraction
    - Clarity scoring
    - Tension detection
    - Coaching prompt generation
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.segments: deque[dict[str, Any]] = deque(maxlen=window_size)
        self.speakers: dict[str, dict[str, Any]] = {}
        self.action_items: list[dict[str, Any]] = []
        self.compliance_risks: list[dict[str, Any]] = []
        self.clarity_issues: list[dict[str, Any]] = []
        self.tension_signals: list[dict[str, Any]] = []
        self.coaching_prompts: list[dict[str, Any]] = []
        self.start_time = time.time()

    def add_segment(self, segment: dict[str, Any]) -> dict[str, Any]:
        """Add a new speech segment and analyze it in real-time.

        Args:
            segment: A speech segment with text, speaker, start, end

        Returns:
            Analysis result with coaching prompts and alerts
        """
        self.segments.append(segment)

        # Update speaker stats
        speaker = segment.get("speaker", "Unknown")
        if speaker not in self.speakers:
            self.speakers[speaker] = {
                "segment_count": 0,
                "total_duration": 0,
                "issues": []
            }
        self.speakers[speaker]["segment_count"] += 1
        self.speakers[speaker]["total_duration"] += segment.get("end", 0) - segment.get("start", 0)

        # Analyze the segment
        analysis = self._analyze_segment(segment)

        # Generate coaching prompts
        prompts = self._generate_coaching_prompts(segment, analysis)

        # Update state
        if analysis.get("action_item"):
            self.action_items.append(analysis["action_item"])
        if analysis.get("compliance_risk"):
            self.compliance_risks.append(analysis["compliance_risk"])
        if analysis.get("clarity_issue"):
            self.clarity_issues.append(analysis["clarity_issue"])
        if analysis.get("tension_signal"):
            self.tension_signals.append(analysis["tension_signal"])
        if prompts:
            self.coaching_prompts.extend(prompts)

        return {
            "segment": segment,
            "analysis": analysis,
            "coaching_prompts": prompts,
            "live_stats": self.get_live_stats()
        }

    def _analyze_segment(self, segment: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single speech segment."""
        text = segment.get("text", "")
        speaker = segment.get("speaker", "Unknown")
        start = segment.get("start", 0)

        analysis = {
            "text": text,
            "speaker": speaker,
            "start": start,
            "sentiment": self._analyze_sentiment(text),
            "action_item": self._extract_action_item(text, speaker, start),
            "compliance_risk": self._detect_compliance_risk(text, speaker, start),
            "clarity_issue": self._detect_clarity_issue(text, speaker, start),
            "tension_signal": self._detect_tension(text, speaker, start)
        }

        return analysis

    def _analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze sentiment of the text."""
        positive_words = ["great", "excellent", "good", "happy", "excited", "love", "best", "awesome"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "poor", "disappointing", "frustrated"]

        text_lower = text.lower()
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)

        if positive_count > negative_count:
            return {"label": "positive", "score": min(1.0, positive_count * 0.2)}
        elif negative_count > positive_count:
            return {"label": "negative", "score": min(1.0, negative_count * 0.2)}
        else:
            return {"label": "neutral", "score": 0.5}

    def _extract_action_item(self, text: str, speaker: str, start: float) -> dict[str, Any] | None:
        """Extract action items from text."""
        action_keywords = ["will", "shall", "promise", "commit", "action", "task", "todo", "follow up", "circle back"]

        text_lower = text.lower()
        if any(kw in text_lower for kw in action_keywords):
            return {
                "text": text,
                "speaker": speaker,
                "start": start,
                "status": "pending"
            }
        return None

    def _detect_compliance_risk(self, text: str, speaker: str, start: float) -> dict[str, Any] | None:
        """Detect compliance risks in text."""
        risk_keywords = ["guarantee", "promise", "assure", "definitely", "certainly", "absolutely", "no doubt"]

        text_lower = text.lower()
        if any(kw in text_lower for kw in risk_keywords):
            return {
                "text": text,
                "speaker": speaker,
                "start": start,
                "risk_level": "medium"
            }
        return None

    def _detect_clarity_issue(self, text: str, speaker: str, start: float) -> dict[str, Any] | None:
        """Detect clarity issues in text."""
        unclear_keywords = ["maybe", "perhaps", "possibly", "might", "could", "not sure", "i think"]

        text_lower = text.lower()
        if any(kw in text_lower for kw in unclear_keywords):
            return {
                "text": text,
                "speaker": speaker,
                "start": start,
                "issue_type": "unclear_language"
            }
        return None

    def _detect_tension(self, text: str, speaker: str, start: float) -> dict[str, Any] | None:
        """Detect tension signals in text."""
        tension_keywords = ["but", "however", "although", "despite", "unfortunately", "problem", "issue", "concern"]

        text_lower = text.lower()
        if any(kw in text_lower for kw in tension_keywords):
            return {
                "text": text,
                "speaker": speaker,
                "start": start,
                "tension_level": "medium"
            }
        return None

    def _generate_coaching_prompts(self, segment: dict[str, Any], analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate coaching prompts based on analysis."""
        prompts = []

        # Compliance risk prompt
        if analysis.get("compliance_risk"):
            prompts.append({
                "type": "compliance",
                "priority": "high",
                "message": "Consider qualifying this commitment. Avoid absolute promises.",
                "timestamp": analysis["start"]
            })

        # Clarity issue prompt
        if analysis.get("clarity_issue"):
            prompts.append({
                "type": "clarity",
                "priority": "medium",
                "message": "Try to be more specific. Use concrete numbers and dates.",
                "timestamp": analysis["start"]
            })

        # Tension signal prompt
        if analysis.get("tension_signal"):
            prompts.append({
                "type": "tension",
                "priority": "medium",
                "message": "Acknowledge the concern and propose a solution.",
                "timestamp": analysis["start"]
            })

        # Action item prompt
        if analysis.get("action_item"):
            prompts.append({
                "type": "action_item",
                "priority": "low",
                "message": "Action item captured. Confirm the owner and deadline.",
                "timestamp": analysis["start"]
            })

        return prompts

    def get_live_stats(self) -> dict[str, Any]:
        """Get live statistics for the current call."""
        elapsed = time.time() - self.start_time

        return {
            "elapsed_time": round(elapsed, 1),
            "segment_count": len(self.segments),
            "speaker_count": len(self.speakers),
            "action_items": len(self.action_items),
            "compliance_risks": len(self.compliance_risks),
            "clarity_issues": len(self.clarity_issues),
            "tension_signals": len(self.tension_signals),
            "coaching_prompts": len(self.coaching_prompts),
            "speakers": {
                name: {
                    "segments": stats["segment_count"],
                    "duration": round(stats["total_duration"], 1)
                }
                for name, stats in self.speakers.items()
            }
        }

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the entire call."""
        return {
            "total_segments": len(self.segments),
            "total_speakers": len(self.speakers),
            "total_duration": round(time.time() - self.start_time, 1),
            "action_items": self.action_items,
            "compliance_risks": self.compliance_risks,
            "clarity_issues": self.clarity_issues,
            "tension_signals": self.tension_signals,
            "coaching_prompts": self.coaching_prompts,
            "speaker_breakdown": {
                name: {
                    "segments": stats["segment_count"],
                    "duration": round(stats["total_duration"], 1)
                }
                for name, stats in self.speakers.items()
            }
        }
