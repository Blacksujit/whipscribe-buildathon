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

def _verify_evidence(text: str, segments: list) -> tuple[bool, float]:
    """Verify a quote exists and return its actual start timestamp."""
    cleaned_text = text.strip("\\' ")
    if not cleaned_text:
        return False, 0.0
    
    for seg in segments:
        seg_text = seg.get("text", "").lower()
        if cleaned_text.lower() in seg_text:
            return True, float(seg.get("start", 0))
            
    return False, 0.0

def _calculate_confidence(agent_results: list, transcript_len: int) -> float:
    """Calculate a confidence score based on result density and transcript size."""
    if not agent_results: return 0.0
    density = len(agent_results) / (transcript_len / 100)
    return min(1.0, density * 0.5)

def evaluate(transcript, api_key=None, model=None, provider=None, pending_items=None):
    """Run a hyper-specialized Investment Readiness QA pipeline."""
    segments = transcript.get("segments", [])
    if not api_key or not provider:
        return _fallback_evaluate(segments)

    if model is None:
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    formatted = format_segments(segments)
    
    # Specialized Agents for Fundraising Intelligence
    agents = {
        "commitments": "InvestorCommitmentAgent: Track every explicit promise made by the founder. a) What was promised? b) When is it due? c) Is it a high-stakes commitment?",
        "friction": "FrictionDetectionAgent: Identify 'micro-tensions'. Look for investor hesitations, interruptions, or defensive founder responses. Mark the exact moment the vibe shifted.",
        "narrative": "NarrativeGapAgent: Analyze the pitch flow. Where did the founder become vague? Where did the investor stop engaging? Identify the 'dead zones' in the narrative.",
        "velocity": f"DealVelocityAgent: Extract action items that move the deal to the next stage. ALSO, check if any of these PENDING items were resolved in this call: {json.dumps(pending_items or [])}. Return JSON: {{ 'new_items': [{{'text', 'speaker', 'timestamp', 'severity', 'insight'}}], 'resolved_items': [{{'text', 'evidence_quote'}}] }}"
    }
    
    results = {}
    for key, system_prompt in agents.items():
        if key == "velocity":
            prompt = f"{system_prompt}\\n\\nTranscript:\\n{formatted}\\n\\nStrictly return JSON with 'new_items' and 'resolved_items' keys."
        else:
            prompt = f"{system_prompt}\\n\\nTranscript:\\n{formatted}\\n\\nReturn a JSON list of issues. Each must have 'text', 'speaker', 'timestamp', 'severity' (1-10), and 'insight'."
        try:
            resp = call_llm(provider, api_key, model, prompt)
            results[key] = clean_json_output(resp)
        except Exception as e:
            results[key] = [] if key != "velocity" else { "new_items": [], "resolved_items": [] }
            print(f"Agent {key} failed: {e}")

    synthesis_prompt = f"""You are a Venture Capitalist and Pitch Coach. Based on these findings:
    {json.dumps(results)}
    
    Provide a 'Brutal Honesty' score (0-100) on whether this founder is actually ready for a term sheet.
    Identify the #1 'Deal Killer' found in this call (the single most dangerous red flag).
    Return JSON: {{ 'overall_score': int, 'deal_killer': str, 'summary': str, 'category_scores': {{ 'commitments': int, 'friction': int, 'narrative': int, 'velocity': int }} }}
    """
    try:
        summary_resp = call_llm(provider, api_key, model, synthesis_prompt)
        summary = clean_json_output(summary_resp)
    except Exception as e:
        summary = {"overall_score": 50, "deal_killer": "None identified", "summary": "Analysis partially completed.", "category_scores": {}}

    # Grounding: replace guessed timestamps with actual segment start times
    for key, issues in results.items():
        if not isinstance(issues, list): continue
        verified = []
        for issue in issues:
            is_valid, timestamp = _verify_evidence(issue.get("text", ""), segments)
            if is_valid:
                verified.append({**issue, "verified": True, "timestamp": timestamp, "confidence": _calculate_confidence(issues, len(segments))})
            else:
                verified.append({**issue, "verified": False, "timestamp": issue.get("timestamp", 0), "confidence": 0.0})
        results[key] = verified
    return {
        "success": True,
        "evaluation": {
            "overall_score": summary.get("overall_score", 50),
            "deal_killer": summary.get("deal_killer", "None identified"),
            "summary": summary.get("summary", ""),
            "category_scores": summary.get("category_scores", {}),
            "compliance_risks": results.get("commitments", []),
            "tension_signals": results.get("friction", []),
            "clarity_issues": results.get("narrative", []),
            "action_items": results.get("velocity", {}).get("new_items", []) if isinstance(results.get("velocity"), dict) else results.get("velocity", []),
            "resolved_items": results.get("velocity", {}).get("resolved_items", []) if isinstance(results.get("velocity"), dict) else []
        },
        "transcript": transcript,
        "metadata": {
            "agent_count": len(agents),
            "total_issues": sum(len(v) if isinstance(v, list) else (len(v.get("new_items", [])) + len(v.get("resolved_items", []))) for v in results.values()),
            "verification_rate": sum(1 for k in results for i in (results[k] if isinstance(results[k], list) else results[k].get("new_items", []) + results[k].get("resolved_items", [])) if isinstance(i, dict) and i.get("verified")) / (sum(len(v) if isinstance(v, list) else (len(v.get("new_items", [])) + len(v.get("resolved_items", []))) for v in results.values()) or 1)
        }
    }

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
        lower = text.lower()
        if any(w in lower for w in ["deadline", "by friday", "by monday", "assign", "owner", "responsible"]):
            action_items.append({"text": text, "speaker": speaker, "start": start, "end": end, "owner": "unspecified", "deadline": "unspecified"})
        if any(w in lower for w in ["i think", "maybe", "probably", "i'm not sure", "i believe", "i guess", "sort of", "kind of"]):
            clarity_issues.append({"text": text, "speaker": speaker, "start": start, "end": end, "issue": "Uncertain/hedging language"})
        if any(w in lower for w in ["actually", "but", "however", "unfortunately", "disagree", "can't", "cannot", "isn't ready", "not ready"]):
            tension_signals.append({"text_a": text, "speaker_a": speaker, "start": start, "end": end, "text_b": "", "speaker_b": "", "signal": "Potential conflict or deflection"})
        if any(w in lower for w in ["promise", "guarantee", "commit to", "commit to deliver"]):
            compliance_risks.append({"text": text, "speaker": speaker, "start": start, "end": end, "risk": "Unbacked commitment/promise"})

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
        "category_scores": {"action_items": ai_score, "clarity": clarity_score, "tension": tension_score, "compliance": compliance_score},
        "overall_score": overall,
    }
