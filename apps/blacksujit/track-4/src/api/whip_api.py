"""WhipScribe API client: submit files, poll jobs, fetch transcripts.

Shapes below are checked against real responses (2026-10), not just the docs:

- GET  /jobs                 -> {"jobs": [...], "limit", "offset", "count", "total", ...}
                                (docs show a bare array; both are accepted)
- GET  /jobs/{id}            -> {"status": "done", ..., "locked": true?, "unlock_url"?}
                                "locked" is a BOOLEAN next to status, not a status value.
- GET  /jobs/{id}/insights   -> {"insights": {"summary", "quotes": [{speaker, text, start}],
                                "topics", "speakers": [{speaker, summary}], "_meta"}}
                                402 transcript_locked when paywalled.
- GET  /jobs/{id}/audio/url  -> {"url": <presigned>, "storage": "vultr"|"disk", "expires_in": 3600}
                                410 AUDIO_EXPIRED / AUDIO_MISSING when the audio is gone.
- GET  /jobs/{id}/summary    -> 404 route-not-found: this endpoint does not exist. The session
                                summary is insights.summary.
- /jobs/{id}/clips/*         -> documented, but every clips route returns a route-level 404 on
                                /api/v1 today. The same features are served by the WhipScribe
                                MCP server (clips_prepare / clips_get_high_signal), so
                                key moments go through src.api.whip_mcp.
"""

import os
import time
import uuid

import requests

BASE_URL = "https://whipscribe.com/api/v1"

# Reasons surfaced to the UI when an extra is missing (stable strings).
REASON_LOCKED = "transcript_locked"
REASON_NOT_READY = "preparing"
REASON_UNAVAILABLE = "unavailable"
REASON_NO_KEY = "no_api_key"
REASON_AUDIO_EXPIRED = "audio_expired"


class WhipScribeLocked(RuntimeError):
    """The finished transcript is paywalled for this account (locked: true)."""

    def __init__(self, job_id, unlock_url=None):
        super().__init__(
            f"Job {job_id} is locked by WhipScribe (transcript_locked). "
            "Add credit to the WhipScribe account to unlock it."
        )
        self.job_id = job_id
        self.unlock_url = unlock_url


def env_api_key():
    """WhipScribe key from the environment.

    WHIPSCRIBE_API_KEY is the correct spelling; WHIPSKRIBE_API_KEY is the
    legacy name this project shipped with and is still honoured.
    """
    return (os.environ.get("WHIPSCRIBE_API_KEY") or os.environ.get("WHIPSKRIBE_API_KEY") or "").strip() or None


def _headers(api_key):
    return {"X-API-Key": api_key}


def _submit_headers(api_key, idempotency_key=None):
    """Submit calls carry an Idempotency-Key so a retried POST never double-bills."""
    headers = _headers(api_key)
    headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
    return headers


def _error_code(resp):
    """Machine error code from a WhipScribe error body ({"error", "code"})."""
    try:
        body = resp.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        code = body.get("code")
        if not code and isinstance(body.get("detail"), dict):
            code = body["detail"].get("code")
        return code
    return None


def submit_file(api_key, filepath, language=None, idempotency_key=None):
    """Upload an audio file with diarization + word timestamps; return the job_id."""
    with open(filepath, "rb") as f:
        files = {"file": f}
        fields = {"diarize": "true", "word_timestamps": "true", "source": "api"}
        if language:
            fields["language"] = language
        for k, v in fields.items():
            files[k] = (None, v)
        resp = requests.post(
            f"{BASE_URL}/transcribe",
            headers=_submit_headers(api_key, idempotency_key),
            files=files,
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()["job_id"]


def submit_url(api_key, url, language=None, idempotency_key=None):
    """Submit a URL for diarized transcription and return the job_id.

    WhipScribe accepts URL submits on POST /api/v1/transcribe/url (per docs).
    Only Creative Commons-licensed YouTube URLs are currently accepted.
    """
    payload = {"url": url, "diarize": True, "word_timestamps": True, "source": "url"}
    if language:
        payload["language"] = language
    resp = requests.post(
        f"{BASE_URL}/transcribe/url",
        headers=_submit_headers(api_key, idempotency_key),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def get_job(api_key, job_id):
    """One status read: {"status", "progress", "locked"?, "unlock_url"?, ...}."""
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=_headers(api_key), timeout=30)
    resp.raise_for_status()
    return resp.json()


def is_locked(status_payload):
    """True when a status payload says the finished transcript is paywalled."""
    if not isinstance(status_payload, dict):
        return False
    return status_payload.get("locked") is True or status_payload.get("locked_code") == REASON_LOCKED


def poll_job(api_key, job_id, timeout=300, interval=5):
    """Poll job status with robust retry for 5xx errors.

    Raises WhipScribeLocked when the job finished but is paywalled: the
    result endpoint would only return a preview slice, which must not be
    scored as if it were the whole call.
    """
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout:
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

        try:
            resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=_headers(api_key), timeout=30)
            if resp.status_code in (429, 502, 503, 504):
                print(f"  [RETRY] Server error {resp.status_code}, retrying...")
                time.sleep(interval)
                continue
            resp.raise_for_status()
            payload = resp.json()
            status = payload.get("status")
            if is_locked(payload):
                raise WhipScribeLocked(job_id, payload.get("unlock_url"))
            if status == "done":
                return "done"
            if status == "failed":
                raise RuntimeError(f"Job {job_id} failed: {payload.get('error', 'unknown')}")
        except requests.exceptions.HTTPError:
            raise
        except requests.exceptions.RequestException as e:
            print(f"  [RETRY] Network error {e}, retrying...")
            time.sleep(interval)
            continue

        time.sleep(interval)


def get_transcript(api_key, job_id, fmt="json"):
    """Fetch the transcript result. Default returns the rich JSON payload."""
    resp = requests.get(
        f"{BASE_URL}/jobs/{job_id}/result",
        headers=_headers(api_key),
        params={"format": fmt},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_audio_url(api_key, job_id):
    """Get a short-lived playback URL for the original audio.

    Real shape: {"url", "storage": "vultr"|"disk", "expires_in": 3600}.
    For storage "disk" the url is backend-relative; it is made absolute here
    so callers can always hand it to a browser.
    """
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/audio/url", headers=_headers(api_key), timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    url = payload.get("url") if isinstance(payload, dict) else None
    if url and url.startswith("/"):
        payload["url"] = "https://whipscribe.com/api" + url if not url.startswith("/api/") else "https://whipscribe.com" + url
    return payload


def list_jobs(api_key, limit=100):
    """List recent jobs for the given API key."""
    resp = requests.get(f"{BASE_URL}/jobs", headers=_headers(api_key), params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_me(api_key):
    """Get account information for the given API key."""
    resp = requests.get(f"{BASE_URL}/me", headers=_headers(api_key), timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_insights(api_key, job_id):
    """WhipScribe's own read of a job. Returns (insights_dict | None, reason | None).

    Real payload: {"insights": {"summary", "quotes": [{speaker, text, start}],
    "topics": [str], "speakers": [{speaker, summary}], "_meta": {...}}}.
    402 transcript_locked -> (None, "transcript_locked"); 404 -> (None, "unavailable").
    """
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/insights", headers=_headers(api_key), timeout=60)
    if resp.status_code == 402:
        return None, REASON_LOCKED
    if resp.status_code == 404:
        return None, REASON_UNAVAILABLE
    if resp.status_code == 409:
        return None, REASON_NOT_READY
    resp.raise_for_status()
    payload = resp.json()
    insights = payload.get("insights") if isinstance(payload, dict) and "insights" in payload else payload
    if not isinstance(insights, dict) or not insights:
        return None, REASON_UNAVAILABLE
    return insights, None


def get_insights(api_key, job_id):
    """Backwards-compatible wrapper: insights dict or None."""
    insights, _reason = fetch_insights(api_key, job_id)
    return insights


def get_session_summary(api_key, job_id, insights=None):
    """The call's summary as WhipScribe wrote it, or None.

    GET /jobs/{id}/summary does not exist (route-level 404 on the live API),
    so the summary comes from /insights. Pass `insights` to avoid a refetch.
    """
    if insights is None:
        insights = get_insights(api_key, job_id)
    if isinstance(insights, dict):
        summary = str(insights.get("summary") or "").strip()
        return summary or None
    return None


def parse_moments(payload, source="whipscribe"):
    """Normalise WhipScribe moment payloads into [{start, end, title, why, ...}].

    Accepts the REST docs shape {"sentences": [{start_s, end_s, text}]}, the
    MCP shape {"sentences": [{start, end, text, speaker, is_question,
    has_hook, has_number, energy_avg}]}, search results {"matches": [...]}
    and a bare list.
    """
    if isinstance(payload, dict):
        rows = payload.get("sentences") or payload.get("matches") or payload.get("candidates") or []
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []
    moments = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or "").strip()
        start = row.get("start", row.get("start_s"))
        if not text or start is None:
            continue
        try:
            start = round(float(start), 2)
        except (TypeError, ValueError):
            continue
        end = row.get("end", row.get("end_s"))
        try:
            end = round(float(end), 2) if end is not None else None
        except (TypeError, ValueError):
            end = None
        why = []
        if row.get("has_hook"):
            why.append("hook")
        if row.get("is_question"):
            why.append("question")
        if row.get("has_number"):
            why.append("number")
        if row.get("kind"):
            why.append(str(row["kind"]))
        moments.append({
            "start": start,
            "end": end,
            "title": text[:140],
            "why": ", ".join(dict.fromkeys(why)) or "high-signal sentence",
            "speaker": row.get("speaker"),
            "source": source,
        })
    return moments


def moments_from_insights(insights, limit=5):
    """Fallback key moments: WhipScribe insights quotes (they carry start times)."""
    if not isinstance(insights, dict):
        return []
    moments = []
    for quote in insights.get("quotes") or []:
        if not isinstance(quote, dict):
            continue
        text = str(quote.get("text") or "").strip()
        if not text or quote.get("start") is None or len(text) < 12:
            continue
        try:
            start = round(float(quote["start"]), 2)
        except (TypeError, ValueError):
            continue
        moments.append({
            "start": start,
            "end": None,
            "title": text[:140],
            "why": "quoted in WhipScribe insights",
            "speaker": quote.get("speaker"),
            "source": "whipscribe-insights",
        })
    moments.sort(key=lambda m: m["start"])
    return moments[:limit]


def get_high_signal_moments(api_key, job_id, kinds=("hook", "question", "number"), limit=5):
    """High-signal moments for a job. Returns (moments, reason | None).

    Tries the documented REST surface first (GET clips/candidates, POST
    clips/preprocess on 409 FEATURES_NOT_READY). On the live API those routes
    404, so it falls through to the WhipScribe MCP tools clips_prepare +
    clips_get_high_signal, which serve the same feature set.
    """
    moments = []
    rest_missing = False
    for kind in kinds:
        resp = requests.get(
            f"{BASE_URL}/jobs/{job_id}/clips/candidates",
            headers=_headers(api_key),
            params={"kind": kind, "limit": limit},
            timeout=30,
        )
        if resp.status_code == 404:
            rest_missing = True
            break
        if resp.status_code == 409 and _error_code(resp) == "FEATURES_NOT_READY":
            requests.post(f"{BASE_URL}/jobs/{job_id}/clips/preprocess", headers=_headers(api_key), timeout=30)
            return [], REASON_NOT_READY
        if resp.status_code == 402:
            return [], REASON_LOCKED
        resp.raise_for_status()
        for moment in parse_moments(resp.json(), source="whipscribe-rest"):
            moment["why"] = moment["why"] if moment["why"] != "high-signal sentence" else kind
            moments.append(moment)
    if not rest_missing:
        return _dedupe_moments(moments, limit), None

    from src.api import whip_mcp

    return whip_mcp.high_signal_moments(api_key, job_id, kinds=kinds, limit=limit)


def _dedupe_moments(moments, limit):
    seen = set()
    out = []
    for moment in sorted(moments, key=lambda m: m["start"]):
        key = round(moment["start"], 1)
        if key in seen:
            continue
        seen.add(key)
        out.append(moment)
    return out[:limit]
