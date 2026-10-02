"""Multi-language support for CallCoach-AI.

Analyzes calls in different languages and provides coaching in the
user's preferred language.

Usage:
    python multilang.py --demo
"""

import json
import os
import sys
from typing import Any


class MultiLanguageSupport:
    """Multi-language support for call analysis."""

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "hi": "Hindi",
        "ar": "Arabic"
    }

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language

    def analyze_multilang(self, transcript: dict[str, Any], source_language: str = None) -> dict[str, Any]:
        """Analyze a transcript in any language.

        Args:
            transcript: The call transcript
            source_language: The source language (auto-detected if None)

        Returns:
            Analysis results with coaching in target language
        """
        # Detect language if not provided
        if not source_language:
            source_language = self._detect_language(transcript)

        # Analyze the transcript
        from src.core.evaluator import evaluate
        evaluation = evaluate(transcript)

        # Translate coaching prompts to target language
        coaching_prompts = self._translate_coaching_prompts(evaluation, source_language)

        return {
            "source_language": source_language,
            "target_language": self.target_language,
            "evaluation": evaluation,
            "coaching_prompts": coaching_prompts
        }

    def _detect_language(self, transcript: dict[str, Any]) -> str:
        """Detect the language of a transcript."""
        # In production, this would use a language detection library
        # For now, we return a default
        return "en"

    def _translate_coaching_prompts(self, evaluation: dict[str, Any], source_language: str) -> list[dict[str, Any]]:
        """Translate coaching prompts to target language."""
        prompts = []

        # Get coaching prompts from evaluation
        for issue_type in ("action_items", "compliance_risks", "clarity_issues", "tension_signals"):
            for item in evaluation.get(issue_type, []):
                prompt = self._create_coaching_prompt(item, issue_type, source_language)
                if prompt:
                    prompts.append(prompt)

        return prompts

    def _create_coaching_prompt(self, item: dict[str, Any], issue_type: str, source_language: str) -> dict[str, Any] | None:
        """Create a coaching prompt for an issue."""
        text = item.get("text", "") or f"{item.get('text_a', '')} {item.get('text_b', '')}"

        if not text:
            return None

        # Create prompt based on issue type
        if issue_type == "action_items":
            return {
                "type": "action_item",
                "priority": "low",
                "message": self._translate("Action item captured. Confirm owner and deadline.", source_language),
                "original_text": text,
                "timestamp": item.get("start", 0)
            }
        elif issue_type == "compliance_risks":
            return {
                "type": "compliance",
                "priority": "high",
                "message": self._translate("Consider qualifying this commitment.", source_language),
                "original_text": text,
                "timestamp": item.get("start", 0)
            }
        elif issue_type == "clarity_issues":
            return {
                "type": "clarity",
                "priority": "medium",
                "message": self._translate("Try to be more specific.", source_language),
                "original_text": text,
                "timestamp": item.get("start", 0)
            }
        elif issue_type == "tension_signals":
            return {
                "type": "tension",
                "priority": "medium",
                "message": self._translate("Acknowledge the concern.", source_language),
                "original_text": text,
                "timestamp": item.get("start", 0)
            }

        return None

    def _translate(self, text: str, source_language: str) -> str:
        """Translate text to target language."""
        # In production, this would use a translation API
        # For now, we return the original text
        return text

    def get_supported_languages(self) -> dict[str, str]:
        """Get list of supported languages."""
        return self.SUPPORTED_LANGUAGES

    def set_target_language(self, language: str):
        """Set the target language for coaching."""
        if language in self.SUPPORTED_LANGUAGES:
            self.target_language = language
        else:
            raise ValueError(f"Unsupported language: {language}")


def demo_multilang():
    """Demonstrate multi-language support."""
    print("=" * 60)
    print("  CallCoach-AI — Multi-Language Support")
    print("=" * 60)
    print()

    multilang = MultiLanguageSupport(target_language="en")

    print("  Supported Languages:")
    for code, name in multilang.get_supported_languages().items():
        print(f"    {code}: {name}")
    print()

    # Analyze a sample transcript
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.main import load_sample_transcript

    transcript = load_sample_transcript()
    result = multilang.analyze_multilang(transcript, source_language="en")

    print(f"  Source Language: {result['source_language']}")
    print(f"  Target Language: {result['target_language']}")
    print(f"  Coaching Prompts: {len(result['coaching_prompts'])}")
    print()

    print("  Sample Coaching Prompts:")
    for prompt in result['coaching_prompts'][:3]:
        print(f"    [{prompt['priority'].upper()}] {prompt['message']}")
        print(f"      Original: {prompt['original_text'][:50]}...")
        print()


if __name__ == "__main__":
    demo_multilang()
