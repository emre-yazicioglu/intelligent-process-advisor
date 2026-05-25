from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


EVENT_ID = "ocel:eid"
ACTIVITY = "ocel:activity"
TIMESTAMP = "ocel:timestamp"
OBJECT_ID = "ocel:oid"
OBJECT_TYPE = "ocel:type"

EXECUTION_MODE = "execution_mode"
PROCESS_VALUE = "process_value"


@dataclass(frozen=True)
class ExecutiveKpis:
    total_process_value: float
    automation_rate: float
    avg_throughput_days: float
    automation_candidates: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_process_value": self.total_process_value,
            "automation_rate": self.automation_rate,
            "avg_throughput_days": self.avg_throughput_days,
            "automation_candidates": self.automation_candidates,
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


def calculate_total_process_value(objects: pd.DataFrame) -> float:
    validate_required_columns(
        objects,
        {OBJECT_TYPE, PROCESS_VALUE},
        "objects",
    )

    purchase_orders = objects[objects[OBJECT_TYPE] == "purchase_order"].copy()

    purchase_orders[PROCESS_VALUE] = pd.to_numeric(
        purchase_orders[PROCESS_VALUE],
        errors="coerce",
    ).fillna(0)

    return float(purchase_orders[PROCESS_VALUE].sum())


def calculate_automation_rate(events: pd.DataFrame) -> float:
    validate_required_columns(
        events,
        {EXECUTION_MODE},
        "events",
    )

    total_events = len(events)

    if total_events == 0:
        return 0.0

    automated_events = events[
        events[EXECUTION_MODE].isin(["automated", "ai_assisted"])
    ]

    return round(len(automated_events) / total_events * 100, 2)


def calculate_avg_throughput_days(
    events: pd.DataFrame,
    relations: pd.DataFrame,
    case_object_type: str = "purchase_order",
) -> float:
    validate_required_columns(
        events,
        {EVENT_ID, TIMESTAMP},
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
        return 0.0

    case_events = case_relations.merge(
        events[[EVENT_ID, TIMESTAMP]],
        on=EVENT_ID,
        how="left",
    )

    missing_events = case_events[case_events[TIMESTAMP].isna()][EVENT_ID].unique()

    if len(missing_events) > 0:
        raise ValueError(
            "relations contains event IDs not found in events: "
            f"{sorted(missing_events.tolist())}"
        )

    case_events[TIMESTAMP] = pd.to_datetime(case_events[TIMESTAMP])

    throughput = (
        case_events.groupby(OBJECT_ID)[TIMESTAMP]
        .agg(["min", "max"])
        .reset_index()
    )

    throughput["throughput_days"] = (
        throughput["max"] - throughput["min"]
    ).dt.total_seconds() / 86400

    return round(float(throughput["throughput_days"].mean()), 2)


def calculate_automation_candidates(activity_insights: Any) -> int:
    """
    Count activities that have meaningful automation or transformation potential.

    We intentionally exclude low-risk single-object monitoring recommendations
    from this KPI so that the number reflects stronger opportunity signals.
    """

    candidate_risks = {"medium", "high"}

    return sum(
        1
        for insight in activity_insights.insights
        if insight.get("risk") in candidate_risks
    )


def calculate_executive_kpis(
    events: pd.DataFrame,
    objects: pd.DataFrame,
    relations: pd.DataFrame,
    activity_insights: Any,
    case_object_type: str = "purchase_order",
) -> ExecutiveKpis:
    return ExecutiveKpis(
        total_process_value=calculate_total_process_value(objects),
        automation_rate=calculate_automation_rate(events),
        avg_throughput_days=calculate_avg_throughput_days(
            events=events,
            relations=relations,
            case_object_type=case_object_type,
        ),
        automation_candidates=calculate_automation_candidates(activity_insights),
    )