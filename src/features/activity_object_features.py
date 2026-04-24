from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


EVENT_ID = "ocel:eid"
ACTIVITY = "ocel:activity"
OBJECT_TYPE = "ocel:type"
QUALIFIER = "ocel:qualifier"


@dataclass(frozen=True)
class ActivityObjectFeatures:
    """
    Reusable Process Intelligence features describing how activities
    interact with object types and relationship qualifiers.
    """

    activity_object_types: dict[str, list[str]]
    activity_object_type_qualifiers: dict[str, dict[str, list[str]]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_object_types": self.activity_object_types,
            "activity_object_type_qualifiers": self.activity_object_type_qualifiers,
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


def extract_activity_object_features(
    events: pd.DataFrame,
    relations: pd.DataFrame,
) -> ActivityObjectFeatures:
    """
    Extract activity-level object interaction features from OCEL tables.

    Parameters
    ----------
    events:
        OCEL events table containing event IDs and activity names.

    relations:
        OCEL relations table connecting events to objects, object types,
        and qualifiers.

    Returns
    -------
    ActivityObjectFeatures
        Feature object containing:
        - activity -> related object types
        - activity -> object type -> qualifiers
    """

    validate_required_columns(
        events,
        {EVENT_ID, ACTIVITY},
        "events",
    )

    validate_required_columns(
        relations,
        {EVENT_ID, OBJECT_TYPE, QUALIFIER},
        "relations",
    )

    unknown_event_ids = set(relations[EVENT_ID]) - set(events[EVENT_ID])

    if unknown_event_ids:
        raise ValueError(
            "relations contains event IDs not found in events: "
            f"{sorted(unknown_event_ids)}"
        )

    merged = relations.merge(
        events[[EVENT_ID, ACTIVITY]],
        on=EVENT_ID,
        how="left",
    )

    activity_object_types = {
    activity: object_types
    for activity, object_types in sorted(
        (
            merged.groupby(ACTIVITY)[OBJECT_TYPE]
            .apply(lambda values: sorted(values.dropna().unique().tolist()))
            .to_dict()
            .items()
        )
    )
    }

    activity_object_type_qualifiers = {}

    grouped = merged.groupby([ACTIVITY, OBJECT_TYPE])[QUALIFIER]

    for (activity, object_type), qualifiers in grouped:
        activity_object_type_qualifiers.setdefault(activity, {})
        activity_object_type_qualifiers[activity][object_type] = sorted(
            qualifiers.dropna().unique().tolist()
        )

    activity_object_type_qualifiers = {
        activity: {
            object_type: qualifiers
            for object_type, qualifiers in sorted(object_dict.items())
        }
        for activity, object_dict in sorted(activity_object_type_qualifiers.items())
    }

    return ActivityObjectFeatures(
        activity_object_types=activity_object_types,
        activity_object_type_qualifiers=activity_object_type_qualifiers,
    )

    return ActivityObjectFeatures(
        activity_object_types=activity_object_types,
        activity_object_type_qualifiers=activity_object_type_qualifiers,
    )