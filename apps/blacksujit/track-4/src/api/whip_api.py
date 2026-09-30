"""WhipScribe API client: submit files, poll jobs, fetch transcripts."""

import time
import requests

BASE_URL = "https://whipscribe.com/api/v1"


def _headers(api_key):
    return {"X-API-Key": api_key}


def submit_file(api_key, filepath, language=None):
    """Upload an audio file with diarization + word timestamps; return the job_id."""
    with open(filepath, "rb") as f:
        files = {"file": f}
        fields = {"diarize": "true", "word_timestamps": "true", "source": "api"}
        if language:
            fields["language"] = language
        for k, v in fields.items():
            files[k] = (None, v)
        resp = requests.post(f"{BASE_URL}/transcribe", headers=_headers(api_key), files=files, timeout=30)
    resp.raise_for_status()
    return resp.json()["job_id"]


def submit_url(api_key, url, language=None):
    """Submit a URL for diarized transcription and return the job_id.

    WhipScribe accepts URL submits on POST /api/v1/transcribe/url (per docs).
    Only Creative Commons-licensed YouTube URLs are currently accepted.
    """
    payload = {"url": url, "diarize": True, "word_timestamps": True, "source": "url"}
    if language:
        payload["language"] = language
    resp = requests.post(f"{BASE_URL}/transcribe/url", headers=_headers(api_key), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["job_id"]


def poll_job(api_key, job_id, timeout=300, interval=5):
    """Poll job status with robust retry for 5xx errors."""
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout:
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

        try:
            resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=_headers(api_key), timeout=30)
            if resp.status_code in (502, 503, 504):
                print(f"  [RETRY] Server error {resp.status_code}, retrying...")
                time.sleep(interval)
                continue
            resp.raise_for_status()
            status = resp.json().get("status")
            if status == "done":
                return "done"
            if status == "failed":
                raise RuntimeError(f"Job {job_id} failed: {resp.json().get('error', 'unknown')}")
            if status == "locked":
                raise RuntimeError(f"Job {job_id} is paywalled")
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
    """Get a short-lived playback URL for the original audio."""
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/audio/url", headers=_headers(api_key), timeout=30)
    resp.raise_for_status()
    return resp.json()


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


def get_session_summary(api_key, job_id):
    """Fetch a high-level summary of a specific job.

    Falls back gracefully if the summary endpoint is unavailable for this job.
    """
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/summary", headers=_headers(api_key), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_high_signal_moments(api_key, job_id):
    """Fetch high-signal moments (quotes) from a job.

    Uses the /clips/candidates endpoint as documented in the WhipScribe API.
    Falls back to None if the endpoint is unavailable for this job.
    """
    resp = requests.get(
        f"{BASE_URL}/jobs/{job_id}/clips/candidates",
        headers=_headers(api_key),
        params={"kind": "question"},
        timeout=30,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_insights(api_key, job_id):
    """WhipScribe's own read of a job: summary, named quotes, topics, speakers.

    Returns None when the job has no insights (404/402) instead of raising.
    """
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/insights", headers=_headers(api_key), timeout=60)
    if resp.status_code in (402, 404):
        return None
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("insights") or payload
