"""Evaluator: rule-based arithmetic and transcript-verified evidence.

The LLM path is exercised offline by replacing ``call_llm`` with canned
agent responses, so the grounding / clamping logic runs for real without a
network call.
"""

import json

import pytest

from src.core import evaluator
from src.core.evaluator import (
    _fallback_evaluate, _verify_evidence, clean_json_output, evaluate, format_segments,
)


# ------------------------------------------------------------ rule-based path

def test_rule_based_scores_on_sample_transcript(sample_transcript):
    """Hand-checked against src/sample_transcript.json.

    Hits: action 1 ("by Friday"), clarity 2 ("I think", "I'm not sure"),
    tension 1 ("Actually ... isn't ready"), compliance 1 ("promise").
    Deductions: action 1*3=3, clarity min(2*8,20)=16, tension 1*5=5,
    compliance min(1*12,30)=12 -> overall 70-36=34, clamped to the 40 floor.
    """
    result = evaluate(sample_transcript)  # no key -> rule-based fallback
    assert result["success"] is True
    core = result["evaluation"]
    assert len(core["action_items"]) == 1
    assert len(core["clarity_issues"]) == 2
    assert len(core["tension_signals"]) == 1
    assert len(core["compliance_risks"]) == 1
    assert core["category_scores"] == {"action_items": 67, "clarity": 54, "tension": 65, "compliance": 58}
    assert core["overall_score"] == 40
    assert core["deal_killer"].startswith("Unbacked commitment language: We'll promise to ship mobile apps")
    assert result["metadata"]["mode"] == "rule-based"
    assert result["metadata"]["total_issues"] == 5


def test_rule_based_clean_call_scores_base():
    t = {"segments": [{"start": 0, "end": 3, "speaker": "A", "text": "Hello there, thanks for joining."}]}
    core = _fallback_evaluate(t)["evaluation"]
    assert core["overall_score"] == 70
    assert core["category_scores"] == {"action_items": 70, "clarity": 70, "tension": 70, "compliance": 70}
    assert core["deal_killer"] == "No critical issues identified"


def test_rule_based_deduction_caps():
    # 5 hedges -> clarity deduction capped at 20; 4 promises -> compliance capped at 30.
    segs = [{"start": i, "end": i + 1, "speaker": "A", "text": "I think maybe"} for i in range(5)]
    segs += [{"start": 10 + i, "end": 11 + i, "speaker": "A", "text": "I promise"} for i in range(4)]
    core = _fallback_evaluate({"segments": segs})["evaluation"]
    assert core["category_scores"]["clarity"] == 50
    assert core["category_scores"]["compliance"] == 40
    assert core["overall_score"] == 40  # 70 - 50 floors at 40


def test_rule_based_evidence_carries_real_timestamps(sample_transcript):
    core = evaluate(sample_transcript)["evaluation"]
    by_text = {s["text"]: s for s in sample_transcript["segments"]}
    for key in ("action_items", "clarity_issues", "compliance_risks"):
        for item in core[key]:
            seg = by_text[item["text"]]
            assert (item["start"], item["end"], item["speaker"]) == (seg["start"], seg["end"], seg["speaker"])
    for item in core["tension_signals"]:
        assert by_text[item["text_a"]]["start"] == item["start"]


def test_rule_based_handles_non_dict_transcript():
    result = _fallback_evaluate(None)
    assert result["success"] and result["evaluation"]["overall_score"] == 70


# ----------------------------------------------------------- evidence checks

SEGMENTS = [
    {"start": 0.0, "end": 4.0, "speaker": "Rep", "text": "Thanks for making the time today."},
    {"start": 4.5, "end": 9.0, "speaker": "Buyer", "text": "Honestly the price is a problem for us."},
    {"start": 65.2, "end": 70.0, "speaker": "Rep", "text": "I guarantee it ships before Christmas."},
]


def test_verify_evidence_exact_quote_maps_to_segment_start():
    assert _verify_evidence("I guarantee it ships before Christmas.", SEGMENTS) == (True, 65.2)


def test_verify_evidence_is_case_insensitive_substring():
    assert _verify_evidence("THE PRICE IS A PROBLEM", SEGMENTS) == (True, 4.5)


def test_verify_evidence_rejects_invented_quote():
    assert _verify_evidence("We will give you a 50% discount", SEGMENTS) == (False, 0.0)


@pytest.mark.parametrize("quote", ["", "   ", "''"])
def test_verify_evidence_rejects_blank(quote):
    assert _verify_evidence(quote, SEGMENTS) == (False, 0.0)


def test_format_segments_timestamps():
    text = format_segments(SEGMENTS)
    assert text.splitlines()[2] == "[Rep 1:05] I guarantee it ships before Christmas."


def test_clean_json_output_variants():
    assert clean_json_output('{"a": 1}') == {"a": 1}
    assert clean_json_output('```json\n{"a": 2}\n```') == {"a": 2}
    assert clean_json_output('Sure! {"a": 3} hope that helps') == {"a": 3}
    with pytest.raises(ValueError):
        clean_json_output("no json here")


# ------------------------------------------------ LLM path with canned agents

def _canned_llm(category_scores, overall=72):
    responses = {
        "ComplianceAgent": [
            {"text": "I guarantee it ships before Christmas.", "speaker": "Rep", "timestamp": 999, "severity": 8, "insight": "absolute promise"},
            {"text": "We will refund everything, no questions asked.", "speaker": "Rep", "timestamp": 12, "severity": 9, "insight": "invented"},
        ],
        "TensionAgent": [
            {"text": "the price is a problem", "speaker": "Buyer", "timestamp": 3, "severity": 6, "insight": "price objection"},
        ],
        "ClarityAgent": [],
        "ActionItemAgent": {
            "new_items": [{"text": "Thanks for making the time today.", "speaker": "Rep", "timestamp": 1, "severity": 2, "insight": "x"}],
            "resolved_items": [],
        },
    }

    def fake(provider, api_key, model, prompt, max_retries=3):
        for marker, payload in responses.items():
            if prompt.startswith(marker):
                return json.dumps(payload)
        return json.dumps({
            "overall_score": overall, "primary_risk": "Absolute ship-date guarantee",
            "summary": "Canned synthesis", "category_scores": category_scores,
        })
    return fake


@pytest.fixture
def llm_result(monkeypatch):
    monkeypatch.setattr(evaluator, "call_llm", _canned_llm(
        {"action_items": 80, "clarity": 70, "tension": 65, "compliance": 30}))
    return evaluate({"segments": SEGMENTS}, api_key="fake", model="m", provider="groq")


def test_llm_quotes_are_verified_against_transcript(llm_result):
    risks = llm_result["evaluation"]["compliance_risks"]
    real, invented = risks
    assert real["verified"] is True
    assert real["timestamp"] == 65.2          # model said 999; grounding replaced it
    assert real["confidence"] > 0
    assert invented["verified"] is False      # not in the transcript
    assert invented["confidence"] == 0.0
    tension = llm_result["evaluation"]["tension_signals"][0]
    assert tension["verified"] is True and tension["timestamp"] == 4.5


def test_llm_verification_rate(llm_result):
    # 2 of the 3 grounded list items are verified (action items are a dict and skipped today).
    meta = llm_result["metadata"]
    assert meta["agent_count"] == 4
    assert meta["total_issues"] == 4
    assert meta["verification_rate"] == pytest.approx(3 / 4)


def test_llm_overall_score_has_no_floor(monkeypatch):
    # A low score must stay low: the old 60 floor made every call read "60/100".
    monkeypatch.setattr(evaluator, "call_llm", _canned_llm({}, overall=12))
    low = evaluate({"segments": SEGMENTS}, api_key="k", model="m", provider="groq")["evaluation"]
    assert low["overall_score"] == 12
    monkeypatch.setattr(evaluator, "call_llm", _canned_llm({}, overall=100))
    high = evaluate({"segments": SEGMENTS}, api_key="k", model="m", provider="groq")["evaluation"]
    assert high["overall_score"] == 100
    monkeypatch.setattr(evaluator, "call_llm", _canned_llm({}, overall=140))
    capped = evaluate({"segments": SEGMENTS}, api_key="k", model="m", provider="groq")["evaluation"]
    assert capped["overall_score"] == 100


def test_llm_category_score_passes_through_without_floor(monkeypatch):
    monkeypatch.setattr(evaluator, "call_llm", _canned_llm({"action_items": 20}))
    core = evaluate({"segments": SEGMENTS}, api_key="k", model="m", provider="groq")["evaluation"]
    assert core["category_scores"]["action_items"] == 20


def test_llm_agent_failure_degrades_gracefully(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("provider down")
    monkeypatch.setattr(evaluator, "call_llm", boom)
    result = evaluate({"segments": SEGMENTS}, api_key="k", model="m", provider="groq")
    core = result["evaluation"]
    assert result["success"] is True
    assert core["compliance_risks"] == [] and core["action_items"] == []
    assert core["summary"] == "Analysis partially completed."


def test_llm_category_scores_respected(llm_result):
    scores = llm_result["evaluation"]["category_scores"]
    assert scores == {"action_items": 80, "clarity": 70, "tension": 65, "compliance": 30}  # 30 passes through: no floor


def test_llm_action_item_quotes_are_verified(llm_result):
    item = llm_result["evaluation"]["action_items"][0]
    assert item.get("verified") is True
    assert item["timestamp"] == 0.0


def test_no_llm_call_without_provider(monkeypatch, sample_transcript):
    def must_not_run(*args, **kwargs):
        raise AssertionError("LLM called without a key")
    monkeypatch.setattr(evaluator, "call_llm", must_not_run)
    assert evaluate(sample_transcript, api_key=None, provider="groq")["metadata"]["mode"] == "rule-based"


def test_unsupported_provider_raises():
    with pytest.raises(ValueError):
        evaluator.call_llm("nope", "k", "m", "prompt")
