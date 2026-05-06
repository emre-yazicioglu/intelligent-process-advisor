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
class ProcessFlowFeatures:
    """
    Process flow analytics based on an object-centric event log.

    For the current P2P prototype, we use purchase_order as the process
    instance anchor. This allows us to calculate variants, start/end
    activities, and directly-follows relations.
    """

    case_object_type: str
    total_cases: int
    start_activities: list[dict[str, Any]]
    end_activities: list[dict[str, Any]]
    activity_frequency: list[dict[str, Any]]
    directly_follows: list[dict[str, Any]]
    variants: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_object_type": self.case_object_type,
            "total_cases": self.total_cases,
            "start_activities": self.start_activities,
            "end_activities": self.end_activities,
            "activity_frequency": self.activity_frequency,
            "directly_follows": self.directly_follows,
            "variants": self.variants,
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


def build_count_table(
    series: pd.Series,
    label_column: str,
    percentage_base: int | None = None,
) -> pd.DataFrame:
    """
    Build a stable count + percentage table.

    This avoids pandas version-specific issues around value_counts()
    column names after reset_index().
    """

    count_table = (
        series.value_counts()
        .rename_axis(label_column)
        .reset_index(name="count")
    )

    count_table["count"] = pd.to_numeric(count_table["count"])

    if percentage_base is None:
        percentage_base = int(count_table["count"].sum())

    if percentage_base == 0:
        count_table["percentage"] = 0.0
    else:
        count_table["percentage"] = (
            count_table["count"] / percentage_base * 100
        ).round(2)

    return count_table


def extract_process_flow_features(
    events: pd.DataFrame,
    relations: pd.DataFrame,
    case_object_type: str = "purchase_order",
) -> ProcessFlowFeatures:
    """
    Extract process-flow analytics using one object type as the process anchor.

    In traditional process mining, variants are usually calculated using a case ID.
    In OCEL, there is not always one universal case ID.

    For this prototype, we anchor the flow on one object type:
    - P2P example: purchase_order
    - O2C example later: sales_order
    - ticketing example later: ticket
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

    total_cases = int(case_events[OBJECT_ID].nunique())

    activity_frequency = build_count_table(
        series=case_events[ACTIVITY],
        label_column="activity",
    )

    start_events = (
        case_events.groupby(OBJECT_ID)
        .first()
        .reset_index()
    )

    start_activities = build_count_table(
        series=start_events[ACTIVITY],
        label_column="activity",
        percentage_base=total_cases,
    )

    end_events = (
        case_events.groupby(OBJECT_ID)
        .last()
        .reset_index()
    )

    end_activities = build_count_table(
        series=end_events[ACTIVITY],
        label_column="activity",
        percentage_base=total_cases,
    )

    case_events["next_activity"] = case_events.groupby(OBJECT_ID)[ACTIVITY].shift(-1)

    directly_follows_events = case_events.dropna(subset=["next_activity"]).copy()

    directly_follows_events["transition"] = (
        directly_follows_events[ACTIVITY]
        + " → "
        + directly_follows_events["next_activity"]
    )

    directly_follows = build_count_table(
        series=directly_follows_events["transition"],
        label_column="transition",
    )

    case_variants = (
        case_events.groupby(OBJECT_ID)[ACTIVITY]
        .apply(lambda activities: " → ".join(activities.tolist()))
        .reset_index()
        .rename(columns={OBJECT_ID: "case_id", ACTIVITY: "variant"})
    )

    variants = build_count_table(
        series=case_variants["variant"],
        label_column="variant",
        percentage_base=total_cases,
    )

    return ProcessFlowFeatures(
        case_object_type=case_object_type,
        total_cases=total_cases,
        start_activities=start_activities.to_dict(orient="records"),
        end_activities=end_activities.to_dict(orient="records"),
        activity_frequency=activity_frequency.to_dict(orient="records"),
        directly_follows=directly_follows.to_dict(orient="records"),
        variants=variants.to_dict(orient="records"),
    )