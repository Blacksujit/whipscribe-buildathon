"""AI quality evaluation: score a transcript for action items, clarity, tension, compliance.
Implements a multi-agent evidence pipeline with a final synthesis and hallucination guardrail.
"""

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
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "").strip()
        mins = int(start // 60)
        secs = int(start % 60)
        line = f"[{speaker} {mins}:{secs:02d}] {text}"
        lines.append(line)
    return "\n".join(lines)

def call_llm(provider, api_key, model, prompt, max_retries=3):
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

    elif provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
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
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\n(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from LLM output: {text[:500]}")

def _match_evidence(text: str, segments: list):
    """Return (segment, exact) for a quote, or (None, False).

    exact=True only when the quote literally appears in the segment text;
    a close-but-not-literal match still supplies timing, but is not
    "verified" evidence.
    """
    cleaned_text = (text or "").strip("\\' ")
    if not cleaned_text:
        return None, False

    for seg in segments:
        seg_text = seg.get("text", "").lower()
        if cleaned_text.lower() in seg_text:
            return seg, True

    from src.core.evidence import match_segment
    return match_segment(cleaned_text, segments), False


def _verify_evidence(text: str, segments: list) -> tuple[bool, float]:
    """Verify a quote exists and return its actual start timestamp."""
    seg, exact = _match_evidence(text, segments)
    if seg is None or not exact:
        return False, 0.0
    return True, float(seg.get("start", 0))


AGENT_NAMES = {"compliance_risks": "compliance", "tension_signals": "tension",
               "clarity_issues": "clarity", "action_items": "action_items"}


def ground_items(key: str, issues: list, segments: list) -> list:
    """Replace guessed timestamps with the matched segment's start/end/speaker.

    Only literal quotes are marked verified; approximate matches keep the
    segment timing with verified=False and match="approximate".
    """
    grounded = []
    agent = AGENT_NAMES.get(key, key)
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        quote = issue.get("text") or issue.get("text_a") or ""
        seg, exact = _match_evidence(quote, segments)
        if seg is not None:
            timestamp = float(seg.get("start", 0))
            grounded.append({
                **issue, "verified": exact, "timestamp": timestamp,
                "start": timestamp, "end": seg.get("end"),
                "speaker": seg.get("speaker") or issue.get("speaker"),
                "agent": agent, "match": "exact" if exact else "approximate",
                "confidence": _calculate_confidence(issues, len(segments)) if exact else 0.0,
            })
        else:
            grounded.append({**issue, "verified": False, "timestamp": issue.get("timestamp", 0),
                             "agent": agent, "match": None, "confidence": 0.0})
    return grounded


def _calculate_confidence(agent_results: list, transcript_len: int) -> float:
    """Calculate a confidence score based on result density and transcript size."""
    if not agent_results: return 0.0
    density = len(agent_results) / (transcript_len / 100)
    return min(1.0, density * 0.5)

def _score(value):
    """Clamp an LLM-reported score to 0-100 (no artificial floor)."""
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return 50

def evaluate(transcript, api_key=None, model=None, provider=None, pending_items=None,
             session_summary=None, key_moments=None, audio_url=None):
    """Run a multi-agent sales call QA evaluation pipeline."""
    segments = transcript.get("segments", [])
    if not api_key or not provider:
        return _fallback_evaluate(transcript)

    if model is None:
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    # When provider is groq, ensure model is a GROQ-native name (no openai/ prefix for non-GROQ models)
    if provider == "groq":
        # Map legacy/deprecated model names to currently available GROQ models.
        # Models that are already valid GROQ IDs pass through unchanged.
        groq_model_map = {
            "gpt-4o-mini": "openai/gpt-oss-20b",
            "gpt-4o": "openai/gpt-oss-120b",
            "llama3-8b-8192": "openai/gpt-oss-20b",
            "llama3-70b-8192": "openai/gpt-oss-120b",
            "llama-3.1-8b-instant": "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
            "gemma2-9b-it": "openai/gpt-oss-20b",
        }
        model = groq_model_map.get(model, model)

    formatted = format_segments(segments)

    # Build context from optional WhipScribe API features
    context_parts = []
    if session_summary:
        context_parts.append(f"Call Summary: {json.dumps(session_summary)}")
    if key_moments:
        context_parts.append(f"Key Moments: {json.dumps(key_moments)}")
    if audio_url:
        context_parts.append(f"Audio URL: {audio_url}")
    context = "\\n".join(context_parts)

    # Specialized Agents for Sales Call Quality Assurance
    agents = {
        "compliance_risks": "ComplianceAgent: You are a sales call quality analyst. Track every explicit promise, guarantee, or commitment made by the sales rep. a) What was promised? b) When is it due? c) Is it a high-stakes commitment?",
        "tension_signals": "TensionAgent: You are a sales call quality analyst. Identify 'micro-tensions'. Look for customer hesitations, interruptions, or defensive rep responses. Mark the exact moment the vibe shifted.",
        "clarity_issues": "ClarityAgent: You are a sales call quality analyst. Analyze the conversation flow. Where did the rep become vague? Where did the customer stop engaging? Identify the 'dead zones' in the narrative.",
        "action_items": f"ActionItemAgent: You are a sales call quality analyst. Extract action items that move the deal forward. ALSO, check if any of these PENDING items were resolved in this call: {json.dumps(pending_items or [])}. Return JSON: {{ 'new_items': [{{'text', 'speaker', 'timestamp', 'severity', 'insight'}}], 'resolved_items': [{{'text', 'evidence_quote'}}] }}"
    }

    # Build context section for prompts
    context_section = f"\\n\\nAdditional Context:\\n{context}" if context else ""

    results = {}
    for key, system_prompt in agents.items():
        if key == "action_items":
            prompt = f"{system_prompt}\\n\\nTranscript:\\n{formatted}{context_section}\\n\\nStrictly return JSON with 'new_items' and 'resolved_items' keys."
        else:
            prompt = f"{system_prompt}\\n\\nTranscript:\\n{formatted}{context_section}\\n\\nReturn a JSON list of issues. Each must have 'text', 'speaker', 'timestamp', 'severity' (1-10), and 'insight'."
        try:
            resp = call_llm(provider, api_key, model, prompt)
            results[key] = clean_json_output(resp)
        except Exception as e:
            results[key] = [] if key != "action_items" else { "new_items": [], "resolved_items": [] }
            print(f"Agent {key} failed: {e}")

    context_line = f"\\nAdditional Context from WhipScribe API: {context}" if context else ""
    synthesis_prompt = f"""You are a sales call quality coach. Based on these findings, provide an overall quality score (0-100) for how well this sales representative handled the customer conversation.
    Scoring guidance (IMPORTANT  use these as benchmarks):
    - 90-100: Excellent  handled everything professionally, all risks mitigated, clear outcomes.
    - 75-89: Good  solid performance with minor coaching opportunities.
    - 60-74: Acceptable  had some issues but managed the conversation adequately.
    - 40-59: Poor  significant issues that need immediate coaching attention.
    - 0-39: Very poor  serious failure (broken commitments, toxic behavior, major compliance violations).
    A typical business call with minor issues like hedging, mild tension, and one unbacked commitment scores 60-70.{context_line}
    Findings:
    {json.dumps(results)}
    Identify the #1 primary risk found in this call (the single most dangerous red flag).
    Return JSON: {{ 'overall_score': int, 'primary_risk': str, 'summary': str, 'category_scores': {{ 'action_items': int, 'clarity': int, 'tension': int, 'compliance': int }} }}
    """
    try:
        summary_resp = call_llm(provider, api_key, model, synthesis_prompt)
        summary = clean_json_output(summary_resp)
    except Exception as e:
        summary = {"overall_score": 50, "primary_risk": "None identified", "summary": "Analysis partially completed.", "category_scores": {}}

    # Grounding: replace guessed timestamps with actual segment start times
    def _ground(key, issues):
        return ground_items(key, issues, segments)

    for key, issues in results.items():
        if isinstance(issues, list):
            results[key] = _ground(key, issues)
        elif key == "action_items" and isinstance(issues, dict) and isinstance(issues.get("new_items"), list):
            # Action items arrive as {new_items, resolved_items}; ground the new ones too.
            results[key] = {**issues, "new_items": _ground(key, issues["new_items"])}

    # Map LLM output categories to frontend-expected names
    cat_scores = summary.get("category_scores", {})
    category_scores = {
        "action_items": _score(cat_scores.get("action_items", cat_scores.get("velocity", 50))),
        "clarity": _score(cat_scores.get("clarity", cat_scores.get("clarity_issues", cat_scores.get("narrative", 50)))),
        "tension": _score(cat_scores.get("tension", cat_scores.get("tension_signals", cat_scores.get("friction", 50)))),
        "compliance": _score(cat_scores.get("compliance", cat_scores.get("compliance_risks", cat_scores.get("commitments", 50)))),
    }
    # No floor: a 60 minimum made every call in the library read "60/100".
    # When the LLM omits an overall score, use the mean of the four categories.
    if isinstance(summary.get("overall_score"), (int, float)):
        overall_score = _score(summary["overall_score"])
    else:
        overall_score = round(sum(category_scores.values()) / len(category_scores))

    return {
        "success": True,
        "evaluation": {
            "overall_score": overall_score,
            "primary_risk": summary.get("primary_risk", "None identified"),
            "deal_killer": summary.get("primary_risk", "None identified"),
            "summary": summary.get("summary", ""),
            "category_scores": category_scores,
            "compliance_risks": results.get("compliance_risks", []),
            "tension_signals": results.get("tension_signals", []),
            "clarity_issues": results.get("clarity_issues", []),
            "action_items": results.get("action_items", {}).get("new_items", []) if isinstance(results.get("action_items"), dict) else results.get("action_items", []),
            "resolved_items": results.get("action_items", {}).get("resolved_items", []) if isinstance(results.get("action_items"), dict) else []
        },
        "transcript": transcript,
        "metadata": {
            "agent_count": len(agents),
            "total_issues": sum(len(v) if isinstance(v, list) else (len(v.get("new_items", [])) + len(v.get("resolved_items", []))) for v in results.values()),
            "verification_rate": sum(1 for k in results for i in (results[k] if isinstance(results[k], list) else results[k].get("new_items", []) + results[k].get("resolved_items", [])) if isinstance(i, dict) and i.get("verified")) / (sum(len(v) if isinstance(v, list) else (len(v.get("new_items", [])) + len(v.get("resolved_items", []))) for v in results.values()) or 1)
        }
    }

def _fallback_evaluate(transcript):
    """Rule-based fallback evaluation when no LLM key is available.

    Returns the same wrapped shape as the LLM pipeline so every caller sees
    one contract: {"success", "evaluation", "transcript", "metadata"}.
    """
    segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
    action_items = []
    clarity_issues = []
    tension_signals = []
    compliance_risks = []

    for seg in segments:
        text = seg.get("text", "")
        speaker = seg.get("speaker") or "UNKNOWN"
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        lower = text.lower()
        if any(w in lower for w in ["deadline", "by friday", "by monday", "assign", "owner", "responsible"]):
            action_items.append({"text": text, "speaker": speaker, "start": start, "end": end, "owner": "unspecified", "deadline": "unspecified"})
        if any(w in lower for w in ["i think", "maybe", "probably", "i'm not sure", "i believe", "i guess", "sort of", "kind of"]):
            clarity_issues.append({"text": text, "speaker": speaker, "start": start, "end": end, "issue": "Uncertain/hedging language"})
        if any(w in lower for w in ["actually", "but", "however", "unfortunately", "disagree", "can't", "cannot", "isn't ready", "not ready"]):
            tension_signals.append({"text_a": text, "speaker_a": speaker, "start": start, "end": end, "text_b": "", "speaker_b": "", "signal": "Potential conflict or deflection"})
        if any(w in lower for w in ["promise", "guarantee", "commit to", "commit to deliver"]):
            compliance_risks.append({"text": text, "speaker": speaker, "start": start, "end": end, "risk": "Unbacked commitment/promise"})

    base_score = 70
    deductions = {
        "action_items": len(action_items) * 3,
        "clarity": min(len(clarity_issues) * 8, 20),
        "tension": len(tension_signals) * 5,
        "compliance": min(len(compliance_risks) * 12, 30),
    }
    overall = max(40, min(95, base_score - sum(deductions.values())))

    ai_score = max(40, min(95, base_score - deductions["action_items"]))
    clarity_score = max(40, min(95, base_score - deductions["clarity"]))
    tension_score = max(40, min(95, base_score - deductions["tension"]))
    compliance_score = max(40, min(95, base_score - deductions["compliance"]))

    if compliance_risks:
        deal_killer = "Unbacked commitment language: " + compliance_risks[0]["text"][:120]
    elif tension_signals:
        deal_killer = "Tension signal: " + tension_signals[0]["text_a"][:120]
    elif clarity_issues:
        deal_killer = "Hedging language: " + clarity_issues[0]["text"][:120]
    else:
        deal_killer = "No critical issues identified"

    total_issues = len(action_items) + len(clarity_issues) + len(tension_signals) + len(compliance_risks)

    return {
        "success": True,
        "evaluation": {
            "overall_score": overall,
            "primary_risk": deal_killer,
            "deal_killer": deal_killer,
            "summary": "Rule-based evaluation (no LLM key configured) using keyword checks over the transcript.",
            "category_scores": {"action_items": ai_score, "clarity": clarity_score, "tension": tension_score, "compliance": compliance_score},
            "action_items": action_items,
            "clarity_issues": clarity_issues,
            "tension_signals": tension_signals,
            "compliance_risks": compliance_risks,
            "resolved_items": [],
        },
        "transcript": transcript if isinstance(transcript, dict) else {},
        "metadata": {
            "agent_count": 0,
            "mode": "rule-based",
            "total_issues": total_issues,
            "verification_rate": 0.0,
        },
    }
