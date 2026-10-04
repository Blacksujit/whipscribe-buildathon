"""Flask route smoke tests against a temp copy of the seed DB (no network)."""

import json

import pytest

from src.core.metrics import calculate_deal_velocity, calculate_momentum_slope


@pytest.fixture
def seed_job_id(seed_rows):
    # The large multi-speaker call has the richest evidence.
    return next(r["job_id"] for r in seed_rows if r["meeting_name"] == "Sample Call ENG MA")


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_root_service_info(client):
    body = client.get("/").get_json()
    assert body["service"] == "CallCoach-AI" and body["health"] == "/api/health"


def test_app_uses_temp_db(flask_app, test_db_path):
    assert flask_app.store.DB_PATH == test_db_path


def test_report_from_db(client, seed_job_id, seed_rows):
    resp = client.get(f"/api/report/{seed_job_id}")
    assert resp.status_code == 200
    body = resp.get_json()
    row = next(r for r in seed_rows if r["job_id"] == seed_job_id)
    assert body["success"] is True and body["job_id"] == seed_job_id
    assert len(body["transcript"]["segments"]) == len(row["transcript"]["segments"])
    core = body["evaluation"].get("evaluation", body["evaluation"])
    assert core["overall_score"] == row["evaluation"].get("evaluation", row["evaluation"])["overall_score"]
    assert body["audio_url"] is None  # no WhipScribe key in tests -> honest null, not a fake URL
    speakers = body["dynamics"]["speakers"]
    assert speakers and sum(s["talk_share"] for s in speakers) == pytest.approx(100.0, abs=0.5)


def test_report_evidence_timestamps_map_to_transcript(client, seed_job_id):
    body = client.get(f"/api/report/{seed_job_id}").get_json()
    segments = body["transcript"]["segments"]
    starts = {float(s["start"]) for s in segments}
    core = body["evaluation"].get("evaluation", body["evaluation"])
    checked = 0
    for key in ("compliance_risks", "tension_signals", "clarity_issues", "action_items"):
        for item in core.get(key, []):
            if item.get("verified") is True:
                start = item.get("start", item.get("timestamp"))
                assert float(start) in starts
                checked += 1
    assert checked > 0


def test_report_missing_is_404(client):
    resp = client.get("/api/report/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


def test_jobs_listing_joins_scores_from_db(client, flask_app, seed_rows, monkeypatch):
    known = seed_rows[0]
    fake_jobs = [
        {"job_id": known["job_id"], "filename": "call.mp3", "status": "done",
         "audio_duration_seconds": 61, "created_at": "2026-09-30T14:36:20Z"},
        {"job_id": "not-scored-yet", "filename": "new.mp3", "status": "done",
         "audio_duration_seconds": 30, "created_at": "2026-10-01T09:00:00Z"},
        {"job_id": "still-running", "filename": "x.mp3", "status": "processing"},
    ]
    calls = []

    def fake_list_jobs(api_key, *args, **kwargs):
        calls.append(api_key)
        return {"jobs": fake_jobs}

    monkeypatch.setattr(flask_app, "list_jobs", fake_list_jobs)
    resp = client.get("/api/jobs", headers={"X-API-Key": "test-key"})
    assert resp.status_code == 200
    body = resp.get_json()
    by_id = {j["job_id"]: j for j in body["jobs"]}
    assert calls == ["test-key"]
    assert "still-running" not in by_id
    expected = known["evaluation"].get("evaluation", known["evaluation"])["overall_score"]
    assert by_id[known["job_id"]]["score"] == expected
    assert by_id["not-scored-yet"]["score"] is None


def test_jobs_without_key_is_explicit(client):
    resp = client.get("/api/jobs")
    # No WhipScribe key: never a fabricated job list.
    if resp.status_code == 200:
        body = resp.get_json()
        assert all(j.get("job_id") for j in body.get("jobs", []))
    else:
        assert resp.status_code == 401
        assert resp.get_json()["jobs"] == []


def test_speakers(client):
    resp = client.get("/api/speakers")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    counts = [s["issue_count"] for s in body["speakers"]]
    assert counts == sorted(counts, reverse=True)
    if body["dynamics"]:
        assert sum(d["talk_share"] for d in body["dynamics"]) == pytest.approx(100.0, abs=0.5)


def test_trends_data_matches_metrics(client, seed_rows):
    resp = client.get("/api/trends-data")
    assert resp.status_code == 200
    body = resp.get_json()
    cores = [r["evaluation"].get("evaluation", r["evaluation"]) for r in seed_rows]
    assert body["labels"] == [r["meeting_name"] for r in seed_rows]
    assert body["overall"] == [c["overall_score"] for c in cores]
    assert body["velocity"] == pytest.approx(round(calculate_deal_velocity(cores), 1))
    assert body["slope"] == pytest.approx(round(calculate_momentum_slope(body["overall"]), 2))
    assert body["momentum"] in {"increasing", "decreasing", "stable"}
    assert set(body["category_scores"]) == {"action_items", "clarity", "tension", "compliance"}
    for change in body["changes"]:
        assert change["delta"] == pytest.approx(change["after"] - change["before"], abs=0.11)


def test_coach_data(client):
    resp = client.get("/api/coach-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ready"] is True
    tracking = body["action_item_tracking"]
    if tracking["total"]:
        assert tracking["completion_rate"] == pytest.approx(round(tracking["resolved"] / tracking["total"] * 100, 1))


def test_spotter_flags_absolute_promise(client):
    resp = client.post("/api/spotter", json={"text": "I guarantee this will definitely ship by Friday.", "start": 12})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["compliance_risk"]
    assert body["prompts"]


def test_spotter_requires_text(client):
    resp = client.post("/api/spotter", json={"text": "  "})
    assert resp.status_code == 400


def test_ask_requires_question(client):
    assert client.post("/api/ask", json={}).status_code == 400


def test_ask_answers_offline_from_local_data(client):
    resp = client.post("/api/ask", json={"question": "What did we promise?"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True and isinstance(body["answer"], str)


def test_sample_endpoint_points_at_a_real_report(client, flask_app):
    rules = {r.rule for r in flask_app.app.url_map.iter_rules()}
    if "/api/sample" not in rules:
        pytest.skip("/api/sample not implemented yet")
    body = client.get("/api/sample").get_json()
    job_id = body.get("job_id")
    assert job_id
    assert client.get(f"/api/report/{job_id}").status_code == 200


def test_responses_are_json_serialisable(client, seed_job_id):
    for path in ("/api/health", "/api/trends-data", "/api/coach-data", "/api/speakers", f"/api/report/{seed_job_id}"):
        resp = client.get(path)
        json.loads(resp.get_data(as_text=True))
