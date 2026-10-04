"""Conversation dynamics: who really held the room.

Pure functions over the diarized segments WhipScribe already returns - no
extra API calls, no model calls. Every number comes from real timestamps:
talk share, overlapping speech, thinking pauses, questions, and the longest
monologue per speaker.
"""

from typing import Any, Dict, List


def _fmt(seconds: float) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        total = 0
    return f"{total // 60}:{total % 60:02d}"


def analyze_dynamics(transcript: Dict[str, Any]) -> Dict[str, Any]:
    """Compute conversation dynamics from a diarized transcript."""
    segments = [s for s in (transcript or {}).get("segments", []) or [] if (s.get("text") or "").strip()]
    if not segments:
        return {}

    by_speaker: Dict[str, Dict[str, Any]] = {}
    silences: List[Dict[str, Any]] = []
    total_talk = 0.0
    prev = None

    for segment in segments:
        speaker = segment.get("speaker") or "Unknown"
        try:
            start = float(segment.get("start") or 0)
            end = float(segment.get("end") or start)
        except (TypeError, ValueError):
            start, end = 0.0, 0.0
        duration = max(0.0, end - start)
        text = (segment.get("text") or "").strip()

        stats = by_speaker.setdefault(speaker, {
            "talk_seconds": 0.0,
            "segments": 0,
            "questions": 0,
            "overlaps": 0,
            "longest_seconds": 0.0,
            "longest_text": "",
            "longest_start": 0.0,
        })
        stats["talk_seconds"] += duration
        stats["segments"] += 1
        total_talk += duration
        if text.endswith("?"):
            stats["questions"] += 1
        if duration > stats["longest_seconds"]:
            stats["longest_seconds"] = duration
            stats["longest_text"] = text[:160]
            stats["longest_start"] = start

        if prev is not None:
            prev_end, prev_speaker = prev
            gap = start - prev_end
            if gap >= 4.0:
                silences.append({
                    "start": round(prev_end, 1),
                    "seconds": round(gap, 1),
                    "after": prev_speaker,
                    "before": speaker,
                })
            elif gap < -0.5 and speaker != prev_speaker:
                # The next speaker started before this one finished: overlapping speech.
                stats["overlaps"] += 1

        prev = (end, speaker)

    speakers = []
    for name, stats in sorted(by_speaker.items(), key=lambda item: -item[1]["talk_seconds"]):
        share = (stats["talk_seconds"] / total_talk * 100) if total_talk else 0.0
        speakers.append({
            "name": name,
            "talk_share": round(share, 1),
            "talk_seconds": round(stats["talk_seconds"], 1),
            "segments": stats["segments"],
            "questions": stats["questions"],
            "overlaps": stats["overlaps"],
            "longest_monologue": {
                "seconds": round(stats["longest_seconds"], 1),
                "start": stats["longest_start"],
                "at": _fmt(stats["longest_start"]),
                "text": stats["longest_text"],
            },
        })

    top = speakers[0] if speakers else None
    named = [s for s in speakers if s["name"] != "Unknown"]
    verdict = ""
    if not named:
        verdict = (
            "No speaker labels in this transcript - it was transcribed before diarization was enabled. "
            "Re-transcribe this recording to get talk balance."
        )
    elif top:
        if top["talk_share"] >= 65:
            verdict = (
                f"{top['name']} held the floor {top['talk_share']}% of the call. "
                "For pitch discipline the founder's share usually stays under about 55%."
            )
        elif top["talk_share"] >= 55:
            verdict = f"{top['name']} carried most of the call ({top['talk_share']}%). Workable, but there is room to pass the floor."
        else:
            verdict = f"The floor was shared fairly evenly - {top['name']} led with {top['talk_share']}%."
        if len(silences) == 0 and len(segments) > 12:
            verdict += " No thinking pause longer than four seconds the whole call."

    longest_silence = max((s["seconds"] for s in silences), default=0.0)
    return {
        "speakers": speakers,
        "silences": {
            "count": len(silences),
            "longest_seconds": longest_silence,
            "items": sorted(silences, key=lambda s: -s["seconds"])[:3],
        },
        "turns": len(segments),
        "total_talk_seconds": round(total_talk, 1),
        "verdict": verdict,
    }


def dynamics_line(dynamics: Dict[str, Any]) -> str:
    """One-line summary for digests (Slack / Notion / HubSpot task bodies)."""
    if not dynamics or not dynamics.get("speakers"):
        return ""
    parts = [f"{s['name']} {s['talk_share']}%" for s in dynamics["speakers"][:3]]
    line = "Talk balance: " + " | ".join(parts)
    silences = dynamics.get("silences") or {}
    if silences.get("count"):
        line += f" | {silences['count']} pauses over 4s (longest {int(silences.get('longest_seconds', 0))}s)"
    return line
