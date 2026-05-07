from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from features.automation_opportunity_features import AutomationOpportunityFeatures


@dataclass(frozen=True)
class AutomationDecisionClusters:
    """
    Groups automation opportunities into decision clusters.

    This layer answers a business question:

    "What kind of automation should we consider for each activity?"

    It prepares the structured decision layer that an AI advisor can later explain.
    """

    clusters: dict[str, list[dict[str, Any]]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "clusters": self.clusters,
        }


def classify_decision_cluster(opportunity: dict[str, Any]) -> str:
    """
    Classify one activity into an automation decision cluster.

    The logic is intentionally explainable.
    This is not AI yet. This is deterministic process intelligence.
    """

    automation_score = opportunity["automation_score"]
    automation_type = opportunity["recommended_automation_type"]
    pattern = opportunity["pattern"]

    if automation_score < 40:
        return "low_automation_potential"

    if automation_type in {"rpa_or_workflow", "workflow_or_rpa"}:
        return "rpa_or_workflow_automation"

    if automation_type == "ai_assisted":
        return "ai_assisted_automation"

    if automation_type == "human_in_the_loop":
        return "human_in_the_loop"

    if pattern == "multi_object_join":
        return "ai_assisted_automation"

    return "human_in_the_loop"


def explain_cluster(cluster: str) -> str:
    """
    Business explanation for each cluster.

    These explanations will later help the AI advisor produce better answers.
    """

    explanations = {
        "rpa_or_workflow_automation": (
            "Activities in this cluster appear suitable for rule-based automation, "
            "workflow automation, or RPA because they show repeatable structure and "
            "sufficient process relevance."
        ),
        "ai_assisted_automation": (
            "Activities in this cluster may require AI assistance because they involve "
            "matching, reconciliation, interpretation, or multi-object dependencies."
        ),
        "human_in_the_loop": (
            "Activities in this cluster should keep human oversight because they may "
            "depend on judgment, validation, exceptions, or unclear process conditions."
        ),
        "low_automation_potential": (
            "Activities in this cluster currently show limited automation potential "
            "based on frequency, process position, standardization, or structural complexity. "
            "They should not be prioritized for automation unless business effort, cost, "
            "or exception impact is high."
        ),
    }

    return explanations.get(
        cluster,
        "No explanation is available for this cluster.",
    )


def extract_automation_decision_clusters(
    automation_features: AutomationOpportunityFeatures,
) -> AutomationDecisionClusters:
    """
    Build automation decision clusters from scored opportunities.

    Output structure:
    - rpa_or_workflow_automation
    - ai_assisted_automation
    - human_in_the_loop
    - low_automation_potential
    """

    clusters: dict[str, list[dict[str, Any]]] = {
        "rpa_or_workflow_automation": [],
        "ai_assisted_automation": [],
        "human_in_the_loop": [],
        "low_automation_potential": [],
    }

    for opportunity in automation_features.opportunities:
        cluster = classify_decision_cluster(opportunity)

        clustered_opportunity = {
            **opportunity,
            "decision_cluster": cluster,
            "cluster_explanation": explain_cluster(cluster),
        }

        clusters[cluster].append(clustered_opportunity)

    return AutomationDecisionClusters(clusters=clusters)