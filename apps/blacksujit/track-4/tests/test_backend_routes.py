"""Backend contract: /api/report additions, /api/audio, /api/ask retrieval source, /api/sample."""

import json
import os

import pytest

from src.core.evidence import annotate_evaluation, match_segment, parse_seconds

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "whipscribe")
SAMPLE_JOB = "bcfcea2d-b6d7-4cff-b75c-d5e3628ec5e7"  # richest seeded call
Q4_JOB = "7ebaeca0-9076-4c14-97be-a8b1948c8482"
AGENTS = {"compliance_risks": "compliance", "tension_signals": "tension",
          "clarity_issues": "clarity", "action_items": "action_items"}


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def no_persist(monkeypatch, flask_app):
    monkeypatch.setattr(flask_app, "_persist_whip_block", lambda *a, **k: None)
    flask_app._AUDIO_CACHE.clear()
    flask_app._MOMENTS_RETRY.clear()


# ------------------------------------------------------------------ evidence

def test_parse_seconds_variants():
    assert parse_seconds("0:41") == 41.0
    assert parse_seconds("1:02:03") == 3723.0
    assert parse_seconds(9.72) == 9.72
    assert parse_seconds("n/a") is None


def test_match_segment_picks_nearest_duplicate():
    segs = [{"start": 1, "end": 2, "text": "Yes."}, {"start": 50, "end": 51, "text": "Yes."}]
    assert match_segment("Yes.", segs, hint=49)["start"] == 50


def test_annotate_carries_segment_timing_and_speaker():
    transcript = {"segments": [
        {"start": 0.0, "end": 4.0, "text": "Hi there.", "speaker": "SPEAKER_00"},
        {"start": 9.72, "end": 17.48, "text": "Actually, the engineering team isn't ready yet.", "speaker": "SPEAKER_01"},
    ]}
    evaluation = {"tension_signals": [{"text": "the engineering team isn't ready yet", "timestamp": "0:03"}],
                  "action_items": [{"text": "Made-up line nobody said at all", "timestamp": 30}]}
    out = annotate_evaluation(evaluation, transcript)
    t = out["tension_signals"][0]
    assert (t["start"], t["end"], t["speaker"], t["agent"], t["verified"]) == (9.72, 17.48, "SPEAKER_01", "tension", True)
    a = out["action_items"][0]
    assert (a["start"], a["end"], a["agent"], a["verified"]) == (30.0, None, "action_items", False)
    assert "start" not in evaluation["tension_signals"][0]  # input untouched


# -------------------------------------------------------------------- report

def test_report_without_key_has_new_fields(client, no_persist):
    body = client.get(f"/api/report/{Q4_JOB}").get_json()
    assert body["success"] is True
    assert body["audio_url"] is None
    assert body["key_moments"] == [] and body["session_summary"] is None
    assert body["whip_status"]["audio_url"] == "no_api_key"
    assert body["whip_status"]["key_moments"] == "no_api_key"
    ev = body["evaluation"]
    total = 0
    for key, agent in AGENTS.items():
        for item in ev.get(key, []):
            total += 1
            assert item["agent"] == agent
            assert isinstance(item["start"], (int, float))
            assert "end" in item and "speaker" in item
    assert total > 0


def test_report_evidence_matches_transcript_segments(client, no_persist):
    body = client.get(f"/api/report/{Q4_JOB}").get_json()
    segments = {round(s["start"], 2): s for s in body["transcript"]["segments"]}
    verified = [i for k in AGENTS for i in body["evaluation"].get(k, []) if i.get("verified")]
    assert verified
    for item in verified:
        seg = segments[item["start"]]
        assert item["end"] == round(seg["end"], 2)


def test_report_with_whipscribe_extras(client, no_persist, monkeypatch, flask_app):
    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "k")
    monkeypatch.setattr(flask_app, "get_audio_url", lambda key, job: load("audio_url.json"))
    monkeypatch.setattr(flask_app, "fetch_insights", lambda key, job: (load("insights.json")["insights"], None))
    moments = [{"start": 11.22, "end": 13.32, "title": "May I speak with Janine Correa?", "why": "question",
                "speaker": None, "source": "whipscribe-mcp"}]
    monkeypatch.setattr(flask_app, "get_high_signal_moments", lambda key, job: (moments, None))
    body = client.get(f"/api/report/{SAMPLE_JOB}").get_json()
    assert body["audio_url"] == f"/api/audio/{SAMPLE_JOB}"
    assert body["session_summary"].startswith("Jesus from Clean Sky Energy")
    assert body["key_moments"] == moments
    assert "key_moments" not in body["whip_status"] and "audio_url" not in body["whip_status"]
    assert body["whip_read"]["topics"]


def test_report_locked_degrades_with_reason(client, no_persist, monkeypatch, flask_app):
    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "k")

    def gone(key, job):
        import requests

        resp = requests.Response()
        resp.status_code = 410
        raise requests.exceptions.HTTPError("410", response=resp)

    monkeypatch.setattr(flask_app, "get_audio_url", gone)
    monkeypatch.setattr(flask_app, "fetch_insights", lambda key, job: (None, "transcript_locked"))
    monkeypatch.setattr(flask_app, "get_high_signal_moments", lambda key, job: ([], "transcript_locked"))
    body = client.get(f"/api/report/{Q4_JOB}").get_json()
    assert body["audio_url"] is None and body["session_summary"] is None and body["key_moments"] == []
    assert body["whip_status"] == {"audio_url": "audio_expired", "insights": "transcript_locked",
                                   "session_summary": "transcript_locked", "key_moments": "transcript_locked"}


def test_audio_route_redirects_to_fresh_signed_url(client, no_persist, monkeypatch, flask_app):
    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "k")
    calls = []

    def signed(key, job):
        calls.append(job)
        return {"url": f"https://audio.example/{len(calls)}.mp3", "storage": "vultr", "expires_in": 3600}

    monkeypatch.setattr(flask_app, "get_audio_url", signed)
    r1 = client.get(f"/api/audio/{SAMPLE_JOB}")
    r2 = client.get(f"/api/audio/{SAMPLE_JOB}")
    assert r1.status_code == 302 and r1.headers["Location"] == "https://audio.example/1.mp3"
    assert r2.headers["Location"] == "https://audio.example/1.mp3"  # cached until near expiry
    r3 = client.get(f"/api/audio/{SAMPLE_JOB}?refresh=1")
    assert r3.headers["Location"] == "https://audio.example/2.mp3"


def test_audio_route_needs_key_and_valid_id(client, no_persist):
    assert client.get(f"/api/audio/{SAMPLE_JOB}").status_code == 401
    assert client.get("/api/audio/not a job").status_code in (400, 404)


# ----------------------------------------------------------------------- ask

def test_ask_falls_back_to_local_index_when_mcp_raises(client, monkeypatch, flask_app):
    from src.api import whip_mcp

    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "k")

    def boom(*a, **k):
        raise whip_mcp.WhipMCPError("down", code="unreachable")

    monkeypatch.setattr(whip_mcp, "search_calls", boom)
    body = client.post("/api/ask", json={"question": "Did anyone guarantee the price?"}).get_json()
    assert body["success"] is True
    assert body["source"] == "local-index"
    assert "unreachable" in body["retrieval"]["fallback_reason"]
    assert body["citations"], "local index should find the price guarantee in the seed calls"
    c = body["citations"][0]
    assert set(c) >= {"job_id", "meeting_name", "speaker", "start", "quote"}


def test_ask_without_key_is_local_index(client):
    body = client.post("/api/ask", json={"question": "What did we commit to?"}).get_json()
    assert body["source"] == "local-index" and body["retrieval"]["fallback_reason"] == "no_api_key"
    assert isinstance(body["citations"], list)


def test_ask_uses_mcp_citations(client, monkeypatch):
    from src.api import whip_mcp

    monkeypatch.setenv("WHIPSCRIBE_API_KEY", "k")
    cite = {"job_id": SAMPLE_JOB, "meeting_name": "Sample Call ENG MA", "speaker": None, "start": 41.92,
            "end": 49.22, "quote": "your price is guaranteed not to increase"}
    seen = {}

    def fake_search(api_key, question, jobs, max_calls=8):
        seen["jobs"] = jobs
        return {"citations": [cite], "searched": len(jobs), "not_ready": [], "errors": [], "query": "price"}

    monkeypatch.setattr(whip_mcp, "search_calls", fake_search)
    body = client.post("/api/ask", json={"question": "price guarantee?", "job_id": SAMPLE_JOB}).get_json()
    assert body["source"] == "whipscribe-mcp" and body["citations"] == [cite]
    assert [j["job_id"] for j in seen["jobs"]] == [SAMPLE_JOB]
    assert "0:41" in body["answer"]  # data-mode answer quotes the cited moment


# -------------------------------------------------------------------- sample

def test_sample_returns_seeded_scored_call(client):
    body = client.get("/api/sample").get_json()
    assert body["success"] is True and body["seeded"] is True
    assert body["job_id"] == SAMPLE_JOB
    report = client.get(f"/api/report/{body['job_id']}")
    assert report.status_code == 200
