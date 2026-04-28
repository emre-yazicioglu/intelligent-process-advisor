from ingestion.load_ocel import load_ocel_tables
from features.activity_object_features import extract_activity_object_features
from features.activity_interaction_patterns import (
    classify_activity_interaction_patterns,
)
from features.activity_insights import generate_activity_insights
from export.export_insights import export_to_json


def main() -> None:
    ocel_tables = load_ocel_tables("data/p2p_sample")

    activity_object_features = extract_activity_object_features(
        events=ocel_tables["events"],
        relations=ocel_tables["relations"],
    )

    interaction_patterns = classify_activity_interaction_patterns(
        features=activity_object_features,
    )

    activity_insights = generate_activity_insights(
        patterns=interaction_patterns,
    )

    print("Activity Object Features")
    print(activity_object_features.to_dict())

    print("\nActivity Interaction Patterns")
    print(interaction_patterns.to_dict())

    print("\nActivity Insights")
    print(activity_insights.to_dict())

    export_to_json(
        data=activity_insights.to_dict(),
        output_path="outputs/activity_insights.json",
    )

    print("\nExport completed: outputs/activity_insights.json")


if __name__ == "__main__":
    main()