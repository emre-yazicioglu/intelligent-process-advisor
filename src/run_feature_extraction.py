from ingestion.load_ocel import load_ocel_tables
from features.activity_object_features import extract_activity_object_features


def main() -> None:
    ocel_tables = load_ocel_tables("data/p2p_sample")

    features = extract_activity_object_features(
        events=ocel_tables["events"],
        relations=ocel_tables["relations"],
    )

    print(features.to_dict())


if __name__ == "__main__":
    main()