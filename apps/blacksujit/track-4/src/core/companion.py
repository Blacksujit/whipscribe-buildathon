"""Griot - the grounded call companion.

Answers questions from the stored call evaluations only. Uses the configured
LLM (via the same call_llm used by the four scoring agents) when a key is
present; otherwise degrades to a data-derived summary over the same stored
rows. Nothing here is invented: every quote comes from a real evaluation row.
"""

import json
import re
from typing import Any


def _fmt_time(seconds: float) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        total = 0
    return f"{total // 60}:{total % 60:02d}"


def _core_eval(evaluation: Any) -> dict[str, Any]:
    if not isinstance(evaluation, dict):
        return {}
    inner = evaluation.get("evaluation")
    return inner if isinstance(inner, dict) else evaluation


def build_evidence(evaluations: list[dict], job_id: str | None = None, max_calls: int = 8) -> dict[str, Any]:
    """Compact evidence from stored rows, newest first."""
    rows = evaluations or []
    if job_id:
        rows = [row for row in rows if row.get("job_id") == job_id]
    rows = rows[:max_calls]

    calls = []
    for row in rows:
        raw = row.get("evaluation")
        core = _core_eval(json.loads(raw) if isinstance(raw, str) else raw)

        issues = []
        for kind, key in (
            ("compliance", "compliance_risks"),
            ("tension", "tension_signals"),
            ("clarity", "clarity_issues"),
        ):
            for item in core.get(key, []) or []:
                text = (item.get("text") or item.get("text_a") or "").strip()
                if not text:
                    continue
                issues.append({
                    "kind": kind,
                    "text": text,
                    "speaker": item.get("speaker") or item.get("speaker_a") or "Unknown",
                    "start": item.get("start", 0),
                })

        items = []
        for item in core.get("action_items", []) or []:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            items.append({
                "text": text,
                "speaker": item.get("speaker") or "Unknown",
                "start": item.get("start", 0),
            })

        calls.append({
            "job_id": row.get("job_id"),
            "name": row.get("meeting_name") or (row.get("job_id") or "")[:8],
            "created_at": str(row.get("created_at") or ""),
            "overall_score": core.get("overall_score", 0),
            "category_scores": core.get("category_scores", {}) or {},
            "summary": (core.get("summary") or "").strip(),
            "issues": issues[:12],
            "action_items": items[:8],
        })

    return {"calls": calls}


def render_evidence_text(evidence: dict[str, Any]) -> str:
    lines = []
    for call in evidence.get("calls", []):
        lines.append(f"## {call['name']} (job {call['job_id']}) - score {call['overall_score']}/100")
        if call.get("summary"):
            lines.append(call["summary"])
        cats = call.get("category_scores") or {}
        if cats:
            lines.append("categories: " + ", ".join(f"{k} {v}" for k, v in cats.items()))
        for issue in call.get("issues", []):
            lines.append(f'- {issue["kind"]} @ {_fmt_time(issue["start"])} ({issue["speaker"]}): "{issue["text"]}"')
        for item in call.get("action_items", []):
            lines.append(f'- commitment @ {_fmt_time(item["start"])} ({item["speaker"]}): "{item["text"]}"')
        lines.append("")
    return "\n".join(lines)


SYSTEM_PROMPT = (
    "You are Griot, the grounded companion inside CallCoach-AI (a call-scoring tool). "
    "Answer ONLY from the EVIDENCE block - these are real scored calls from the user's account. "
    "Cite claims as [Call name @ m:ss - Speaker]. "
    "If the evidence does not contain the answer, say exactly what is missing. "
    "Never invent calls, quotes, numbers, or timestamps. Keep answers under 130 words."
)


def local_citations(question: str, evaluations: list[dict], job_id: str | None = None,
                    limit: int = 8) -> list[dict[str, Any]]:
    """Local index: keyword search over the stored transcripts' segments.

    Same citation shape as the WhipScribe MCP retrieval, so the UI renders
    both identically: {job_id, meeting_name, speaker, start, end, quote}.
    """
    from src.api.whip_mcp import query_terms

    terms = query_terms(question)
    if not terms:
        return []
    hits = []
    for row in evaluations or []:
        if job_id and row.get("job_id") != job_id:
            continue
        transcript = row.get("transcript")
        if isinstance(transcript, str):
            try:
                transcript = json.loads(transcript)
            except (ValueError, TypeError):
                transcript = {}
        for seg in (transcript or {}).get("segments", []) or []:
            text = (seg.get("text") or "").strip()
            low = text.lower()
            score = sum(1 for t in terms if t in low)
            if not score:
                continue
            hits.append((score, {
                "job_id": row.get("job_id"),
                "meeting_name": row.get("meeting_name") or (row.get("job_id") or "")[:8],
                "speaker": seg.get("speaker"),
                "start": round(float(seg.get("start") or 0), 2),
                "end": round(float(seg["end"]), 2) if seg.get("end") is not None else None,
                "quote": text[:280],
            }))
    hits.sort(key=lambda h: -h[0])
    return [h[1] for h in hits[:limit]]


def render_citations_text(citations: list[dict[str, Any]], source: str) -> str:
    if not citations:
        return ""
    lines = [f"TRANSCRIPT MATCHES (retrieved from {source}; exact words said on the call):"]
    for c in citations:
        lines.append(
            f'- {c.get("meeting_name")} @ {_fmt_time(c.get("start") or 0)} '
            f'({c.get("speaker") or "Unknown"}): "{c.get("quote")}"'
        )
    return "\n".join(lines)


def ask(question: str, evidence: dict[str, Any], provider: str | None = None,
        api_key: str | None = None, model: str | None = None,
        citations: list[dict[str, Any]] | None = None, source: str = "local-index") -> dict[str, Any]:
    """Answer a question over the evidence; LLM when possible, data-derived otherwise.

    ``citations`` are transcript sentences retrieved for this question (from
    the WhipScribe MCP search or the local index) and are given to the model
    alongside the stored scorecards.
    """
    citations = citations or []
    if not evidence.get("calls") and not citations:
        return {
            "answer": "No scored calls yet. Open a recording on the home page and run the analysis first - then I can answer from it.",
            "mode": "empty",
            "sources": [],
        }

    if provider and api_key:
        try:
            from src.core.evaluator import call_llm

            matches = render_citations_text(citations, source)
            prompt = (
                f"{SYSTEM_PROMPT}\n\nEVIDENCE:\n{render_evidence_text(evidence)}\n\n"
                + (f"{matches}\n\n" if matches else "")
                + f"QUESTION: {question}\n\nANSWER:"
            )
            answer = call_llm(provider, api_key, model, prompt)
            return {"answer": answer.strip(), "mode": "llm", "sources": _extract_sources(answer, evidence)}
        except Exception as exc:  # noqa: BLE001
            result = _data_answer(question, evidence, citations)
            result["note"] = f"LLM unavailable ({type(exc).__name__}); answered from the stored data."
            return result

    return _data_answer(question, evidence, citations)


def _fold(text: str) -> str:
    """Lowercase and strip everything outside a-z0-9.

    Model output often swaps hyphens/apostrophes for lookalikes (non-breaking
    hyphen, curly quote), which would otherwise break name matching.
    """
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _extract_sources(answer: str, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Match cited call names back to stored issues so the UI can deep-link."""
    sources = []
    answer_folded = _fold(answer)
    seen = set()
    for call in evidence.get("calls", []):
        name = call.get("name") or ""
        if name and _fold(name) in answer_folded:
            for issue in call.get("issues", [])[:2]:
                key = (call["job_id"], issue["start"], issue["text"][:40])
                if key in seen:
                    continue
                seen.add(key)
                sources.append({
                    "job_id": call["job_id"],
                    "call": name,
                    "speaker": issue["speaker"],
                    "start": issue["start"],
                    "text": issue["text"][:140],
                })
    return sources[:6]


def _data_answer(question: str, evidence: dict[str, Any],
                 citations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Honest data-derived answer when no LLM key is configured."""
    q = question.lower()
    calls = evidence.get("calls", [])
    lines: list[str] = []

    if citations:
        lines.append("Where this comes up on your calls:")
        for c in citations[:6]:
            lines.append(
                f'- {c.get("meeting_name")} @ {_fmt_time(c.get("start") or 0)} '
                f'({c.get("speaker") or "Unknown"}): "{c.get("quote")}"'
            )
        return {"answer": "\n".join(lines), "mode": "data", "sources": []}

    if any(word in q for word in ("commit", "promise", "action", "follow")):
        lines.append("Commitments found across scored calls:")
        for call in calls:
            for item in call.get("action_items", [])[:3]:
                lines.append(f'- {call["name"]} @ {_fmt_time(item["start"])} ({item["speaker"]}): "{item["text"]}"')
    elif any(word in q for word in ("weak", "improve", "lose", "risk")):
        lines.append("Lowest categories across scored calls:")
        for call in calls:
            cats = call.get("category_scores") or {}
            if not cats:
                continue
            name, score = min(cats.items(), key=lambda kv: kv[1])
            lines.append(f"- {call['name']}: {name} {score}/100 (overall {call['overall_score']})")
    elif any(word in q for word in ("score", "how did", "last call")):
        latest = calls[0]
        cats = ", ".join(f"{k} {v}" for k, v in (latest.get("category_scores") or {}).items())
        lines.append(f"Latest scored call: {latest['name']} - {latest['overall_score']}/100 ({cats}).")
        if latest.get("summary"):
            lines.append(latest["summary"])
    else:
        lines.append(f"I can read {len(calls)} scored calls right now:")
        for call in calls[:8]:
            lines.append(f"- {call['name']}: {call['overall_score']}/100")
        lines.append("")
        lines.append("Try: 'What did we commit to?', 'What are my weaknesses?', 'How did my last call score?'")

    return {"answer": "\n".join(lines), "mode": "data", "sources": []}
