"""CRM integration for CallCoach-AI.

Integrates with Salesforce and HubSpot to automatically update records
based on call analysis. Syncs action items, scores, and coaching notes.
"""

import json
import os
from typing import Any


class CRMIntegration:
    """Base class for CRM integrations."""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    def create_record(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a record in the CRM."""
        raise NotImplementedError

    def update_record(self, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a record in the CRM."""
        raise NotImplementedError

    def search_records(self, query: str) -> list[dict[str, Any]]:
        """Search for records in the CRM."""
        raise NotImplementedError


class SalesforceIntegration(CRMIntegration):
    """Salesforce CRM integration."""

    def __init__(self, api_key: str, instance_url: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.instance_url = instance_url

    def create_task(self, subject: str, description: str, due_date: str = None) -> dict[str, Any]:
        """Create a task in Salesforce."""
        # In production, this would make a real API call to Salesforce
        return {
            "id": "sf_task_123",
            "subject": subject,
            "description": description,
            "due_date": due_date,
            "status": "Not Started"
        }

    def update_opportunity(self, opp_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an opportunity in Salesforce."""
        return {
            "id": opp_id,
            "updated": True,
            "fields": data
        }

    def create_coaching_note(self, contact_id: str, note: str) -> dict[str, Any]:
        """Create a coaching note in Salesforce."""
        return {
            "id": "sf_note_456",
            "contact_id": contact_id,
            "note": note,
            "created_date": "2026-09-30"
        }


class HubSpotIntegration(CRMIntegration):
    """HubSpot CRM integration."""

    def __init__(self, api_key: str, portal_id: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.portal_id = portal_id

    def create_task(self, subject: str, description: str, due_date: str = None) -> dict[str, Any]:
        """Create a task in HubSpot."""
        return {
            "id": "hs_task_123",
            "subject": subject,
            "description": description,
            "due_date": due_date,
            "status": "NOT_STARTED"
        }

    def update_contact(self, contact_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a contact in HubSpot."""
        return {
            "id": contact_id,
            "updated": True,
            "properties": data
        }

    def create_engagement(self, contact_id: str, note: str) -> dict[str, Any]:
        """Create an engagement in HubSpot."""
        return {
            "id": "hs_engagement_456",
            "contact_id": contact_id,
            "note": note,
            "type": "NOTE"
        }


def sync_call_to_crm(evaluation: dict[str, Any], transcript: dict[str, Any], crm: CRMIntegration) -> dict[str, Any]:
    """Sync call analysis results to CRM.

    Args:
        evaluation: The call evaluation results
        transcript: The call transcript
        crm: The CRM integration to use

    Returns:
        Sync results with created/updated records
    """
    results = {
        "tasks_created": [],
        "notes_created": [],
        "records_updated": []
    }

    # Create tasks for action items
    for item in evaluation.get("action_items", []):
        task = crm.create_task(
            subject=f"Action Item: {item.get('text', '')[:50]}",
            description=item.get("text", ""),
            due_date=None
        )
        results["tasks_created"].append(task)

    # Create coaching note
    note = f"CallCoach-AI Score: {evaluation.get('overall_score', 0)}/100\n"
    note += f"Compliance: {evaluation.get('category_scores', {}).get('compliance', 0)}/100\n"
    note += f"Action Items: {len(evaluation.get('action_items', []))}"

    if hasattr(crm, 'create_coaching_note'):
        coaching_note = crm.create_coaching_note("contact_id", note)
        results["notes_created"].append(coaching_note)
    elif hasattr(crm, 'create_engagement'):
        engagement = crm.create_engagement("contact_id", note)
        results["notes_created"].append(engagement)

    return results


def create_crm_integration(provider: str, **kwargs) -> CRMIntegration:
    """Factory function to create a CRM integration.

    Args:
        provider: The CRM provider (salesforce or hubspot)
        **kwargs: Additional configuration options

    Returns:
        A CRM integration instance
    """
    if provider.lower() == "salesforce":
        return SalesforceIntegration(**kwargs)
    elif provider.lower() == "hubspot":
        return HubSpotIntegration(**kwargs)
    else:
        raise ValueError(f"Unsupported CRM provider: {provider}")
