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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def get_performance_lookup(performance_features: Any | None) -> dict[str, dict[str, Any]]:
    if performance_features is None:
        return {}

    activity_performance = getattr(
        performance_features,
        "activity_performance",
        [],
    )

    return {
        row["activity"]: row
        for row in activity_performance
        if isinstance(row, dict) and "activity" in row
    }


def classify_automation_type(
    activity: str,
    pattern: str,
    automation_score: int,
    percentage_of_total_events: float,
    variants_containing_activity: int,
    rework_rate: float,
    bottleneck_risk: str,
    stability_score: float,
) -> str:
    """
    Decide the most suitable automation direction.

    Business meaning:
    - stable, repetitive, structured work fits RPA/workflow automation
    - reconciliation-heavy or exception-heavy work fits AI-assisted automation
    - unstable, high-impact work may still need human-in-the-loop control
    """

    activity_lower = activity.lower()

    is_invoice_or_matching = (
        "invoice" in activity_lower
        or "match" in activity_lower
        or "mismatch" in activity_lower
    )

    has_pain_signal = (
        rework_rate >= 10
        or bottleneck_risk == "high"
        or stability_score < 70
    )

    if pattern == "multi_object_join" and has_pain_signal:
        return "ai_assisted"

    if is_invoice_or_matching and has_pain_signal:
        return "ai_assisted"

    if "mismatch" in activity_lower:
        return "human_in_the_loop"

    if pattern == "single_object_primary" and automation_score >= 60:
        return "rpa_or_workflow"

    if pattern == "item_level_activity" and percentage_of_total_events >= 8:
        return "workflow_or_rpa"

    if pattern == "primary_with_reference" and has_pain_signal:
        return "human_in_the_loop"

    if automation_score >= 60 and variants_containing_activity <= 5:
        return "rpa_or_workflow"

    if automation_score >= 50:
        return "human_in_the_loop"

    return "low_automation_potential"


def extract_automation_opportunity_features(
    patterns: ActivityInteractionPatterns,
    context_features: ActivityContextFeatures,
    performance_features: Any | None = None,
) -> AutomationOpportunityFeatures:
    """
    Score activities for automation opportunity.

    Business logic:
    - frequent activities have higher automation value
    - early activities can affect downstream process performance
    - standardized activities are easier to automate with RPA/workflow
    - rework-heavy activities may be strong AI-assisted automation candidates
    - bottleneck activities may require automation, redesign, or human-in-the-loop support
    """

    opportunities: list[dict[str, Any]] = []
    performance_lookup = get_performance_lookup(performance_features)

    for activity, pattern in patterns.activity_patterns.items():
        context = context_features.activity_context.get(activity)

        if context is None:
            opportunities.append({
                "activity": activity,
                "pattern": pattern,
                "frequency": 0,
                "percentage_of_total_events": 0.0,
                "average_position": 0.0,
                "variants_containing_activity": 0,
                "rework_rate": 0.0,
                "bottleneck_risk": "unknown",
                "stability_score": 0.0,
                "automation_score": 0,
                "automation_candidate": False,
                "recommended_automation_type": "insufficient_data",
                "automation_value_driver": "insufficient_data",
                "reasoning": [
                    "No contextual activity features were available for this activity."
                ],
            })
            continue

        performance = performance_lookup.get(activity, {})

        frequency = context["frequency"]
        percentage_of_total_events = safe_float(
            context["percentage_of_total_events"]
        )
        average_position = safe_float(context["average_position"])
        variants_containing_activity = int(context["variants_containing_activity"])

        rework_rate = safe_float(
            performance.get(
                "rework_rate",
                performance.get("rework_percentage", 0.0),
            )
        )
        bottleneck_risk = str(performance.get("bottleneck_risk", "unknown"))
        stability_score = safe_float(performance.get("stability_score", 100.0))

        score = 0
        reasoning: list[str] = []

        # ---------------- VOLUME VALUE ----------------
        if percentage_of_total_events >= 15:
            score += 25
            reasoning.append(
                "High event share indicates strong automation value."
            )
        elif percentage_of_total_events >= 8:
            score += 18
            reasoning.append(
                "Medium event share indicates meaningful automation value."
            )
        else:
            score += 10
            reasoning.append(
                "Lower event share reduces pure volume-based automation priority."
            )

        # ---------------- PROCESS POSITION ----------------
        if average_position <= 2:
            score += 20
            reasoning.append(
                "Early process position means improvements can influence downstream flow."
            )
        elif average_position <= 5:
            score += 10
            reasoning.append(
                "Mid-process position may still influence process performance."
            )

        # ---------------- STANDARDIZATION ----------------
        if variants_containing_activity <= 3:
            score += 15
            reasoning.append(
                "Activity appears in a limited number of variants, suggesting automation simplicity."
            )
        elif variants_containing_activity <= 8:
            score += 8
            reasoning.append(
                "Activity appears across several variants, suggesting moderate standardization."
            )
        else:
            reasoning.append(
                "Activity appears across many variants, which reduces simple RPA suitability."
            )

        # ---------------- STRUCTURAL AUTOMATION FIT ----------------
        if pattern == "single_object_primary":
            score += 25
            reasoning.append(
                "Single-object structure is usually easier to automate with workflow or RPA."
            )

        elif pattern == "item_level_activity":
            score += 18
            reasoning.append(
                "Item-level activity can create repetitive operational workload."
            )

        elif pattern == "multi_object_join":
            score += 25
            reasoning.append(
                "Multi-object activity may represent matching, reconciliation, or validation work."
            )

        elif pattern == "primary_with_reference":
            score += 15
            reasoning.append(
                "Reference dependency suggests automation may need validation or orchestration logic."
            )

        elif pattern == "reference_only":
            score -= 10
            reasoning.append(
                "Reference-only structure suggests unclear ownership or incomplete modeling."
            )

        # ---------------- PERFORMANCE PAIN ----------------
        if rework_rate >= 20:
            score += 25
            reasoning.append(
                "High rework rate indicates strong opportunity for AI-assisted validation or exception handling."
            )
        elif rework_rate >= 10:
            score += 15
            reasoning.append(
                "Moderate rework rate suggests improvement potential through better validation or guided handling."
            )

        if bottleneck_risk == "high":
            score += 20
            reasoning.append(
                "High bottleneck risk indicates an operational pain point worth prioritizing."
            )
        elif bottleneck_risk == "medium":
            score += 10
            reasoning.append(
                "Medium bottleneck risk suggests possible improvement value."
            )

        if stability_score < 60:
            score += 15
            reasoning.append(
                "Low stability suggests the activity may need human-in-the-loop or AI-assisted control."
            )
        elif stability_score < 80:
            score += 8
            reasoning.append(
                "Moderate stability concerns suggest process control improvement potential."
            )

        automation_score = max(0, min(score, 100))

        recommended_automation_type = classify_automation_type(
            activity=activity,
            pattern=pattern,
            automation_score=automation_score,
            percentage_of_total_events=percentage_of_total_events,
            variants_containing_activity=variants_containing_activity,
            rework_rate=rework_rate,
            bottleneck_risk=bottleneck_risk,
            stability_score=stability_score,
        )

        if recommended_automation_type in {"rpa_or_workflow", "workflow_or_rpa"}:
            automation_value_driver = "standardization_and_volume"
        elif recommended_automation_type == "ai_assisted":
            automation_value_driver = "reconciliation_rework_or_exception_handling"
        elif recommended_automation_type == "human_in_the_loop":
            automation_value_driver = "controlled_decision_support"
        else:
            automation_value_driver = "low_priority"

        opportunities.append({
            "activity": activity,
            "pattern": pattern,
            "frequency": frequency,
            "percentage_of_total_events": percentage_of_total_events,
            "average_position": average_position,
            "variants_containing_activity": variants_containing_activity,
            "rework_rate": rework_rate,
            "bottleneck_risk": bottleneck_risk,
            "stability_score": stability_score,
            "automation_score": automation_score,
            "automation_candidate": automation_score >= 50,
            "recommended_automation_type": recommended_automation_type,
            "automation_value_driver": automation_value_driver,
            "reasoning": reasoning,
        })

    opportunities = sorted(
        opportunities,
        key=lambda row: row["automation_score"],
        reverse=True,
    )

    return AutomationOpportunityFeatures(opportunities=opportunities)