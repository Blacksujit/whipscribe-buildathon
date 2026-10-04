"""Offline end-to-end pipeline (pytest form of ``python e2e_test.py --offline``).

sample transcript -> rule-based evaluation -> SQLite store -> trend comparison,
plus the same pipeline over the real seeded calls.
"""

import pytest

from src.core.compare import compare_evaluations
from src.core.evaluator import evaluate
from src.core.metrics import calculate_deal_velocity
from src.database import store


def test_e2e_script_offline_mode_passes():
    import e2e_test

    assert e2e_test.run_offline() is True


def test_pipeline_store_roundtrip(sample_transcript, fresh_db):
    result = evaluate(sample_transcript)
    store.save_evaluation("job-1", sample_transcript, result, "Sample Call", db_path=fresh_db)

    row = store.get_evaluation("job-1", db_path=fresh_db)
    assert row["meeting_name"] == "Sample Call"
    assert row["transcript"] == sample_transcript
    # The store unwraps {"success", "evaluation"} and keeps only the evaluation.
    assert row["evaluation"] == result["evaluation"]

    items = store.get_all_action_items(db_path=fresh_db)
    assert [i["text"] for i in items] == ["Let me circle back with you by Friday. Thanks."]
    assert items[0]["status"] == "PENDING"


def test_reanalysis_does_not_duplicate_action_items(sample_transcript, fresh_db):
    result = evaluate(sample_transcript)
    for _ in range(3):
        store.save_evaluation("job-1", sample_transcript, result, "Sample Call", db_path=fresh_db)
    assert len(store.get_all_action_items(db_path=fresh_db)) == 1
    assert len(store.get_all_evaluations(db_path=fresh_db)) == 1


def test_action_item_resolution(sample_transcript, fresh_db):
    result = evaluate(sample_transcript)
    store.save_evaluation("job-1", sample_transcript, result, db_path=fresh_db)
    text = result["evaluation"]["action_items"][0]["text"]
    assert store.get_unresolved_action_items(db_path=fresh_db) == [{"text": text, "owner": "unspecified"}]
    store.resolve_action_item(text, job_id="job-1", db_path=fresh_db)
    assert store.get_unresolved_action_items(db_path=fresh_db) == []
    assert store.get_all_action_items(db_path=fresh_db)[0]["resolved_at"]


def test_settings_and_deliveries(fresh_db):
    assert store.get_setting("missing", db_path=fresh_db) is None
    store.save_setting("llm_provider", "groq", db_path=fresh_db)
    assert store.get_setting("llm_provider", db_path=fresh_db) == "groq"
    store.save_delivery("job-1", "slack", "error", "first", db_path=fresh_db)
    store.save_delivery("job-1", "slack", "ok", "second", db_path=fresh_db)
    last = store.get_last_deliveries(db_path=fresh_db)
    assert last["slack"]["status"] == "ok" and last["slack"]["detail"] == "second"


def test_trend_comparison_over_two_stored_calls(sample_transcript, fresh_db):
    result = evaluate(sample_transcript)
    store.save_evaluation("a", sample_transcript, result, "Call A", db_path=fresh_db)
    store.save_evaluation("b", sample_transcript, result, "Call B", db_path=fresh_db)
    evals, names = store.get_evaluation_dicts_for_comparison(db_path=fresh_db)
    assert sorted(names) == ["Call A", "Call B"]
    comparisons = compare_evaluations(evals, names)
    # One action item per call, identical scores -> commitment rate 1, no slope, no variance.
    assert comparisons["deal_velocity"]["score"] == pytest.approx(1.0)
    assert comparisons["deal_velocity"]["velocity"] == "Low"
    assert set(comparisons["trends"].values()) == {"stable"}
    # Same commitment twice: the first sighting is still open, the last counts as resolved.
    assert comparisons["action_item_tracking"]["total"] == 2
    assert comparisons["action_item_tracking"]["resolved"] == 1


def test_seed_db_init_is_idempotent_and_seed_restores(tmp_path, monkeypatch):
    target = str(tmp_path / "empty.db")
    store.init_db(target)
    assert store.seed_if_missing(target) == 8
    store.init_db(target)  # recreate tables the seed lacks (deliveries)
    store.save_delivery("x", "slack", "ok", db_path=target)
    assert store.seed_if_missing(target) == 8  # already populated: left alone


def test_comparison_over_seeded_calls(seed_rows):
    evals = [r["evaluation"] for r in seed_rows]
    names = [r["meeting_name"] for r in seed_rows]
    comparisons = compare_evaluations(evals, names)
    assert len(comparisons["meetings"]) == len(seed_rows) == 8
    total_items = sum(len(e.get("action_items", [])) for e in evals)
    assert comparisons["deal_velocity"]["metrics"]["commitment_rate"] == pytest.approx(round(total_items / 8, 2))
    assert 0.0 <= calculate_deal_velocity(evals) <= 100.0


def test_seeded_verified_evidence_is_in_transcript(seed_rows):
    """Every quote marked verified must literally appear in its call, at a real segment start."""
    checked = 0
    for row in seed_rows:
        segments = row["transcript"].get("segments", [])
        core = row["evaluation"].get("evaluation", row["evaluation"])
        for key in ("compliance_risks", "tension_signals", "clarity_issues", "action_items"):
            for item in core.get(key, []):
                if item.get("verified") is not True:
                    continue
                quote = (item.get("text") or item.get("text_a") or "").strip("\\' ").lower()
                start = item.get("start", item.get("timestamp"))
                hits = [s for s in segments if quote in (s.get("text") or "").lower()]
                assert hits, f"{row['job_id'][:8]} {key}: verified quote not in transcript"
                assert float(start) == float(hits[0]["start"]), f"{row['job_id'][:8]} {key}: timestamp drift"
                checked += 1
    assert checked > 40  # the seed has ~60 verified quotes


def test_network_is_blocked_in_tests():
    import requests

    with pytest.raises(RuntimeError, match="network access attempted"):
        requests.get("https://api.whipscribe.com/health", timeout=1)
