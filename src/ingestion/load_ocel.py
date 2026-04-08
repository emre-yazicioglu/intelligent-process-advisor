from pathlib import Path
from typing import Any, Dict

from pm4py.read import read_ocel


def load_ocel_file(file_path: str) -> Any:
    """
    Load an OCEL file from the given path.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ocel = read_ocel(str(path))
    return ocel


def summarize_ocel(ocel: Any) -> Dict[str, Any]:
    """
    Return a basic summary of the OCEL object.
    """
    events_count = len(ocel.events)
    objects_count = len(ocel.objects)

    activity_count = ocel.events["ocel:activity"].nunique()
    object_types = sorted(
        ocel.objects["ocel:type"].dropna().unique().tolist()
    )

    return {
        "events_count": events_count,
        "objects_count": objects_count,
        "activity_count": activity_count,
        "object_types": object_types,
    }


if __name__ == "__main__":
    sample_path = "data/sample_ocel.jsonocel"

    try:
        ocel = load_ocel_file(sample_path)
        summary = summarize_ocel(ocel)

        print("OCEL summary")
        print("-------------------")
        print(f"Events: {summary['events_count']}")
        print(f"Objects: {summary['objects_count']}")
        print(f"Activities: {summary['activity_count']}")
        print(f"Object types: {summary['object_types']}")

    except Exception as e:
        print(f"Error: {e}")
