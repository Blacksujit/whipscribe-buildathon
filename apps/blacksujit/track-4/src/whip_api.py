"""WhipScribe API client: submit files, poll jobs, fetch transcripts."""

import time
import requests

BASE_URL = "https://whipscribe.com/api/v1"


def _headers(api_key):
    return {"X-API-Key": api_key}


def submit_file(api_key, filepath, language=None):
    """Upload an audio file and return the job_id.

    Uses the presigned-init flow for large files.
    """
    with open(filepath, "rb") as f:
        files = {"file": f}
        fields = {}
        if language:
            fields["language"] = language
        fields["source"] = "api"
        for k, v in fields.items():
            files[k] = (None, v)
        resp = requests.post(f"{BASE_URL}/transcribe", headers=_headers(api_key), files=files)
    resp.raise_for_status()
    return resp.json()["job_id"]


def submit_url(api_key, url, language=None):
    """Submit a URL (YouTube, podcast, etc.) and return the job_id."""
    payload = {"url": url, "source": "url"}
    if language:
        payload["language"] = language
    resp = requests.post(
        f"{BASE_URL}/transcribe/url",
        headers={**_headers(api_key), "Content-Type": "application/json"},
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def poll_job(api_key, job_id, timeout=300, interval=3):
    """Poll job status until done, failed, or timeout."""
    while True:
        resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=_headers(api_key))
        resp.raise_for_status()
        status = resp.json()["status"]
        if status == "done":
            return
        if status == "failed":
            raise RuntimeError(f"Job {job_id} failed: {resp.json().get('error', 'unknown')}")
        if status == "locked":
            raise RuntimeError(f"Job {job_id} is paywalled — add credit at the unlock_url")
        if timeout <= 0:
            raise TimeoutError(f"Job {job_id} timed out after polling")
        time.sleep(interval)
        timeout -= interval


def get_transcript(api_key, job_id, fmt="json"):
    """Fetch the transcript result. Default returns the rich JSON payload."""
    resp = requests.get(
        f"{BASE_URL}/jobs/{job_id}/result",
        headers=_headers(api_key),
        params={"format": fmt},
    )
    resp.raise_for_status()
    return resp.json()


def get_audio_url(api_key, job_id):
    """Get a short-lived playback URL for the original audio."""
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/audio/url", headers=_headers(api_key))
    resp.raise_for_status()
    return resp.json()


def get_high_signal(api_key, job_id, kind="question", limit=30):
    """Fetch high-signal moments (hooks, questions, numbers, speaker changes, etc.)."""
    resp = requests.get(
        f"{BASE_URL}/jobs/{job_id}/clips/candidates",
        headers=_headers(api_key),
        params={"kind": kind, "limit": limit},
    )
    resp.raise_for_status()
    return resp.json()


def get_session_summary(api_key, job_id):
    """Get session summary (duration, speaker turns, silences, brief summary)."""
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/clips/summary", headers=_headers(api_key))
    resp.raise_for_status()
    return resp.json()
