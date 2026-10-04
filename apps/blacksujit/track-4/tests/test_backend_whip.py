"""WhipScribe REST client, checked against recorded real responses.

Fixtures in tests/fixtures/whipscribe/ were captured from the live API on
2026-10-03 (identity/billing fields stripped). The locked-job fixtures follow
the documented shape because the test account has credit and no locked job.
"""

import json
import os

import pytest
import requests

from src.api import whip_api

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "whipscribe")
JOB = "bcfcea2d-b6d7-4cff-b75c-d5e3628ec5e7"


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


class FakeResponse:
    def __init__(self, status=200, payload=None, text=None, headers=None):
        self.status_code = status
        self._payload = payload
        self.text = text if text is not None else json.dumps(payload)
        self.headers = headers or {"Content-Type": "application/json"}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}", response=self)


class Recorder:
    """Route fake requests by URL suffix; remember every call."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, *args, **kwargs):
        self.calls.append({"url": url, **kwargs})
        for suffix, response in self.routes.items():
            if url.endswith(suffix) or suffix in url:
                return response() if callable(response) else response
        return FakeResponse(404, {"detail": "Not Found"})


# ------------------------------------------------------------------ env var

def test_env_key_prefers_correct_spelling(monkeypatch):
    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "new-key")
    monkeypatch.setenv("WHIPSKRIBE_API_KEY", "legacy-key")
    assert whip_api.env_api_key() == "new-key"


def test_env_key_falls_back_to_legacy_spelling(monkeypatch):
    monkeypatch.delenv("WHIPSCRIBE_API_KEY", raising=False)
    monkeypatch.setenv("WHIPSKRIBE_API_KEY", "legacy-key")
    assert whip_api.env_api_key() == "legacy-key"


def test_env_key_missing(monkeypatch):
    monkeypatch.delenv("WHIPSCRIBE_API_KEY", raising=False)
    monkeypatch.delenv("WHIPSKRIBE_API_KEY", raising=False)
    assert whip_api.env_api_key() is None


def test_app_get_api_key_uses_both_spellings(monkeypatch, flask_app):
    monkeypatch.setenv("WHIPSKRIBE_API_KEY", "legacy-key")
    with flask_app.app.test_request_context("/"):
        assert flask_app.get_api_key() == "legacy-key"
    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "new-key")
    with flask_app.app.test_request_context("/"):
        assert flask_app.get_api_key() == "new-key"


# -------------------------------------------------------------- idempotency

def test_submit_url_sends_idempotency_key(monkeypatch):
    rec = Recorder({"/transcribe/url": FakeResponse(202, {"job_id": JOB, "status": "queued"})})
    monkeypatch.setattr(requests, "post", rec)
    assert whip_api.submit_url("k", "https://youtube.com/watch?v=x") == JOB
    headers = rec.calls[0]["headers"]
    assert headers["X-API-Key"] == "k"
    key = headers["Idempotency-Key"]
    assert 8 <= len(key) <= 255 and " " not in key


def test_submit_file_sends_fresh_idempotency_key_each_time(monkeypatch, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF0000")
    rec = Recorder({"/transcribe": FakeResponse(202, {"job_id": JOB, "status": "queued"})})
    monkeypatch.setattr(requests, "post", rec)
    whip_api.submit_file("k", str(audio))
    whip_api.submit_file("k", str(audio))
    keys = [c["headers"]["Idempotency-Key"] for c in rec.calls]
    assert len(set(keys)) == 2


def test_submit_respects_caller_idempotency_key(monkeypatch):
    rec = Recorder({"/transcribe/url": FakeResponse(202, {"job_id": JOB})})
    monkeypatch.setattr(requests, "post", rec)
    whip_api.submit_url("k", "https://x", idempotency_key="retry-123")
    assert rec.calls[0]["headers"]["Idempotency-Key"] == "retry-123"


# ------------------------------------------------------------------- locked

def test_poll_job_done(monkeypatch):
    monkeypatch.setattr(requests, "get", Recorder({f"/jobs/{JOB}": FakeResponse(200, load("job_status_done.json"))}))
    assert whip_api.poll_job("k", JOB, interval=0) == "done"


def test_poll_job_detects_locked_boolean(monkeypatch):
    """The real paywall signal is the boolean `locked`, not status == "locked"."""
    monkeypatch.setattr(requests, "get", Recorder({f"/jobs/{JOB}": FakeResponse(200, load("job_status_locked.json"))}))
    with pytest.raises(whip_api.WhipScribeLocked) as info:
        whip_api.poll_job("k", JOB, interval=0)
    assert info.value.unlock_url == "https://whipscribe.com/credits"
    assert whip_api.is_locked(load("job_status_locked.json"))
    assert not whip_api.is_locked(load("job_status_done.json"))


def test_insights_locked_returns_reason(monkeypatch):
    monkeypatch.setattr(requests, "get", Recorder({"/insights": FakeResponse(402, load("insights_locked_402.json"))}))
    insights, reason = whip_api.fetch_insights("k", JOB)
    assert insights is None and reason == "transcript_locked"
    assert whip_api.get_session_summary("k", JOB) is None


# --------------------------------------------------------- insights/summary

def test_insights_parsed_from_real_payload(monkeypatch):
    monkeypatch.setattr(requests, "get", Recorder({"/insights": FakeResponse(200, load("insights.json"))}))
    insights, reason = whip_api.fetch_insights("k", JOB)
    assert reason is None
    assert insights["summary"].startswith("Jesus from Clean Sky Energy")
    assert insights["quotes"][0]["start"] == 187.4
    assert "EcoRigWolf 12 plan" in insights["topics"]


def test_session_summary_comes_from_insights_not_summary_route(monkeypatch):
    rec = Recorder({"/insights": FakeResponse(200, load("insights.json")), "/summary": FakeResponse(404, load("summary_404.json"))})
    monkeypatch.setattr(requests, "get", rec)
    summary = whip_api.get_session_summary("k", JOB)
    assert summary and summary.startswith("Jesus from Clean Sky Energy")
    assert not any(c["url"].endswith("/summary") for c in rec.calls)


def test_moments_from_insights_quotes():
    moments = whip_api.moments_from_insights(load("insights.json")["insights"])
    assert moments and all(m["source"] == "whipscribe-insights" for m in moments)
    assert moments == sorted(moments, key=lambda m: m["start"])
    assert all(len(m["title"]) >= 12 for m in moments)  # "Yes." is not a moment


# ---------------------------------------------------------------- moments

def test_parse_moments_docs_shape():
    payload = {"sentences": [{"start_s": 312.4, "end_s": 318.9, "text": "Here's the part nobody tells you"}]}
    [m] = whip_api.parse_moments(payload)
    assert (m["start"], m["end"], m["title"]) == (312.4, 318.9, "Here's the part nobody tells you")


def test_rest_candidates_parse_sentences_key(monkeypatch):
    sentences = {"sentences": [{"start_s": 5.0, "end_s": 7.5, "text": "What would it cost?"}]}
    monkeypatch.setattr(requests, "get", Recorder({"/clips/candidates": FakeResponse(200, sentences)}))
    moments, reason = whip_api.get_high_signal_moments("k", JOB, kinds=("question",))
    assert reason is None
    assert moments[0]["start"] == 5.0 and moments[0]["why"] == "question"


def test_rest_candidates_not_ready_kicks_preprocess(monkeypatch):
    monkeypatch.setattr(requests, "get", Recorder({"/clips/candidates": FakeResponse(409, {"error": "x", "code": "FEATURES_NOT_READY"})}))
    post = Recorder({"/clips/preprocess": FakeResponse(202, {})})
    monkeypatch.setattr(requests, "post", post)
    moments, reason = whip_api.get_high_signal_moments("k", JOB)
    assert moments == [] and reason == "preparing"
    assert post.calls[0]["url"].endswith(f"/jobs/{JOB}/clips/preprocess")


def test_rest_clips_404_falls_through_to_mcp(monkeypatch):
    """Live API: every /clips route is a route-level 404, so MCP serves moments."""
    from src.api import whip_mcp

    monkeypatch.setattr(requests, "get", Recorder({"/clips/candidates": FakeResponse(404, load("clips_candidates_404.json"))}))
    seen = {}

    def fake_high_signal(api_key, job_id, kinds, limit):
        seen["job"] = job_id
        return [{"start": 11.22, "end": 13.32, "title": "May I speak with Janine Correa?", "why": "question"}], None

    monkeypatch.setattr(whip_mcp, "high_signal_moments", fake_high_signal)
    moments, reason = whip_api.get_high_signal_moments("k", JOB)
    assert seen["job"] == JOB and reason is None and moments[0]["start"] == 11.22


# -------------------------------------------------------------------- audio

def test_audio_url_real_shape(monkeypatch):
    monkeypatch.setattr(requests, "get", Recorder({"/audio/url": FakeResponse(200, load("audio_url.json"))}))
    data = whip_api.get_audio_url("k", JOB)
    assert data["url"].startswith("https://audio.") and data["expires_in"] == 3600


def test_audio_url_disk_storage_made_absolute(monkeypatch):
    payload = {"url": "/v1/jobs/x/audio", "storage": "disk", "expires_in": 600}
    monkeypatch.setattr(requests, "get", Recorder({"/audio/url": FakeResponse(200, payload)}))
    assert whip_api.get_audio_url("k", JOB)["url"] == "https://whipscribe.com/api/v1/jobs/x/audio"


def test_jobs_list_real_shape_is_wrapped():
    data = load("jobs_list.json")
    assert isinstance(data, dict) and isinstance(data["jobs"], list)  # docs show a bare array
    assert "claim_token" not in json.dumps(data["jobs"])
