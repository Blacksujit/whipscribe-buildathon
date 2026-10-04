"""Arithmetic under test: src/core/metrics.py and src/core/compare.py.

Every expected number below is worked out by hand from the formula in the
module docstring, so a silent change to the maths fails the suite.
"""

import pytest

from src.core import compare
from src.core.compare import compare_evaluations, generate_comparison_report
from src.core.metrics import calculate_deal_velocity, calculate_momentum_slope


def _ev(overall=70, clarity=50, tension=50, compliance=50, action_scores=50,
        action_items=(), clarity_issues=(), resolved=()):
    return {
        "overall_score": overall,
        "category_scores": {
            "action_items": action_scores, "clarity": clarity,
            "tension": tension, "compliance": compliance,
        },
        "action_items": [{"text": t} for t in action_items],
        "clarity_issues": [{"text": t, "speaker": "Rep"} for t in clarity_issues],
        "tension_signals": [],
        "compliance_risks": [],
        "resolved_items": [{"text": t} for t in resolved],
    }


# ---------------------------------------------------------------- metrics.py

class TestMetricsDealVelocity:
    def test_empty_is_zero(self):
        assert calculate_deal_velocity([]) == 0.0

    def test_execution_rate_times_clarity(self):
        # promised 4, resolved 1 -> 0.25 ; avg clarity (80+60)/2 = 70 -> 0.25*0.70*100
        evals = [
            _ev(clarity=80, action_items=["a", "b"], resolved=["a"]),
            _ev(clarity=60, action_items=["c", "d"]),
        ]
        assert calculate_deal_velocity(evals) == pytest.approx(17.5)

    def test_no_promises_falls_back_to_average_clarity(self):
        assert calculate_deal_velocity([_ev(clarity=40), _ev(clarity=90)]) == pytest.approx(65.0)

    def test_capped_at_100(self):
        evals = [_ev(clarity=100, action_items=["a"], resolved=["a", "b", "c"])]
        assert calculate_deal_velocity(evals) == 100.0

    def test_wrapped_and_flat_inputs_agree(self):
        flat = [_ev(clarity=80, action_items=["a", "b"], resolved=["a"])]
        wrapped = [{"success": True, "evaluation": flat[0]}]
        assert calculate_deal_velocity(flat) == calculate_deal_velocity(wrapped) == pytest.approx(40.0)

    def test_legacy_narrative_key_used_for_clarity(self):
        legacy = {"category_scores": {"narrative": 30}, "action_items": []}
        assert calculate_deal_velocity([legacy]) == pytest.approx(30.0)


class TestMomentumSlope:
    def test_linear_rise(self):
        assert calculate_momentum_slope([60, 70, 80]) == pytest.approx(10.0)

    def test_linear_fall(self):
        assert calculate_momentum_slope([90, 85, 80, 75]) == pytest.approx(-5.0)

    def test_flat(self):
        assert calculate_momentum_slope([70, 70, 70]) == pytest.approx(0.0, abs=1e-9)

    def test_needs_two_points(self):
        assert calculate_momentum_slope([]) == 0.0
        assert calculate_momentum_slope([42]) == 0.0

    def test_non_numeric_values_are_dropped(self):
        assert calculate_momentum_slope([None, 50, "x", 70]) == pytest.approx(20.0)
        assert calculate_momentum_slope([None, 50]) == 0.0


# ---------------------------------------------------------------- compare.py

class TestCompareDealVelocity:
    def test_empty(self):
        assert compare._calculate_deal_velocity([]) == {"velocity": "N/A", "score": 0, "trend": "Stable"}

    def test_full_formula(self):
        # commitment_rate = (2+4)/2 = 3
        # clarity slope over [50, 70] = 20 -> norm 2.0
        # tension variance of [40, 60] = 100 -> norm 1.0
        # velocity = 3 * (1 + 2.0) / (1 + 1.0) = 4.5 -> "High"
        evals = [
            _ev(clarity=50, tension=40, action_items=["a", "b"]),
            _ev(clarity=70, tension=60, action_items=["c", "d", "e", "f"]),
        ]
        result = compare._calculate_deal_velocity(evals)
        assert result["score"] == pytest.approx(4.5)
        assert result["velocity"] == "High"
        metrics = result["metrics"]
        assert float(metrics["commitment_rate"]) == pytest.approx(3.0)
        assert float(metrics["clarity_slope"]) == pytest.approx(20.0)
        assert float(metrics["tension_variance"]) == pytest.approx(100.0)

    def test_negative_clarity_slope_is_not_a_bonus(self):
        # slope -20 is clipped to 0 -> velocity = rate / (1 + var/100) = 2 / 1 = 2 -> "Moderate"
        evals = [
            _ev(clarity=70, tension=50, action_items=["a", "b"]),
            _ev(clarity=50, tension=50, action_items=["c", "d"]),
        ]
        result = compare._calculate_deal_velocity(evals)
        assert result["score"] == pytest.approx(2.0)
        assert result["velocity"] == "Moderate"

    @pytest.mark.parametrize("items,label", [(0, "Low"), (1, "Low"), (2, "Moderate"), (4, "High")])
    def test_label_thresholds_single_call(self, items, label):
        evals = [_ev(action_items=[f"item {i}" for i in range(items)])]
        result = compare._calculate_deal_velocity(evals)
        assert result["score"] == pytest.approx(float(items))
        assert result["velocity"] == label


class TestCompareEvaluations:
    def test_trend_labels_use_first_to_last_delta(self):
        evals = [
            _ev(overall=60, clarity=80, tension=50, compliance=70),
            _ev(overall=66, clarity=70, tension=52, compliance=60),
        ]
        result = compare_evaluations(evals, ["Call A", "Call B"], dates=["2026-01-01", "2026-01-02"])
        assert result["trends"]["overall"] == "improving"      # +6
        assert result["trends"]["clarity"] == "declining"      # -10
        assert result["trends"]["tension"] == "stable"         # +2
        assert result["trends"]["compliance"] == "declining"   # -10
        assert result["trends"]["action_items"] == "stable"    # 0

    def test_single_call_has_insufficient_data(self):
        result = compare_evaluations([_ev()], ["Only"], dates=["2026-01-01"])
        assert set(result["trends"].values()) == {"insufficient_data"}

    def test_meetings_sorted_by_date(self):
        evals = [_ev(overall=90), _ev(overall=50)]
        result = compare_evaluations(evals, ["Late", "Early"], dates=["2026-03-01", "2026-01-01"])
        assert [m["name"] for m in result["meetings"]] == ["Early", "Late"]
        # Scores travel with their meeting through the sort: Early=50 -> Late=90.
        assert [m["scores"]["overall"] for m in result["meetings"]] == [50, 90]
        assert result["trends"]["overall"] == "improving"

    def test_action_item_tracking_resolution_rule(self):
        # An item is "resolved" when it never appears again later in history.
        evals = [
            _ev(action_items=["Send the pricing deck"]),
            _ev(action_items=["Send the pricing deck", "Book the security review"]),
        ]
        result = compare_evaluations(evals, ["One", "Two"], dates=["2026-01-01", "2026-01-02"])
        tracking = result["action_item_tracking"]
        assert tracking["total"] == 3
        assert tracking["resolved"] == 2
        assert tracking["completion_rate"] == pytest.approx(66.7)
        assert [u["text"] for u in tracking["unresolved"]] == ["Send the pricing deck"]

    def test_common_issues_need_two_sightings(self):
        evals = [
            _ev(clarity_issues=["We can probably maybe do that"]),
            _ev(clarity_issues=["We can probably maybe do that", "One-off hedge here"]),
        ]
        result = compare_evaluations(evals, ["One", "Two"], dates=["2026-01-01", "2026-01-02"])
        common = result["common_issues"]
        assert len(common) == 1
        assert common[0]["count"] == 2
        assert common[0]["meetings"] == ["One", "Two"]

    def test_speaker_analysis_counts(self):
        evals = [_ev(clarity_issues=["a", "b"]), _ev(clarity_issues=["c"])]
        result = compare_evaluations(evals, ["One", "Two"], dates=["2026-01-01", "2026-01-02"])
        assert result["speaker_analysis"]["Rep"]["count"] == 3
        assert result["speaker_analysis"]["Rep"]["types"] == {"clarity_issues"}

    def test_insights_reflect_trend(self):
        evals = [_ev(overall=50), _ev(overall=80)]
        result = compare_evaluations(evals, ["One", "Two"], dates=["2026-01-01", "2026-01-02"])
        assert "Overall meeting quality is trending upwards." in result["insights"]

    def test_report_renders(self):
        evals = [_ev(action_items=["x"]), _ev(action_items=["y"])]
        report = generate_comparison_report(compare_evaluations(evals, ["A", "B"]))
        assert report.startswith("# Meeting Intelligence Comparison Report")
        assert "Commitment Rate: 1.0" in report


class TestFuzzyMatch:
    def test_identical(self):
        assert compare._fuzzy_match("follow up on pricing", "follow up on pricing")

    def test_close_variant(self):
        assert compare._fuzzy_match("follow up on pricing friday", "follow up on the pricing by friday", 0.6)

    def test_unrelated(self):
        assert not compare._fuzzy_match("follow up on pricing", "the weather is nice")

    def test_empty(self):
        assert not compare._fuzzy_match("", "anything")
