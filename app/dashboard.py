from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))


from ingestion.load_ocel import load_ocel_tables
from features.activity_object_features import extract_activity_object_features
from features.activity_interaction_patterns import (
    classify_activity_interaction_patterns,
)
from features.activity_insights import generate_activity_insights


DATA_PATH = "data/p2p_sample"

EVENT_ID = "ocel:eid"
ACTIVITY = "ocel:activity"
TIMESTAMP = "ocel:timestamp"
OBJECT_ID = "ocel:oid"
OBJECT_TYPE = "ocel:type"


def build_insights_dataframe(insights: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(insights)


def build_pattern_summary(insights_df: pd.DataFrame) -> pd.DataFrame:
    return (
        insights_df["pattern"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "pattern", "pattern": "count"})
    )


def build_object_type_counts(objects: pd.DataFrame) -> pd.DataFrame:
    return (
        objects[OBJECT_TYPE]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "object_type", OBJECT_TYPE: "count"})
    )


def build_purchase_order_variants(
    events: pd.DataFrame,
    relations: pd.DataFrame,
) -> pd.DataFrame:
    """
    Approximate variant analysis for the current P2P sample.

    In OCEL, there is no single universal case ID.
    For this first dashboard, we use purchase_order objects as the
    process instance anchor.
    """

    purchase_order_relations = relations[
        relations[OBJECT_TYPE] == "purchase_order"
    ][[EVENT_ID, OBJECT_ID]]

    po_events = purchase_order_relations.merge(
        events[[EVENT_ID, ACTIVITY, TIMESTAMP]],
        on=EVENT_ID,
        how="left",
    )

    po_events[TIMESTAMP] = pd.to_datetime(po_events[TIMESTAMP])

    variants = (
        po_events.sort_values([OBJECT_ID, TIMESTAMP])
        .groupby(OBJECT_ID)[ACTIVITY]
        .apply(lambda activities: " → ".join(activities.tolist()))
        .reset_index()
        .rename(columns={OBJECT_ID: "purchase_order", ACTIVITY: "variant"})
    )

    variant_summary = (
        variants["variant"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "variant", "variant": "count"})
    )

    total_cases = variant_summary["count"].sum()

    variant_summary["percentage"] = (
        variant_summary["count"] / total_cases * 100
    ).round(2)

    return variant_summary


def main() -> None:
    st.set_page_config(
        page_title="Intelligent Process Advisor",
        layout="wide",
    )

    st.title("Intelligent Process Advisor")
    st.caption(
        "Object-centric process analytics and automation decision support prototype"
    )

    ocel_tables = load_ocel_tables(DATA_PATH)

    events = ocel_tables["events"]
    objects = ocel_tables["objects"]
    relations = ocel_tables["relations"]

    activity_object_features = extract_activity_object_features(
        events=events,
        relations=relations,
    )

    interaction_patterns = classify_activity_interaction_patterns(
        features=activity_object_features,
    )

    activity_insights = generate_activity_insights(
        patterns=interaction_patterns,
    )

    insights_df = build_insights_dataframe(activity_insights.insights)
    pattern_summary = build_pattern_summary(insights_df)
    object_type_counts = build_object_type_counts(objects)
    variant_summary = build_purchase_order_variants(events, relations)

    st.header("Process Overview")

    number_of_events = len(events)
    number_of_activities = events[ACTIVITY].nunique()
    number_of_objects = len(objects)
    number_of_object_types = objects[OBJECT_TYPE].nunique()
    number_of_variants = len(variant_summary)

    purchase_orders = objects[objects[OBJECT_TYPE] == "purchase_order"]
    invoices = objects[objects[OBJECT_TYPE] == "invoice"]
    items = objects[objects[OBJECT_TYPE] == "item"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Events", number_of_events)
    col2.metric("Activities", number_of_activities)
    col3.metric("Objects", number_of_objects)
    col4.metric("Object Types", number_of_object_types)

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Purchase Orders", len(purchase_orders))
    col6.metric("Invoices", len(invoices))
    col7.metric("Items", len(items))
    col8.metric("Variants", number_of_variants)

    st.divider()

    st.header("Activity Insights")
    st.dataframe(
        insights_df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Interaction Pattern Summary")
        st.dataframe(
            pattern_summary,
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(
            pattern_summary.set_index("pattern")["count"]
        )

    with right_col:
        st.subheader("Object Type Distribution")
        st.dataframe(
            object_type_counts,
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(
            object_type_counts.set_index("object_type")["count"]
        )

    st.divider()

    st.header("Variant Analysis")
    st.caption(
        "Current prototype uses purchase_order as the process instance anchor for variant analysis."
    )

    st.dataframe(
        variant_summary,
        use_container_width=True,
        hide_index=True,
    )

    if not variant_summary.empty:
        most_common_variant = variant_summary.iloc[0]

        st.info(
            f"Most common variant appears in "
            f"{most_common_variant['percentage']}% of purchase orders."
        )

        st.write(most_common_variant["variant"])


if __name__ == "__main__":
    main()