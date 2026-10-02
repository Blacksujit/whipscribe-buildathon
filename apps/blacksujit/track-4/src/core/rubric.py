"""Custom scoring rubrics for CallCoach-AI.

Lets users define custom scoring criteria, weight different categories
differently, and save/reuse rubrics across calls.
"""

import json
import os
from typing import Any


class ScoringRubric:
    """A custom scoring rubric."""

    def __init__(self, name: str, categories: dict[str, float], criteria: dict[str, Any] = None):
        """Initialize a scoring rubric.

        Args:
            name: The rubric name
            categories: Dict mapping category names to weights (0-1)
            criteria: Optional dict with custom criteria for each category
        """
        self.name = name
        self.categories = categories
        self.criteria = criteria or {}

    def validate(self) -> bool:
        """Validate the rubric."""
        # Check that weights sum to 1.0
        total_weight = sum(self.categories.values())
        if abs(total_weight - 1.0) > 0.01:
            return False

        # Check that all weights are positive
        for weight in self.categories.values():
            if weight < 0:
                return False

        return True

    def calculate_score(self, category_scores: dict[str, float]) -> float:
        """Calculate weighted score based on category scores.

        Args:
            category_scores: Dict mapping category names to scores (0-100)

        Returns:
            Weighted overall score (0-100)
        """
        total = 0
        for category, weight in self.categories.items():
            score = category_scores.get(category, 0)
            total += score * weight
        return round(total, 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            "name": self.name,
            "categories": self.categories,
            "criteria": self.criteria
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoringRubric":
        """Create from dict."""
        return cls(
            name=data["name"],
            categories=data["categories"],
            criteria=data.get("criteria", {})
        )


class RubricManager:
    """Manages custom scoring rubrics."""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "rubrics.json"
        )
        self.rubrics: dict[str, ScoringRubric] = {}
        self._load_rubrics()

    def _load_rubrics(self):
        """Load rubrics from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    for name, rubric_data in data.items():
                        self.rubrics[name] = ScoringRubric.from_dict(rubric_data)
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_rubrics(self):
        """Save rubrics to storage."""
        data = {name: rubric.to_dict() for name, rubric in self.rubrics.items()}
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def create_rubric(self, name: str, categories: dict[str, float], criteria: dict[str, Any] = None) -> ScoringRubric:
        """Create a new rubric.

        Args:
            name: The rubric name
            categories: Dict mapping category names to weights
            criteria: Optional custom criteria

        Returns:
            The created rubric
        """
        rubric = ScoringRubric(name, categories, criteria)

        if not rubric.validate():
            raise ValueError("Invalid rubric: weights must sum to 1.0 and be positive")

        self.rubrics[name] = rubric
        self._save_rubrics()
        return rubric

    def get_rubric(self, name: str) -> ScoringRubric | None:
        """Get a rubric by name."""
        return self.rubrics.get(name)

    def list_rubrics(self) -> list[str]:
        """List all rubric names."""
        return list(self.rubrics.keys())

    def delete_rubric(self, name: str) -> bool:
        """Delete a rubric."""
        if name in self.rubrics:
            del self.rubrics[name]
            self._save_rubrics()
            return True
        return False

    def apply_rubric(self, name: str, category_scores: dict[str, float]) -> float:
        """Apply a rubric to category scores.

        Args:
            name: The rubric name
            category_scores: Dict mapping category names to scores

        Returns:
            Weighted overall score
        """
        rubric = self.get_rubric(name)
        if not rubric:
            raise ValueError(f"Rubric '{name}' not found")
        return rubric.calculate_score(category_scores)


# Default rubrics
DEFAULT_RUBRICS = {
    "standard": {
        "name": "Standard",
        "categories": {
            "compliance": 0.3,
            "tension": 0.2,
            "clarity": 0.25,
            "action_items": 0.25
        }
    },
    "sales": {
        "name": "Sales Focus",
        "categories": {
            "compliance": 0.2,
            "tension": 0.15,
            "clarity": 0.25,
            "action_items": 0.4
        }
    },
    "support": {
        "name": "Support Focus",
        "categories": {
            "compliance": 0.25,
            "tension": 0.3,
            "clarity": 0.25,
            "action_items": 0.2
        }
    },
    "compliance_heavy": {
        "name": "Compliance Heavy",
        "categories": {
            "compliance": 0.5,
            "tension": 0.15,
            "clarity": 0.15,
            "action_items": 0.2
        }
    }
}


def create_default_rubrics(manager: RubricManager):
    """Create default rubrics if they don't exist."""
    for name, data in DEFAULT_RUBRICS.items():
        if name not in manager.rubrics:
            manager.rubrics[name] = ScoringRubric.from_dict(data)
    manager._save_rubrics()
