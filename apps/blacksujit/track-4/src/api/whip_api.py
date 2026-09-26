"""WhipScribe API client: submit files, poll jobs, fetch transcripts."""

import time
import requests

BASE_URL = "https://whipscribe.com/api/v1"


def _headers(api_key):
    return {"X-API-Key": api_key}


def submit_file(api_key, filepath, language=None):
    """Upload an audio file and return the job_id."""
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
    """Submit a URL for transcription and return the job_id."""
    payload = {"url": url}
    if language:
        payload["language"] = language
    resp = requests.post(f"{BASE_URL}/transcribe", headers=_headers(api_key), json=payload)
    resp.raise_for_status()
    return resp.json()["job_id"]


def poll_job(api_key, job_id, timeout=300, interval=5):
    """Poll job status with robust retry for 5xx errors."""
    start_time = time.time()
    while True:
        try:
            resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=_headers(api_key))
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

        if (time.time() - start_time) > timeout:
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")
        time.sleep(interval)


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


def list_jobs(api_key, limit=100):
    """List recent jobs for the given API key."""
    resp = requests.get(f"{BASE_URL}/jobs", headers=_headers(api_key), params={"limit": limit})
    resp.raise_for_status()
    return resp.json()


def get_me(api_key):
    """Get account information for the given API key."""
    resp = requests.get(f"{BASE_URL}/me", headers=_headers(api_key))
    resp.raise_for_status()
    return resp.json()


def get_session_summary(api_key, job_id):
    """Fetch a high-level summary of a specific job."""
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/summary", headers=_headers(api_key))
    resp.raise_for_status()
    return resp.json()


def get_high_signal_moments(api_key, job_id):
    """Fetch high-signal moments (quotes) from a job."""
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/moments", headers=_headers(api_key))
    resp.raise_for_status()
    return resp.json()
