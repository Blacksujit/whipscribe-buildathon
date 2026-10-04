"""Conversation dynamics (src/core/dynamics.py): numbers from real timestamps."""

import pytest

from src.core.dynamics import _fmt, analyze_dynamics, dynamics_line


def _seg(speaker, start, end, text):
    return {"speaker": speaker, "start": start, "end": end, "text": text}


@pytest.fixture
def two_party():
    # Rep talks 0-10, Buyer 10-15 (a question), 5 s silence, Rep 20-30,
    # Buyer starts at 29 while the Rep is still talking (1 s overlap).
    return {"segments": [
        _seg("Rep", 0, 10, "Here is the full walkthrough of the plan."),
        _seg("Buyer", 10, 15, "Why that price?"),
        _seg("Rep", 20, 30, "Because the onboarding is included."),
        _seg("Buyer", 29, 31, "Okay."),
    ]}


def test_talk_share_and_seconds(two_party):
    result = analyze_dynamics(two_party)
    rep, buyer = result["speakers"]
    assert rep["name"] == "Rep" and buyer["name"] == "Buyer"
    assert rep["talk_seconds"] == 20.0 and buyer["talk_seconds"] == 7.0
    assert result["total_talk_seconds"] == 27.0
    assert rep["talk_share"] == pytest.approx(74.1)   # 20 / 27
    assert buyer["talk_share"] == pytest.approx(25.9)  # 7 / 27
    assert rep["talk_share"] + buyer["talk_share"] == pytest.approx(100.0, abs=0.11)


def test_questions_overlaps_silences(two_party):
    result = analyze_dynamics(two_party)
    rep, buyer = result["speakers"]
    assert buyer["questions"] == 1 and rep["questions"] == 0
    assert buyer["overlaps"] == 1 and rep["overlaps"] == 0
    assert result["silences"]["count"] == 1
    assert result["silences"]["longest_seconds"] == 5.0
    assert result["silences"]["items"][0] == {"start": 15.0, "seconds": 5.0, "after": "Buyer", "before": "Rep"}
    assert result["turns"] == 4


def test_longest_monologue(two_party):
    rep = analyze_dynamics(two_party)["speakers"][0]
    assert rep["longest_monologue"]["seconds"] == 10.0
    assert rep["longest_monologue"]["start"] == 0
    assert rep["longest_monologue"]["at"] == "0:00"


def test_dominant_speaker_verdict(two_party):
    assert "held the floor 74.1%" in analyze_dynamics(two_party)["verdict"]


def test_balanced_verdict():
    t = {"segments": [_seg("A", 0, 10, "one"), _seg("B", 10, 20, "two")]}
    assert analyze_dynamics(t)["verdict"].startswith("The floor was shared fairly evenly")


def test_undiarized_transcript_says_so():
    t = {"segments": [{"start": 0, "end": 5, "text": "hello"}]}
    result = analyze_dynamics(t)
    assert result["speakers"][0]["name"] == "Unknown"
    assert "No speaker labels" in result["verdict"]


def test_same_speaker_overlap_is_not_counted():
    t = {"segments": [_seg("A", 0, 10, "one"), _seg("A", 8, 12, "two")]}
    assert analyze_dynamics(t)["speakers"][0]["overlaps"] == 0


@pytest.mark.parametrize("transcript", [None, {}, {"segments": []}, {"segments": [{"text": "  "}]}])
def test_empty_inputs(transcript):
    assert analyze_dynamics(transcript) == {}


def test_bad_timestamps_do_not_crash():
    t = {"segments": [_seg("A", "x", "y", "text"), _seg("B", 1, 3, "more")]}
    result = analyze_dynamics(t)
    assert result["turns"] == 2


@pytest.mark.parametrize("seconds,label", [(0, "0:00"), (59.9, "0:59"), (125, "2:05"), ("bad", "0:00")])
def test_fmt(seconds, label):
    assert _fmt(seconds) == label


def test_dynamics_line(two_party):
    line = dynamics_line(analyze_dynamics(two_party))
    assert line == "Talk balance: Rep 74.1% | Buyer 25.9% | 1 pauses over 4s (longest 5s)"
    assert dynamics_line({}) == ""


def test_sample_transcript_dynamics(sample_transcript):
    result = analyze_dynamics(sample_transcript)
    total = sum(s["end"] - s["start"] for s in sample_transcript["segments"])
    assert result["total_talk_seconds"] == pytest.approx(round(total, 1))
    assert {s["name"] for s in result["speakers"]} == {"SPEAKER_00", "SPEAKER_01", "SPEAKER_02"}
    assert result["silences"]["count"] == 0
