"""Commitment ledger: every promise across calls, deduplicated and aged.

Built from the stored action-item rows and the evaluations that produced
them. Nothing new is invented - repeats are detected by normalising the
text, so "Follow up with the team by Friday" said in two calls shows up as
one commitment with two sightings and its first-seen date.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def build_ledger(action_rows: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Group stored action items into a cross-call commitment ledger."""
    by_job = {e.get("job_id"): e for e in evaluations or []}
    groups: Dict[str, Dict[str, Any]] = {}

    for row in action_rows or []:
        key = _normalize(row.get("text"))[:90]
        if not key:
            continue
        job_id = row.get("job_id") or ""
        evaluation = by_job.get(job_id) or {}
        name = evaluation.get("meeting_name") or job_id[:8]
        date = str(evaluation.get("created_at") or "")[:10]

        entry = groups.setdefault(key, {
            "text": (row.get("text") or "").strip(),
            "owner": row.get("owner") or "unspecified",
            "status": (row.get("status") or "PENDING").upper(),
            "resolved_at": row.get("resolved_at"),
            "seen_in": [],
            "first_seen": None,
        })
        entry["seen_in"].append({"job_id": job_id, "call": name, "date": date})
        if entry["status"] != "RESOLVED" and (row.get("status") or "").upper() == "RESOLVED":
            entry["status"] = "RESOLVED"
            entry["resolved_at"] = row.get("resolved_at")
        if entry["first_seen"] is None or (date and date < entry["first_seen"]["date"]):
            entry["first_seen"] = {"job_id": job_id, "call": name, "date": date}

    now = datetime.now(timezone.utc)
    ledger = []
    for entry in groups.values():
        days_open = None
        first_date = (entry.get("first_seen") or {}).get("date") or ""
        if first_date:
            try:
                seen = datetime.fromisoformat(first_date).replace(tzinfo=timezone.utc)
                days_open = max(0, (now - seen).days)
            except ValueError:
                days_open = None
        ledger.append({
            "text": entry["text"],
            "owner": entry["owner"],
            "open": entry["status"] != "RESOLVED",
            "resolved_at": entry["resolved_at"],
            "times_seen": len(entry["seen_in"]),
            "first_seen": entry["first_seen"],
            "calls": entry["seen_in"][:6],
            "days_open": days_open,
        })

    open_items = sorted(
        [item for item in ledger if item["open"]],
        key=lambda item: (-item["times_seen"], -(item["days_open"] or 0)),
    )
    resolved_items = sorted(
        [item for item in ledger if not item["open"]],
        key=lambda item: item.get("resolved_at") or "",
        reverse=True,
    )
    return {
        "open": open_items[:25],
        "resolved": resolved_items[:25],
        "open_count": len(open_items),
        "resolved_count": len(resolved_items),
        "repeated_count": len([item for item in open_items if item["times_seen"] > 1]),
    }
