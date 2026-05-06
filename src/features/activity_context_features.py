from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


EVENT_ID = "ocel:eid"
ACTIVITY = "ocel:activity"
TIMESTAMP = "ocel:timestamp"
OBJECT_ID = "ocel:oid"
OBJECT_TYPE = "ocel:type"


@dataclass(frozen=True)
class ActivityContextFeatures:
    """
    Contextual activity intelligence.

    These features explain how important an activity is inside the process:
    - how often it happens
    - how much of the event log it represents
    - where it usually appears in the case flow
    - how many process variants contain it
    """

    activity_context: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_context": self.activity_context,
        }


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    dataframe_name: str,
) -> None:
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"{dataframe_name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def extract_activity_context_features(
    events: pd.DataFrame,
    relations: pd.DataFrame,
    case_object_type: str = "purchase_order",
) -> ActivityContextFeatures:
    """
    Extract contextual intelligence per activity.

    We use the same case anchor as process_flow_features:
    purchase_order.

    Why:
    OCEL does not always have one simple case ID.
    For this prototype, purchase_order gives us a stable process view.
    """

    validate_required_columns(
        events,
        {EVENT_ID, ACTIVITY, TIMESTAMP},
        "events",
    )

    validate_required_columns(
        relations,
        {EVENT_ID, OBJECT_ID, OBJECT_TYPE},
        "relations",
    )

    case_relations = relations[
        relations[OBJECT_TYPE] == case_object_type
    ][[EVENT_ID, OBJECT_ID]].copy()

    if case_relations.empty:
        raise ValueError(
            f"No relations found for case_object_type='{case_object_type}'"
        )

    case_events = case_relations.merge(
        events[[EVENT_ID, ACTIVITY, TIMESTAMP]],
        on=EVENT_ID,
        how="left",
    )

    missing_events = case_events[case_events[ACTIVITY].isna()][EVENT_ID].unique()

    if len(missing_events) > 0:
        raise ValueError(
            "relations contains event IDs not found in events: "
            f"{sorted(missing_events.tolist())}"
        )

    case_events[TIMESTAMP] = pd.to_datetime(case_events[TIMESTAMP])

    case_events = case_events.sort_values(
        [OBJECT_ID, TIMESTAMP, EVENT_ID]
    ).reset_index(drop=True)

    total_events = len(case_events)
    total_cases = int(case_events[OBJECT_ID].nunique())

    case_events["position_in_case"] = (
        case_events.groupby(OBJECT_ID).cumcount() + 1
    )

    activity_counts = (
        case_events[ACTIVITY]
        .value_counts()
        .rename_axis("activity")
        .reset_index(name="frequency")
    )

    average_positions = (
        case_events.groupby(ACTIVITY)["position_in_case"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={ACTIVITY: "activity", "position_in_case": "average_position"})
    )

    case_variants = (
        case_events.groupby(OBJECT_ID)[ACTIVITY]
        .apply(lambda activities: tuple(activities.tolist()))
        .reset_index()
        .rename(columns={OBJECT_ID: "case_id", ACTIVITY: "variant"})
    )

    variant_rows: list[dict[str, Any]] = []

    for variant in case_variants["variant"].unique():
        variant_activities = set(variant)

        for activity in variant_activities:
            variant_rows.append({
                "activity": activity,
                "variant": variant,
            })

    activity_variant_counts = (
        pd.DataFrame(variant_rows)
        .groupby("activity")["variant"]
        .nunique()
        .reset_index()
        .rename(columns={"variant": "variants_containing_activity"})
    )

    context_df = activity_counts.merge(
        average_positions,
        on="activity",
        how="left",
    ).merge(
        activity_variant_counts,
        on="activity",
        how="left",
    )

    context_df["percentage_of_total_events"] = (
        context_df["frequency"] / total_events * 100
    ).round(2)

    context_df["total_cases"] = total_cases

    context_df["variants_containing_activity"] = (
        context_df["variants_containing_activity"]
        .fillna(0)
        .astype(int)
    )

    activity_context = {
        row["activity"]: {
            "frequency": int(row["frequency"]),
            "percentage_of_total_events": float(row["percentage_of_total_events"]),
            "average_position": float(row["average_position"]),
            "variants_containing_activity": int(row["variants_containing_activity"]),
            "total_cases": int(row["total_cases"]),
        }
        for _, row in context_df.iterrows()
    }

    return ActivityContextFeatures(activity_context=activity_context)