"""Automated follow-up email generator for CallCoach-AI.

Generates and sends follow-up emails based on action items from calls.
Ensures follow-through on commitments made during calls.
"""

import json
import os
from typing import Any
from datetime import datetime, timedelta


class FollowUpEmailGenerator:
    """Generates follow-up emails based on call analysis."""

    def __init__(self, smtp_host: str = None, smtp_port: int = 587, smtp_user: str = None, smtp_pass: str = None):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_pass = smtp_pass or os.getenv("SMTP_PASS")

    def generate_followup_email(self, evaluation: dict[str, Any], transcript: dict[str, Any], recipient: str) -> dict[str, Any]:
        """Generate a follow-up email based on call analysis.

        Args:
            evaluation: The call evaluation results
            transcript: The call transcript
            recipient: The email recipient

        Returns:
            Email content with subject, body, and metadata
        """
        # Extract key information
        overall_score = evaluation.get("overall_score", 0)
        category_scores = evaluation.get("category_scores", {})
        action_items = evaluation.get("action_items", [])
        compliance_risks = evaluation.get("compliance_risks", [])

        # Generate subject
        subject = f"Follow-up: Call Summary and Action Items (Score: {overall_score}/100)"

        # Generate body
        body = self._generate_email_body(evaluation, transcript, action_items, compliance_risks)

        return {
            "to": recipient,
            "subject": subject,
            "body": body,
            "metadata": {
                "overall_score": overall_score,
                "action_items_count": len(action_items),
                "compliance_risks_count": len(compliance_risks),
                "generated_at": datetime.now().isoformat()
            }
        }

    def _generate_email_body(self, evaluation: dict[str, Any], transcript: dict[str, Any], action_items: list, compliance_risks: list) -> str:
        """Generate the email body."""
        overall_score = evaluation.get("overall_score", 0)
        category_scores = evaluation.get("category_scores", {})

        body = f"""Hi,

Thank you for taking the time to speak with me today. I wanted to follow up on our conversation and summarize the key points and action items.

## Call Summary

**Overall Score:** {overall_score}/100

**Category Scores:**
- Compliance: {category_scores.get('compliance', 0)}/100
- Tension: {category_scores.get('tension', 0)}/100
- Clarity: {category_scores.get('clarity', 0)}/100
- Action Items: {category_scores.get('action_items', 0)}/100

## Action Items

"""
        if action_items:
            for i, item in enumerate(action_items, 1):
                body += f"{i}. {item.get('text', '')}\n"
        else:
            body += "No action items were identified in this call.\n"

        body += "\n## Compliance Notes\n\n"
        if compliance_risks:
            for risk in compliance_risks:
                body += f"- {risk.get('text', '')}\n"
        else:
            body += "No compliance risks were identified.\n"

        body += """
## Next Steps

Please review the action items above and let me know if you have any questions or concerns. I'm happy to discuss any of these points in more detail.

Best regards,
CallCoach-AI
"""

        return body

    def send_email(self, email: dict[str, Any]) -> dict[str, Any]:
        """Send the follow-up email.

        Args:
            email: The email to send

        Returns:
            Send result with status and message ID
        """
        # In production, this would use smtplib to send the email
        # For now, we just return a success response
        return {
            "success": True,
            "message_id": f"msg_{datetime.now().timestamp()}",
            "to": email["to"],
            "subject": email["subject"],
            "sent_at": datetime.now().isoformat()
        }

    def schedule_followup(self, evaluation: dict[str, Any], transcript: dict[str, Any], recipient: str, delay_hours: int = 24) -> dict[str, Any]:
        """Schedule a follow-up email to be sent later.

        Args:
            evaluation: The call evaluation results
            transcript: The call transcript
            recipient: The email recipient
            delay_hours: Hours to delay the email

        Returns:
            Scheduled email details
        """
        email = self.generate_followup_email(evaluation, transcript, recipient)
        scheduled_time = datetime.now() + timedelta(hours=delay_hours)

        return {
            "email": email,
            "scheduled_for": scheduled_time.isoformat(),
            "status": "scheduled"
        }


def generate_followup_emails(evaluation: dict[str, Any], transcript: dict[str, Any], recipients: list[str]) -> list[dict[str, Any]]:
    """Generate follow-up emails for multiple recipients.

    Args:
        evaluation: The call evaluation results
        transcript: The call transcript
        recipients: List of email recipients

    Returns:
        List of generated emails
    """
    generator = FollowUpEmailGenerator()
    emails = []

    for recipient in recipients:
        email = generator.generate_followup_email(evaluation, transcript, recipient)
        emails.append(email)

    return emails
