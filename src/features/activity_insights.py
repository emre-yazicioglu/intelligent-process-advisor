from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from features.activity_context_features import ActivityContextFeatures
from features.activity_interaction_patterns import ActivityInteractionPatterns


@dataclass(frozen=True)
class ActivityInsights:
    """
    Business-level interpretation of activity patterns.

    Transforms technical classifications into process intelligence insights.
    """

    insights: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "insights": self.insights,
        }


def build_context_explanation(activity_context: dict[str, Any] | None) -> str:
    if activity_context is None:
        return "No activity context is available yet."

    frequency = activity_context["frequency"]
    percentage = activity_context["percentage_of_total_events"]
    average_position = activity_context["average_position"]
    variants = activity_context["variants_containing_activity"]

    return (
        f"This activity occurred {frequency} times, representing {percentage}% "
        f"of all case-level events. Its average process position is {average_position}, "
        f"and it appears in {variants} process variant(s)."
    )


def build_data_driven_recommendation(
    base_recommendation: str,
    activity_context: dict[str, Any] | None,
) -> str:
    if activity_context is None:
        return base_recommendation

    percentage = activity_context["percentage_of_total_events"]
    average_position = activity_context["average_position"]
    variants = activity_context["variants_containing_activity"]

    if percentage >= 20 and average_position <= 2:
        context_recommendation = (
            "Because this activity is frequent and appears early in the process, "
            "improving it can influence many downstream cases. Prioritize it for "
            "standardization, workflow automation, or preventive validation."
        )
    elif percentage >= 20:
        context_recommendation = (
            "Because this activity is high-volume, it is worth checking for repetitive "
            "manual work, rule-based decisions, and automation potential."
        )
    elif variants >= 2:
        context_recommendation = (
            "Because this activity appears across multiple variants, review whether it "
            "represents a stable process step or a source of process variation."
        )
    else:
        context_recommendation = (
            "Because this activity has limited contextual impact in the current log, "
            "monitor it but avoid over-prioritizing automation unless business effort "
            "or exception cost is high."
        )

    return f"{base_recommendation} {context_recommendation}"


def generate_activity_insights(
    patterns: ActivityInteractionPatterns,
    context_features: ActivityContextFeatures | None = None,
) -> ActivityInsights:
    insights: list[dict[str, Any]] = []

    activity_context_map = {}

    if context_features is not None:
        activity_context_map = context_features.activity_context

    for activity, pattern in patterns.activity_patterns.items():
        activity_context = activity_context_map.get(activity)
        context_explanation = build_context_explanation(activity_context)

        if pattern == "multi_object_join":
            base_recommendation = (
                "Investigate whether this activity involves manual checks, mismatches, "
                "missing references, price or quantity differences, or approval delays. "
                "This is a strong candidate for rule-based validation, exception handling, "
                "or AI-assisted matching."
            )

            insights.append({
                "activity": activity,
                "pattern": pattern,
                "pattern_label": "Object Matching / Reconciliation Activity",
                "risk": "high",
                "context": activity_context,
                "insight": (
                    "This activity connects multiple business objects. "
                    "In a P2P process, this usually indicates a matching, reconciliation, "
                    "or dependency point where process issues can become visible. "
                    f"{context_explanation}"
                ),
                "recommendation": build_data_driven_recommendation(
                    base_recommendation,
                    activity_context,
                ),
            })

        elif pattern == "item_level_activity":
            base_recommendation = (
                "Analyze item-level variation, repeated manual work, and exception frequency. "
                "Consider standardization, aggregation, validation rules, or targeted automation "
                "for high-volume item-level steps."
            )

            insights.append({
                "activity": activity,
                "pattern": pattern,
                "pattern_label": "Item-Level Activity",
                "risk": "medium",
                "context": activity_context,
                "insight": (
                    "This activity operates at item level rather than only at document/header level. "
                    "Item-level processing often increases transaction volume, operational complexity, "
                    "and exception handling effort. "
                    f"{context_explanation}"
                ),
                "recommendation": build_data_driven_recommendation(
                    base_recommendation,
                    activity_context,
                ),
            })

        elif pattern == "single_object_primary":
            base_recommendation = (
                "Monitor cycle time, repetition, and manual effort. "
                "If the activity is frequent and rule-based, it may still be a candidate "
                "for RPA or workflow automation."
            )

            insights.append({
                "activity": activity,
                "pattern": pattern,
                "pattern_label": "Single-Object Activity",
                "risk": "low",
                "context": activity_context,
                "insight": (
                    "This activity mainly works on one primary business object. "
                    "Structurally, it is less complex than activities that connect multiple objects. "
                    f"{context_explanation}"
                ),
                "recommendation": build_data_driven_recommendation(
                    base_recommendation,
                    activity_context,
                ),
            })

        elif pattern == "primary_with_reference":
            base_recommendation = (
                "Review upstream data quality, reference availability, and dependency timing. "
                "Consider validation checks before the activity starts."
            )

            insights.append({
                "activity": activity,
                "pattern": pattern,
                "pattern_label": "Primary Object with Reference Dependency",
                "risk": "medium",
                "context": activity_context,
                "insight": (
                    "This activity has a primary object but also depends on reference objects. "
                    "That dependency can create delays or data quality issues when upstream information "
                    "is missing, late, or inconsistent. "
                    f"{context_explanation}"
                ),
                "recommendation": build_data_driven_recommendation(
                    base_recommendation,
                    activity_context,
                ),
            })

        elif pattern == "reference_only":
            base_recommendation = (
                "Review the event log design and confirm whether this activity should be linked "
                "to a primary object."
            )

            insights.append({
                "activity": activity,
                "pattern": pattern,
                "pattern_label": "Reference-Only Activity",
                "risk": "medium",
                "context": activity_context,
                "insight": (
                    "This activity does not have a clear primary business object. "
                    "That may indicate incomplete event-object modeling or unclear process ownership. "
                    f"{context_explanation}"
                ),
                "recommendation": build_data_driven_recommendation(
                    base_recommendation,
                    activity_context,
                ),
            })

        else:
            base_recommendation = (
                "Review the activity-object relationships and extend the classification rules "
                "if this pattern is relevant."
            )

            insights.append({
                "activity": activity,
                "pattern": pattern,
                "pattern_label": "Unclassified Activity",
                "risk": "unknown",
                "context": activity_context,
                "insight": (
                    "This activity could not be clearly classified with the current pattern logic. "
                    f"{context_explanation}"
                ),
                "recommendation": build_data_driven_recommendation(
                    base_recommendation,
                    activity_context,
                ),
            })

    return ActivityInsights(insights=insights)