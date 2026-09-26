"""Metrics engine for calculating fundraising momentum and deal velocity."""

import numpy as np
from typing import List, Dict, Any

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
        eval_obj = eval_data.get("evaluation", {})
        
        # Promised are the action items identified in the call
        action_items = eval_obj.get("action_items", [])
        total_promised += len(action_items)
        
        # Resolved are the items marked as resolved in that call
        resolved_items = eval_obj.get("resolved_items", [])
        total_resolved += len(resolved_items)
        
        # Extract clarity score from category_scores
        cat_scores = eval_obj.get("category_scores", {})
        clarity = cat_scores.get("narrative", 0) # narrative agent = clarity
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
    
    x = np.arange(len(scores))
    y = np.array(scores)
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)
