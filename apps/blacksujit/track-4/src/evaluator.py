"""LLM quality evaluation: score a transcript for action items, clarity, tension, compliance."""

import json
import os
import re
import time
import requests


def format_segments(segments):
    """Convert WhipScribe segment JSON into a readable format for the LLM."""
    lines = []
    for seg in segments:
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "").strip()
        mins = int(start // 60)
        secs = int(start % 60)
        line = f"[{speaker} {mins}:{secs:02d}] {text}"
        lines.append(line)
    return "\n".join(lines)


def build_prompt(segments):
    """Build the LLM evaluation prompt."""
    formatted = format_segments(segments)
    prompt = f"""You are a meeting quality analyst evaluating a business meeting transcript.

Analyze the transcript for the following quality metrics. For each issue found, include the exact text quote, the speaker, start/end timestamps in seconds, and a brief explanation.

1. ACTION ITEMS: Identify all decisions, next steps, assignments, owners, and deadlines mentioned.
2. CLARITY: Flag vague language, hedging ("I think," "maybe," "probably"), unbacked claims, or answers that lack specificity.
3. TENSION: Detect conflicting viewpoints, defensive language, abrupt topic changes, or rising tension between speakers.
4. COMPLIANCE: Flag risky promises, unbacked commitments, inappropriate language, or missing disclosures.

Score each category 0-100 (100 = best). Overall score is the average.

Return ONLY a JSON object (no extra text) with this exact schema:
{{
  "action_items": [{{"text": "...", "speaker": "...", "start": 0.0, "end": 0.0, "owner": "...", "deadline": "..."}}],
  "clarity_issues": [{{"text": "...", "speaker": "...", "start": 0.0, "end": 0.0, "issue": "..."}}],
  "tension_signals": [{{"text_a": "...", "speaker_a": "...", "start": 0.0, "end": 0.0, "text_b": "...", "speaker_b": "...", "signal": "..."}}],
  "compliance_risks": [{{"text": "...", "speaker": "...", "start": 0.0, "end": 0.0, "risk": "..."}}],
  "category_scores": {{"action_items": 0, "clarity": 0, "tension": 0, "compliance": 0}},
  "overall_score": 0
}}

Transcript:
{formatted}
"""
    return prompt


def call_llm(provider, api_key, model, prompt, max_retries=3):
    """Call an LLM provider and return the response text.

    Supports: openai, ollama (OpenAI-compatible), anthropic.
    """
    if provider in ("openai", "ollama"):
        url = "https://api.openai.com/v1/chat/completions" if provider == "openai" else "http://localhost:11434/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 4000,
        }
        for attempt in range(max_retries):
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        raise RuntimeError(f"Rate limited after {max_retries} retries (provider: {provider})")

    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        }
        for attempt in range(max_retries):
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip()
        raise RuntimeError(f"Rate limited after {max_retries} retries (provider: {provider})")

    raise ValueError(f"Unsupported provider: {provider}")


def clean_json_output(text):
    """Extract a JSON object from LLM output, handling common formatting issues."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from code blocks
    match = re.search(r"```(?:json)?\n(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting between first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM output: {text[:500]}")


def evaluate(transcript, api_key=None, model=None, provider=None):
    """Run LLM quality evaluation on a transcript.

    If no LLM credentials are provided, runs a rule-based fallback.
    """
    segments = transcript.get("segments", [])

    # If no LLM provider configured, use rule-based fallback
    if not api_key or not provider:
        return _fallback_evaluate(segments)

    if model is None:
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    prompt = build_prompt(segments)
    try:
        raw = call_llm(provider, api_key, model, prompt)
        result = clean_json_output(raw)
    except Exception as e:
        print(f"  [WARN] LLM evaluation failed ({e}), falling back to rule-based scoring.")
        return _fallback_evaluate(segments)

    return result


def _fallback_evaluate(segments):
    """Rule-based fallback evaluation when no LLM key is available."""
    action_items = []
    clarity_issues = []
    tension_signals = []
    compliance_risks = []

    for seg in segments:
        text = seg.get("text", "")
        speaker = seg.get("speaker") or "UNKNOWN"
        start = seg.get("start", 0)
        end = seg.get("end", 0)

        # Look for action item keywords
        lower = text.lower()
        if any(w in lower for w in ["deadline", "by friday", "by monday", "assign", "owner", "responsible"]):
            action_items.append({
                "text": text,
                "speaker": speaker,
                "start": start,
                "end": end,
                "owner": "unspecified",
                "deadline": "unspecified",
            })

        # Clarity issues: hedging language
        if any(w in lower for w in ["i think", "maybe", "probably", "i'm not sure", "i believe", "i guess", "sort of", "kind of"]):
            clarity_issues.append({
                "text": text,
                "speaker": speaker,
                "start": start,
                "end": end,
                "issue": "Uncertain/hedging language",
            })

        # Tension: defensive or conflicting language
        if any(w in lower for w in ["actually", "but", "however", "unfortunately", "disagree", "can't", "cannot", "isn't ready", "not ready"]):
            tension_signals.append({
                "text_a": text,
                "speaker_a": speaker,
                "start": start,
                "end": end,
                "text_b": "",
                "speaker_b": "",
                "signal": "Potential conflict or deflection",
            })

        # Compliance risk: unbacked promises
        if any(w in lower for w in ["promise", "guarantee", "guarantee", "commit to", "commit to deliver"]):
            compliance_risks.append({
                "text": text,
                "speaker": speaker,
                "start": start,
                "end": end,
                "risk": "Unbacked commitment/promise",
            })

    # Scores: start at 100, deduct per issue
    ai_score = max(0, 100 - len(action_items) * 5)
    clarity_score = max(0, 100 - len(clarity_issues) * 10)
    compliance_score = max(0, 100 - len(compliance_risks) * 15)
    tension_score = max(0, 100 - len(tension_signals) * 12)

    overall = round((ai_score + clarity_score + tension_score + compliance_score) / 4)

    return {
        "action_items": action_items,
        "clarity_issues": clarity_issues,
        "tension_signals": tension_signals,
        "compliance_risks": compliance_risks,
        "category_scores": {
            "action_items": ai_score,
            "clarity": clarity_score,
            "tension": tension_score,
            "compliance": compliance_score,
        },
        "overall_score": overall,
    }
