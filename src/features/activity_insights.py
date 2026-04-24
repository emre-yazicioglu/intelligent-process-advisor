from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from features.activity_interaction_patterns import ActivityInteractionPatterns


@dataclass(frozen=True)
class ActivityInsights:
    """
    Business-level interpretation of activity patterns.

    Transforms technical classifications into actionable insights.
    """

    insights: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "insights": self.insights,
        }


def generate_activity_insights(
    patterns: ActivityInteractionPatterns,
) -> ActivityInsights:
    insights = []

    for activity, pattern in patterns.activity_patterns.items():

        if pattern == "multi_object_join":
            insights.append({
                "activity": activity,
                "pattern": pattern,
                "risk": "high",
                "insight": "Activity connects multiple business objects and may introduce reconciliation issues",
                "recommendation": "Validate object consistency and consider automation for matching logic",
            })

        elif pattern == "item_level_activity":
            insights.append({
                "activity": activity,
                "pattern": pattern,
                "risk": "medium",
                "insight": "Activity operates at item level, increasing process complexity and volume",
                "recommendation": "Aggregate where possible and monitor processing performance",
            })

        elif pattern == "single_object_primary":
            insights.append({
                "activity": activity,
                "pattern": pattern,
                "risk": "low",
                "insight": "Activity operates on a single primary object with low structural complexity",
                "recommendation": "Ensure efficiency and monitor cycle time",
            })

        elif pattern == "primary_with_reference":
            insights.append({
                "activity": activity,
                "pattern": pattern,
                "risk": "medium",
                "insight": "Activity depends on reference objects which may introduce dependency risks",
                "recommendation": "Ensure upstream data quality and availability",
            })

        elif pattern == "reference_only":
            insights.append({
                "activity": activity,
                "pattern": pattern,
                "risk": "medium",
                "insight": "Activity lacks a clear primary object and may indicate modeling issues",
                "recommendation": "Review event-object relationships",
            })

        else:
            insights.append({
                "activity": activity,
                "pattern": pattern,
                "risk": "unknown",
                "insight": "Pattern could not be clearly classified",
                "recommendation": "Investigate data quality or extend classification logic",
            })

    return ActivityInsights(insights=insights)