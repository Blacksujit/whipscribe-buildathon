"""Tie every scored evidence quote back to the transcript segment it came from.

The four agents return quotes with a guessed timestamp (sometimes "m:ss"
strings, sometimes floats, sometimes nothing). The report needs the exact
segment: start/end seconds and the diarized speaker, so the UI can seek the
audio to the moment the words were said.
"""

import re

AGENT_KEYS = (
    ("compliance_risks", "compliance"),
    ("tension_signals", "tension"),
    ("clarity_issues", "clarity"),
    ("action_items", "action_items"),
)


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9$% ]+", " ", (text or "").lower())).strip()


def _literal(text):
    return (text or "").strip("\\' ").lower()


def parse_seconds(value):
    """Seconds from 12.5, "12.5", "0:41" or "1:02:03"; None when unparseable."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        try:
            total = 0.0
            for part in text.split(":"):
                total = total * 60 + float(part)
            return total
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def match_segment(text, segments, hint=None):
    """Return the transcript segment that contains ``text`` (or best overlaps it).

    Exact (normalised) substring wins; quotes that span two segments match
    the segment holding most of their words. ``hint`` (seconds) breaks ties
    between identical lines, e.g. repeated "Yes.".
    """
    quote = _norm(text)
    if not quote or not segments:
        return None

    exact = []
    for seg in segments:
        seg_text = _norm(seg.get("text"))
        if seg_text and (quote in seg_text or (len(seg_text) >= 12 and seg_text in quote)):
            exact.append(seg)
    if exact:
        if hint is not None and len(exact) > 1:
            return min(exact, key=lambda s: abs(float(s.get("start") or 0) - hint))
        return exact[0]

    words = [w for w in quote.split() if len(w) > 2]
    if len(words) < 3:
        return None
    best, best_score = None, 0.0
    for seg in segments:
        seg_words = set(_norm(seg.get("text")).split())
        if not seg_words:
            continue
        score = sum(1 for w in words if w in seg_words) / len(words)
        if score > best_score:
            best, best_score = seg, score
    return best if best_score >= 0.6 else None


def annotate_item(item, segments, agent):
    """Copy of one evidence item with start/end/speaker/agent filled in."""
    if not isinstance(item, dict):
        return item
    out = dict(item)
    text = item.get("text") or item.get("text_a") or item.get("evidence_quote") or ""
    hint = parse_seconds(item.get("start"))
    if hint is None:
        hint = parse_seconds(item.get("timestamp"))
    seg = match_segment(text, segments, hint=hint)
    if seg is not None:
        out["start"] = round(float(seg.get("start") or 0), 2)
        out["end"] = round(float(seg["end"]), 2) if seg.get("end") is not None else None
        out["speaker"] = seg.get("speaker") or item.get("speaker") or item.get("speaker_a") or None
        # Verified means the words literally appear in that segment.
        literal = _literal(text) in (seg.get("text") or "").lower()
        out["verified"] = bool(literal)
        out["match"] = "exact" if literal else "approximate"
    else:
        out["start"] = round(hint, 2) if hint is not None else 0.0
        end = parse_seconds(item.get("end"))
        out["end"] = round(end, 2) if end is not None else None
        out["speaker"] = item.get("speaker") or item.get("speaker_a") or None
        out["verified"] = False
        out["match"] = None
    out["agent"] = agent
    return out


def annotate_evaluation(evaluation, transcript):
    """Return a copy of ``evaluation`` whose evidence lists carry start/end/speaker/agent.

    Works on the inner evaluation dict and on the wrapped
    {"evaluation": {...}} shape. The stored record is not modified.
    """
    if not isinstance(evaluation, dict):
        return evaluation
    segments = (transcript or {}).get("segments", []) if isinstance(transcript, dict) else []
    wrapped = isinstance(evaluation.get("evaluation"), dict)
    inner = dict(evaluation["evaluation"] if wrapped else evaluation)
    for key, agent in AGENT_KEYS:
        items = inner.get(key)
        if isinstance(items, list):
            inner[key] = [annotate_item(item, segments, agent) for item in items]
    if wrapped:
        out = dict(evaluation)
        out["evaluation"] = inner
        return out
    return inner
