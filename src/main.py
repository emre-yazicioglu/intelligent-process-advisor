import argparse

from ingestion.load_ocel import load_ocel_tables
from features.activity_object_features import extract_activity_object_features
from features.activity_interaction_patterns import (
    classify_activity_interaction_patterns,
)
from features.activity_insights import generate_activity_insights
from export.export_insights import export_to_json


def run_pipeline(data_path: str) -> None:
    print("Loading data...")
    ocel_tables = load_ocel_tables(data_path)

    print("Extracting features...")
    features = extract_activity_object_features(
        events=ocel_tables["events"],
        relations=ocel_tables["relations"],
    )

    print("Classifying interaction patterns...")
    patterns = classify_activity_interaction_patterns(features)

    print("Generating insights...")
    insights = generate_activity_insights(patterns)

    print("Exporting results...")
    export_to_json(
        data=insights.to_dict(),
        output_path="outputs/activity_insights.json",
    )

    print("Done.")
    print("Output: outputs/activity_insights.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Intelligent Process Advisor CLI"
    )

    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to OCEL data folder",
    )

    args = parser.parse_args()

    run_pipeline(args.data)


if __name__ == "__main__":
    main()