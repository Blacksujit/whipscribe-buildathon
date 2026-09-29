"""Metrics engine for calculating fundraising momentum and deal velocity."""

import numpy as np
from typing import List, Dict, Any


def _core_eval(eval_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the inner evaluation dict whether the input is wrapped or flat.

    Accepts either {"success": ..., "evaluation": {...}} (LLM pipeline output)
    or a bare evaluation dict (rows already unwrapped by the store).
    """
    if not isinstance(eval_data, dict):
        return {}
    inner = eval_data.get("evaluation")
    return inner if isinstance(inner, dict) else eval_data


def calculate_deal_velocity(evaluations: List[Dict[str, Any]]) -> float:
    """
    Calculates the Deal Velocity score (0-100).
    Formula: (Resolved / Promised) * (Avg Clarity / 100) * 100
    """
    if not evaluations:
        return 0.0

    total_promised = 0
    total_resolved = 0
    clarity_scores = []

    for eval_data in evaluations:
        eval_obj = _core_eval(eval_data)

        # Promised are the action items identified in the call
        action_items = eval_obj.get("action_items", [])
        total_promised += len(action_items)

        # Resolved are the items marked as resolved in that call
        resolved_items = eval_obj.get("resolved_items", [])
        total_resolved += len(resolved_items)

        # Extract clarity score from category_scores
        cat_scores = eval_obj.get("category_scores", {})
        clarity = cat_scores.get("clarity", cat_scores.get("narrative", 0)) or 0  # legacy key: narrative
        clarity_scores.append(clarity)

    if total_promised == 0:
        # If no promises were made, velocity depends entirely on clarity
        avg_clarity = np.mean(clarity_scores) if clarity_scores else 0
        return float(avg_clarity)

    execution_rate = total_resolved / total_promised
    avg_clarity = np.mean(clarity_scores) if clarity_scores else 0

    # Scale to 0-100
    velocity = execution_rate * (avg_clarity / 100) * 100
    return float(min(100.0, velocity))


def calculate_momentum_slope(scores: List[float]) -> float:
    """
    Calculates the trend slope of the overall score.
    Positive = Improving, Negative = Declining.
    """
    if len(scores) < 2:
        return 0.0

    # Filter out None or non-numeric values
    numeric_scores = [float(s) for s in scores if s is not None and isinstance(s, (int, float))]
    if len(numeric_scores) < 2:
        return 0.0

    x = np.arange(len(numeric_scores))
    y = np.array(numeric_scores)
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)
