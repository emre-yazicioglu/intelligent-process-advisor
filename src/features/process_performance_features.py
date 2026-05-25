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
class ProcessPerformanceFeatures:
    """
    Performance intelligence signals per activity.

    This layer identifies operational pain signals:
    - rework
    - waiting time
    - bottleneck risk
    - variant spread
    - stability

    These signals support automation prioritization and operational improvement.
    """

    activity_performance: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_performance": self.activity_performance,
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


def classify_bottleneck_risk(avg_waiting_time_hours: float) -> str:
    """
    Waiting time after an activity is used as a bottleneck signal.

    This does not prove the activity itself is the root cause, but it indicates
    that cases tend to wait after this step before progressing.
    """

    if avg_waiting_time_hours >= 72:
        return "high"

    if avg_waiting_time_hours >= 24:
        return "medium"

    return "low"


def classify_stability_score(
    rework_rate: float,
    variant_spread: int,
    average_position_std: float,
) -> int:
    """
    Higher score means the activity behaves more consistently.

    Stable activities are usually easier to standardize and automate.
    Low stability may indicate process variation, exception handling,
    or human judgment requirements.
    """

    score = 100

    if rework_rate >= 30:
        score -= 35
    elif rework_rate >= 10:
        score -= 20
    elif rework_rate > 0:
        score -= 10

    if variant_spread >= 12:
        score -= 25
    elif variant_spread >= 6:
        score -= 15
    elif variant_spread >= 3:
        score -= 5

    if average_position_std >= 3:
        score -= 20
    elif average_position_std >= 1.5:
        score -= 10

    return max(0, min(score, 100))


def extract_process_performance_features(
    events: pd.DataFrame,
    relations: pd.DataFrame,
    case_object_type: str = "purchase_order",
) -> ProcessPerformanceFeatures:
    """
    Extract process performance signals using one object type as traversal anchor.

    For this prototype:
    - purchase_order is used as the traversal anchor
    - each purchase order creates one PO-based process instance
    - performance is calculated from ordered event sequences
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

    case_events["activity_position"] = (
        case_events.groupby(OBJECT_ID).cumcount() + 1
    )

    case_events["next_timestamp"] = case_events.groupby(OBJECT_ID)[TIMESTAMP].shift(-1)

    case_events["waiting_time_hours"] = (
        case_events["next_timestamp"] - case_events[TIMESTAMP]
    ).dt.total_seconds() / 3600

    case_events["waiting_time_hours"] = case_events["waiting_time_hours"].fillna(0)

    total_cases = int(case_events[OBJECT_ID].nunique())

    activity_frequency = (
        case_events.groupby(ACTIVITY)
        .size()
        .reset_index(name="frequency")
    )

    activity_waiting_time = (
        case_events.groupby(ACTIVITY)["waiting_time_hours"]
        .mean()
        .round(2)
        .reset_index(name="average_waiting_time_hours")
    )

    activity_position = (
        case_events.groupby(ACTIVITY)["activity_position"]
        .agg(
            average_position="mean",
            average_position_std="std",
        )
        .round(2)
        .reset_index()
    )

    activity_position["average_position_std"] = (
        activity_position["average_position_std"].fillna(0)
    )

    activity_rework = (
        case_events.groupby([OBJECT_ID, ACTIVITY])
        .size()
        .reset_index(name="activity_count_in_case")
    )

    activity_rework["is_rework"] = activity_rework["activity_count_in_case"] > 1

    rework_summary = (
        activity_rework.groupby(ACTIVITY)
        .agg(
            rework_cases=("is_rework", "sum"),
            cases_with_activity=(OBJECT_ID, "count"),
        )
        .reset_index()
    )

    rework_summary["rework_rate"] = (
        rework_summary["rework_cases"]
        / rework_summary["cases_with_activity"]
        * 100
    ).round(2)

    case_variants = (
        case_events.groupby(OBJECT_ID)[ACTIVITY]
        .apply(lambda activities: tuple(activities.tolist()))
        .reset_index(name="variant")
    )

    activity_variant_rows: list[dict[str, Any]] = []

    for _, row in case_variants.iterrows():
        variant = row["variant"]
        unique_activities = set(variant)

        for activity in unique_activities:
            activity_variant_rows.append({
                "activity": activity,
                "variant": variant,
            })

    activity_variant_df = pd.DataFrame(activity_variant_rows)

    if activity_variant_df.empty:
        variant_spread = pd.DataFrame(columns=["activity", "variant_spread"])
    else:
        variant_spread = (
            activity_variant_df.groupby("activity")["variant"]
            .nunique()
            .reset_index(name="variant_spread")
        )

    performance_df = activity_frequency.merge(
        activity_waiting_time,
        on=ACTIVITY,
        how="left",
    ).merge(
        activity_position,
        on=ACTIVITY,
        how="left",
    ).merge(
        rework_summary,
        on=ACTIVITY,
        how="left",
    ).merge(
        variant_spread,
        left_on=ACTIVITY,
        right_on="activity",
        how="left",
    )

    performance_df = performance_df.drop(columns=["activity"], errors="ignore")

    performance_df["activity"] = performance_df[ACTIVITY]

    performance_df["rework_cases"] = (
        performance_df["rework_cases"].fillna(0).astype(int)
    )

    performance_df["cases_with_activity"] = (
        performance_df["cases_with_activity"].fillna(0).astype(int)
    )

    performance_df["rework_rate"] = (
        performance_df["rework_rate"].fillna(0).astype(float)
    )

    performance_df["variant_spread"] = (
        performance_df["variant_spread"].fillna(0).astype(int)
    )

    performance_df["average_waiting_time_hours"] = (
        performance_df["average_waiting_time_hours"].fillna(0).astype(float)
    )

    performance_df["average_position"] = (
        performance_df["average_position"].fillna(0).astype(float)
    )

    performance_df["average_position_std"] = (
        performance_df["average_position_std"].fillna(0).astype(float)
    )

    performance_df["bottleneck_risk"] = performance_df[
        "average_waiting_time_hours"
    ].apply(classify_bottleneck_risk)

    performance_df["stability_score"] = performance_df.apply(
        lambda row: classify_stability_score(
            rework_rate=row["rework_rate"],
            variant_spread=row["variant_spread"],
            average_position_std=row["average_position_std"],
        ),
        axis=1,
    )

    performance_df["total_cases"] = total_cases

    risk_order = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    performance_df["bottleneck_risk_rank"] = (
        performance_df["bottleneck_risk"].map(risk_order).fillna(0)
    )

    performance_df = performance_df.sort_values(
        [
            "bottleneck_risk_rank",
            "average_waiting_time_hours",
            "rework_rate",
            "variant_spread",
        ],
        ascending=[False, False, False, False],
    )

    performance_df = performance_df.drop(columns=["bottleneck_risk_rank"])

    display_columns = [
        "activity",
        "frequency",
        "average_waiting_time_hours",
        "bottleneck_risk",
        "rework_cases",
        "cases_with_activity",
        "rework_rate",
        "variant_spread",
        "average_position",
        "average_position_std",
        "stability_score",
        "total_cases",
    ]

    return ProcessPerformanceFeatures(
        activity_performance=performance_df[display_columns].to_dict(orient="records"),
    )