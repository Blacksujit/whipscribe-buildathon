"""CRM delivery for CallCoach-AI.

Real HubSpot integration via the v3 CRM API (private-app token). Salesforce
support was removed on purpose: its REST tokens expire every couple of hours,
so a one-click connect is impossible - a checkbox that cannot stay green is
worse than an honest limit.

Without a token every call reports the honest "not connected" state; nothing
here invents a record id.
"""

from typing import Any, Dict, List

from src.api.hubspot import deliver_task


class HubSpotIntegration:
    """Thin HubSpot client used by the sync helper and the demo scripts."""

    provider = "hubspot"

    def __init__(self, token: str = "", **kwargs: Any):
        self.token = token or kwargs.get("api_key") or ""

    def create_task(self, subject: str, description: str, due_date: str = None) -> Dict[str, Any]:
        """Create one real HubSpot task, or report why it could not be created."""
        if not self.token:
            return {"created": False, "error": "HubSpot is not connected (no token configured)."}
        try:
            result = deliver_task(
                {"overall_score": 0, "summary": description},
                "crm-task",
                call_name=subject[:80],
                token=self.token,
            )
            return {"created": True, "id": result.get("id")}
        except Exception as exc:  # noqa: BLE001
            return {"created": False, "error": str(exc)}


def sync_call_to_crm(evaluation: dict, transcript: dict, crm: HubSpotIntegration) -> dict:
    """Create one HubSpot task per action item, plus a scorecard summary task."""
    results: Dict[str, List[Dict[str, Any]]] = {
        "tasks_created": [],
        "notes_created": [],
        "records_updated": [],
    }

    for item in evaluation.get("action_items", []):
        task = crm.create_task(
            subject=f"Action item: {item.get('text', '')[:50]}",
            description=item.get("text", ""),
        )
        results["tasks_created"].append(task)

    summary = (
        f"CallCoach-AI score: {evaluation.get('overall_score', 0)}/100\n"
        f"Compliance: {evaluation.get('category_scores', {}).get('compliance', 0)}/100\n"
        f"Action items: {len(evaluation.get('action_items', []))}"
    )
    results["notes_created"].append(crm.create_task(subject="Scorecard summary", description=summary))
    return results


def create_crm_integration(provider: str, **kwargs: Any) -> HubSpotIntegration:
    """Only HubSpot is supported - it is the one that can be verified in one click."""
    if provider.lower() == "hubspot":
        return HubSpotIntegration(**kwargs)
    raise ValueError(
        f"{provider} is not supported. CallCoach-AI ships a real HubSpot integration; "
        "Salesforce needs a connected app whose tokens expire in about two hours."
    )
