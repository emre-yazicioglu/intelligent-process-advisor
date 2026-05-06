from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from features.activity_context_features import ActivityContextFeatures
from features.activity_interaction_patterns import ActivityInteractionPatterns


@dataclass(frozen=True)
class AutomationOpportunityFeatures:
    """
    Automation opportunity assessment per activity.

    This layer translates process intelligence signals into automation decision support.

    It does not use AI yet.
    It creates structured, explainable signals that an AI layer can later reason over.
    """

    opportunities: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunities": self.opportunities,
        }


def classify_automation_type(
    pattern: str,
    automation_score: int,
    percentage_of_total_events: float,
    variants_containing_activity: int,
) -> str:
    """
    Decide the most suitable automation direction.

    This is intentionally simple and explainable.
    Later, an AI layer can use this structured output for richer recommendations.
    """

    if automation_score < 40:
        return "human_review"

    if pattern == "multi_object_join":
        return "ai_assisted"

    if pattern == "item_level_activity" and percentage_of_total_events >= 15:
        return "workflow_or_rpa"

    if pattern == "single_object_primary" and variants_containing_activity <= 2:
        return "rpa_or_workflow"

    if pattern == "primary_with_reference":
        return "human_in_the_loop"

    return "human_in_the_loop"


def extract_automation_opportunity_features(
    patterns: ActivityInteractionPatterns,
    context_features: ActivityContextFeatures,
) -> AutomationOpportunityFeatures:
    """
    Score activities for automation opportunity.

    Business logic:
    - frequent activities have higher automation value
    - early activities can affect downstream process performance
    - standardized activities are easier to automate
    - multi-object matching activities may need AI-assisted automation
    - unclear or highly dependent activities should keep human oversight
    """

    opportunities: list[dict[str, Any]] = []

    for activity, pattern in patterns.activity_patterns.items():
        context = context_features.activity_context.get(activity)

        if context is None:
            opportunities.append({
                "activity": activity,
                "pattern": pattern,
                "automation_score": 0,
                "automation_candidate": False,
                "recommended_automation_type": "insufficient_data",
                "reasoning": [
                    "No contextual activity features were available for this activity."
                ],
            })
            continue

        frequency = context["frequency"]
        percentage_of_total_events = context["percentage_of_total_events"]
        average_position = context["average_position"]
        variants_containing_activity = context["variants_containing_activity"]

        score = 0
        reasoning: list[str] = []

        if percentage_of_total_events >= 20:
            score += 30
            reasoning.append(
                "High event share indicates strong automation value."
            )
        elif percentage_of_total_events >= 10:
            score += 20
            reasoning.append(
                "Medium event share indicates possible automation value."
            )
        else:
            score += 10
            reasoning.append(
                "Low event share reduces automation priority."
            )

        if average_position <= 2:
            score += 20
            reasoning.append(
                "Early process position means improvements can influence downstream flow."
            )
        elif average_position <= 4:
            score += 10
            reasoning.append(
                "Mid-process position may still influence process performance."
            )

        if variants_containing_activity <= 1:
            score += 20
            reasoning.append(
                "Activity appears in a limited number of variants, suggesting standardization."
            )
        elif variants_containing_activity <= 3:
            score += 10
            reasoning.append(
                "Activity appears across several variants, suggesting moderate standardization."
            )
        else:
            reasoning.append(
                "Activity appears across many variants, which may reduce automation simplicity."
            )

        if pattern == "single_object_primary":
            score += 20
            reasoning.append(
                "Single-object structure is usually easier to automate."
            )

        elif pattern == "item_level_activity":
            score += 15
            reasoning.append(
                "Item-level activity can create repetitive operational workload."
            )

        elif pattern == "multi_object_join":
            score += 15
            reasoning.append(
                "Multi-object activity may represent matching or reconciliation work."
            )

        elif pattern == "primary_with_reference":
            score += 10
            reasoning.append(
                "Reference dependency suggests automation may need validation logic."
            )

        elif pattern == "reference_only":
            score -= 10
            reasoning.append(
                "Reference-only structure suggests unclear ownership or incomplete modeling."
            )

        automation_score = max(0, min(score, 100))

        recommended_automation_type = classify_automation_type(
            pattern=pattern,
            automation_score=automation_score,
            percentage_of_total_events=percentage_of_total_events,
            variants_containing_activity=variants_containing_activity,
        )

        opportunities.append({
            "activity": activity,
            "pattern": pattern,
            "frequency": frequency,
            "percentage_of_total_events": percentage_of_total_events,
            "average_position": average_position,
            "variants_containing_activity": variants_containing_activity,
            "automation_score": automation_score,
            "automation_candidate": automation_score >= 50,
            "recommended_automation_type": recommended_automation_type,
            "reasoning": reasoning,
        })

    opportunities = sorted(
        opportunities,
        key=lambda row: row["automation_score"],
        reverse=True,
    )

    return AutomationOpportunityFeatures(opportunities=opportunities)