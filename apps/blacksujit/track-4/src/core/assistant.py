"""AI coaching assistant for CallCoach-AI.

Provides a conversational interface for coaching questions:
- "How did I do on my last call?"
- "What should I improve?"
- "How does my team compare?"
- "What are my top weaknesses?"

Usage:
    python assistant.py --demo
"""

import json
import os
import sys
from typing import Any


class CoachingAssistant:
    """AI coaching assistant for conversational coaching."""

    def __init__(self):
        self.conversation_history: list[dict[str, str]] = []
        self.context: dict[str, Any] = {}

    def set_context(self, evaluation: dict[str, Any], transcript: dict[str, Any], comparisons: dict[str, Any] = None):
        """Set the context for the coaching assistant.

        Args:
            evaluation: The call evaluation results
            transcript: The call transcript
            comparisons: Optional cross-call comparison data
        """
        self.context = {
            "evaluation": evaluation,
            "transcript": transcript,
            "comparisons": comparisons
        }

    def ask(self, question: str) -> dict[str, Any]:
        """Ask a coaching question.

        Args:
            question: The question to ask

        Returns:
            Answer with coaching insights
        """
        self.conversation_history.append({"role": "user", "content": question})

        # Generate answer based on question
        answer = self._generate_answer(question)

        self.conversation_history.append({"role": "assistant", "content": answer["answer"]})

        return answer

    def _generate_answer(self, question: str) -> dict[str, Any]:
        """Generate an answer to a coaching question."""
        question_lower = question.lower()

        if "how did i do" in question_lower or "how was my call" in question_lower:
            return self._answer_performance_summary()
        elif "what should i improve" in question_lower or "what to improve" in question_lower:
            return self._answer_improvement_suggestions()
        elif "how does my team compare" in question_lower or "team comparison" in question_lower:
            return self._answer_team_comparison()
        elif "what are my weaknesses" in question_lower or "my weaknesses" in question_lower:
            return self._answer_weaknesses()
        elif "what are my strengths" in question_lower or "my strengths" in question_lower:
            return self._answer_strengths()
        elif "action items" in question_lower:
            return self._answer_action_items()
        elif "compliance" in question_lower:
            return self._answer_compliance()
        else:
            return self._answer_general()

    def _answer_performance_summary(self) -> dict[str, Any]:
        """Answer: How did I do on my last call?"""
        evaluation = self.context.get("evaluation", {})
        overall_score = evaluation.get("overall_score", 0)
        category_scores = evaluation.get("category_scores", {})

        answer = f"Your overall score was {overall_score}/100. "

        if overall_score >= 80:
            answer += "Great job! You're performing at a high level. "
        elif overall_score >= 60:
            answer += "Good work, but there's room for improvement. "
        else:
            answer += "There's significant room for improvement. "

        answer += "\n\nCategory breakdown:\n"
        for cat, score in category_scores.items():
            answer += f"- {cat}: {score}/100\n"

        return {
            "question": "How did I do on my last call?",
            "answer": answer,
            "type": "performance_summary",
            "data": {
                "overall_score": overall_score,
                "category_scores": category_scores
            }
        }

    def _answer_improvement_suggestions(self) -> dict[str, Any]:
        """Answer: What should I improve?"""
        evaluation = self.context.get("evaluation", {})
        category_scores = evaluation.get("category_scores", {})

        # Find lowest scoring categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])

        answer = "Here are your top areas for improvement:\n\n"

        for i, (cat, score) in enumerate(sorted_categories[:3], 1):
            if score < 70:
                answer += f"{i}. {cat}: {score}/100\n"
                answer += f"   {self._get_improvement_tip(cat)}\n\n"

        return {
            "question": "What should I improve?",
            "answer": answer,
            "type": "improvement_suggestions",
            "data": {
                "improvement_areas": sorted_categories[:3]
            }
        }

    def _get_improvement_tip(self, category: str) -> str:
        """Get an improvement tip for a category."""
        tips = {
            "compliance": "Practice qualifying commitments instead of making absolute promises.",
            "clarity": "Use concrete numbers and dates instead of vague language.",
            "tension": "Acknowledge concerns before proposing solutions.",
            "action_items": "Use a standard template to capture action items during calls."
        }
        return tips.get(category, "Review best practices for this category.")

    def _answer_team_comparison(self) -> dict[str, Any]:
        """Answer: How does my team compare?"""
        comparisons = self.context.get("comparisons", {})

        if not comparisons:
            return {
                "question": "How does my team compare?",
                "answer": "No team comparison data available. Analyze multiple calls to see team comparisons.",
                "type": "team_comparison",
                "data": None
            }

        answer = "Here's how you compare to your team:\n\n"

        # Add comparison data
        if "trends" in comparisons:
            answer += "Trends:\n"
            for metric, trend in comparisons["trends"].items():
                answer += f"- {metric}: {trend}\n"

        return {
            "question": "How does my team compare?",
            "answer": answer,
            "type": "team_comparison",
            "data": comparisons
        }

    def _answer_weaknesses(self) -> dict[str, Any]:
        """Answer: What are my weaknesses?"""
        evaluation = self.context.get("evaluation", {})
        category_scores = evaluation.get("category_scores", {})

        # Find weaknesses (scores below 70)
        weaknesses = [(cat, score) for cat, score in category_scores.items() if score < 70]
        weaknesses.sort(key=lambda x: x[1])

        if not weaknesses:
            return {
                "question": "What are my weaknesses?",
                "answer": "Great job! No significant weaknesses detected. Keep up the good work!",
                "type": "weaknesses",
                "data": []
            }

        answer = "Here are your main weaknesses:\n\n"

        for i, (cat, score) in enumerate(weaknesses, 1):
            answer += f"{i}. {cat}: {score}/100\n"

        return {
            "question": "What are my weaknesses?",
            "answer": answer,
            "type": "weaknesses",
            "data": weaknesses
        }

    def _answer_strengths(self) -> dict[str, Any]:
        """Answer: What are my strengths?"""
        evaluation = self.context.get("evaluation", {})
        category_scores = evaluation.get("category_scores", {})

        # Find strengths (scores above 80)
        strengths = [(cat, score) for cat, score in category_scores.items() if score >= 80]
        strengths.sort(key=lambda x: x[1], reverse=True)

        if not strengths:
            return {
                "question": "What are my strengths?",
                "answer": "No standout strengths detected yet. Keep working on your skills!",
                "type": "strengths",
                "data": []
            }

        answer = "Here are your main strengths:\n\n"

        for i, (cat, score) in enumerate(strengths, 1):
            answer += f"{i}. {cat}: {score}/100\n"

        return {
            "question": "What are my strengths?",
            "answer": answer,
            "type": "strengths",
            "data": strengths
        }

    def _answer_action_items(self) -> dict[str, Any]:
        """Answer: What are my action items?"""
        evaluation = self.context.get("evaluation", {})
        action_items = evaluation.get("action_items", [])

        if not action_items:
            return {
                "question": "What are my action items?",
                "answer": "No action items were identified in your last call.",
                "type": "action_items",
                "data": []
            }

        answer = f"You have {len(action_items)} action items:\n\n"

        for i, item in enumerate(action_items, 1):
            answer += f"{i}. {item.get('text', '')}\n"
            answer += f"   Speaker: {item.get('speaker', 'Unknown')}\n\n"

        return {
            "question": "What are my action items?",
            "answer": answer,
            "type": "action_items",
            "data": action_items
        }

    def _answer_compliance(self) -> dict[str, Any]:
        """Answer: How did I do on compliance?"""
        evaluation = self.context.get("evaluation", {})
        compliance_score = evaluation.get("category_scores", {}).get("compliance", 0)
        compliance_risks = evaluation.get("compliance_risks", [])

        answer = f"Your compliance score is {compliance_score}/100.\n\n"

        if compliance_risks:
            answer += f"Found {len(compliance_risks)} compliance risks:\n\n"
            for i, risk in enumerate(compliance_risks, 1):
                answer += f"{i}. {risk.get('text', '')}\n"
        else:
            answer += "No compliance risks detected. Great job!"

        return {
            "question": "How did I do on compliance?",
            "answer": answer,
            "type": "compliance",
            "data": {
                "score": compliance_score,
                "risks": compliance_risks
            }
        }

    def _answer_general(self) -> dict[str, Any]:
        """Answer: General question."""
        return {
            "question": "General question",
            "answer": "I can help you with:\n- Performance summary\n- Improvement suggestions\n- Team comparison\n- Strengths and weaknesses\n- Action items\n- Compliance review\n\nWhat would you like to know?",
            "type": "general",
            "data": None
        }

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []


def demo_assistant():
    """Demonstrate the coaching assistant."""
    print("=" * 60)
    print("  CallCoach-AI — AI Coaching Assistant")
    print("=" * 60)
    print()

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.main import load_sample_transcript
    from src.core.evaluator import evaluate

    # Create assistant
    assistant = CoachingAssistant()

    # Set context
    transcript = load_sample_transcript()
    evaluation = evaluate(transcript)
    assistant.set_context(evaluation, transcript)

    # Ask questions
    questions = [
        "How did I do on my last call?",
        "What should I improve?",
        "What are my weaknesses?",
        "What are my strengths?",
        "What are my action items?",
        "How did I do on compliance?"
    ]

    for question in questions:
        print(f"  Q: {question}")
        answer = assistant.ask(question)
        print(f"  A: {answer['answer'][:100]}...")
        print()


if __name__ == "__main__":
    demo_assistant()
