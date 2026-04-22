from pathlib import Path
from typing import Any, Dict

import pandas as pd


def load_ocel_tables(data_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load OCEL tables from a folder containing:
    - events.csv
    - objects.csv
    - relations.csv
    """
    base_path = Path(data_dir)

    events_path = base_path / "events.csv"
    objects_path = base_path / "objects.csv"
    relations_path = base_path / "relations.csv"

    required_files = [events_path, objects_path, relations_path]
    missing_files = [str(file) for file in required_files if not file.exists()]

    if missing_files:
        raise FileNotFoundError(f"Missing required files: {missing_files}")

    events_df = pd.read_csv(events_path)
    objects_df = pd.read_csv(objects_path)
    relations_df = pd.read_csv(relations_path)

    return {
        "events": events_df,
        "objects": objects_df,
        "relations": relations_df,
    }


def summarize_ocel_tables(ocel_tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Return a basic summary of the OCEL tables.
    """
    events_df = ocel_tables["events"]
    objects_df = ocel_tables["objects"]
    relations_df = ocel_tables["relations"]

    summary = {
        "events_count": len(events_df),
        "objects_count": len(objects_df),
        "relations_count": len(relations_df),
        "activity_count": events_df["ocel:activity"].nunique(),
        "activities": sorted(events_df["ocel:activity"].dropna().unique().tolist()),
        "object_types": sorted(objects_df["ocel:type"].dropna().unique().tolist()),
    }

    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    """
    Print a readable summary of the OCEL tables.
    """
    print("OCEL summary")
    print("-------------------")
    print(f"Events: {summary['events_count']}")
    print(f"Objects: {summary['objects_count']}")
    print(f"Relations: {summary['relations_count']}")
    print(f"Activity count: {summary['activity_count']}")
    print(f"Activities: {summary['activities']}")
    print(f"Object types: {summary['object_types']}")


if __name__ == "__main__":
    sample_dir = "data/p2p_sample"

    try:
        ocel_tables = load_ocel_tables(sample_dir)
        summary = summarize_ocel_tables(ocel_tables)
        print_summary(summary)

    except Exception as e:
        print(f"Error: {e}")