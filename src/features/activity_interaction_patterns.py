from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from features.activity_object_features import ActivityObjectFeatures


ITEM_OBJECT_TYPE = "item"
PRIMARY_QUALIFIER = "primary"
REFERENCE_QUALIFIER = "reference"


@dataclass(frozen=True)
class ActivityInteractionPatterns:
    """
    Classification layer that explains how each activity interacts
    with object types.

    This turns raw activity-object features into higher-level
    Process Intelligence semantics.
    """

    activity_patterns: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity_patterns": self.activity_patterns,
        }


def classify_activity_interaction_patterns(
    features: ActivityObjectFeatures,
) -> ActivityInteractionPatterns:
    """
    Classify each activity into an interaction pattern.

    Input example:
    {
        "Receive Goods": {
            "item": ["primary"],
            "purchase_order": ["reference"]
        }
    }

    Output example:
    {
        "Receive Goods": "item_level_activity"
    }
    """

    activity_patterns: dict[str, str] = {}

    for activity, object_type_qualifiers in features.activity_object_type_qualifiers.items():
        object_types = set(object_type_qualifiers.keys())

        all_qualifiers = {
            qualifier
            for qualifiers in object_type_qualifiers.values()
            for qualifier in qualifiers
        }

        has_item = ITEM_OBJECT_TYPE in object_types
        has_primary = PRIMARY_QUALIFIER in all_qualifiers
        has_reference = REFERENCE_QUALIFIER in all_qualifiers
        object_type_count = len(object_types)

        # Highest priority:
        # If the activity touches item-level objects, it is item-level.
        # This matters because item-level behavior often indicates
        # granularity below document/header level.
        if has_item:
            pattern = "item_level_activity"

        # One object type, only primary relationship.
        # Example:
        # Pay Invoice -> invoice -> primary
        elif object_type_count == 1 and has_primary and not has_reference:
            pattern = "single_object_primary"

        # Multiple object types with primary and reference relationships.
        # Example:
        # Match Invoice -> invoice primary + purchase_order reference
        elif object_type_count > 1 and has_primary and has_reference:
            pattern = "multi_object_join"

        # Primary activity with supporting/reference context.
        # This is kept as a separate fallback semantic category.
        elif has_primary and has_reference:
            pattern = "primary_with_reference"

        # Edge case:
        # Activity only references objects but has no primary object.
        # This may indicate weak modeling or incomplete event semantics.
        elif has_reference and not has_primary:
            pattern = "reference_only"

        # Edge case:
        # No meaningful qualifier structure found.
        else:
            pattern = "unknown"

        activity_patterns[activity] = pattern

    # Stable output order for reproducibility and clean Git diffs.
    activity_patterns = dict(sorted(activity_patterns.items()))

    return ActivityInteractionPatterns(activity_patterns=activity_patterns)