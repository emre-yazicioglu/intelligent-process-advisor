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
from features.activity_context_features import extract_activity_context_features
from features.activity_insights import generate_activity_insights
from features.automation_opportunity_features import (
    extract_automation_opportunity_features,
)
from features.process_flow_features import extract_process_flow_features


DATA_PATH = "data/p2p_sample"

ACTIVITY = "ocel:activity"
OBJECT_TYPE = "ocel:type"


def build_insights_dataframe(insights: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(insights)


def build_count_table(series: pd.Series, label_column: str) -> pd.DataFrame:
    return (
        series.value_counts()
        .rename_axis(label_column)
        .reset_index(name="count")
    )


def build_pattern_summary(insights_df: pd.DataFrame) -> pd.DataFrame:
    if insights_df.empty or "pattern" not in insights_df.columns:
        return pd.DataFrame(columns=["pattern", "count"])

    return build_count_table(
        series=insights_df["pattern"],
        label_column="pattern",
    )


def build_object_type_counts(objects: pd.DataFrame) -> pd.DataFrame:
    return build_count_table(
        series=objects[OBJECT_TYPE],
        label_column="object_type",
    )


def show_metric_row(metrics: list[tuple[str, int]]) -> None:
    columns = st.columns(len(metrics))

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def main() -> None:
    st.set_page_config(
        page_title="Intelligent Process Advisor",
        layout="wide",
    )

    st.title("Intelligent Process Advisor")
    st.caption(
        "Advanced process analytics and automation decision support prototype"
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

    activity_context_features = extract_activity_context_features(
        events=events,
        relations=relations,
        case_object_type="purchase_order",
    )

    activity_insights = generate_activity_insights(
        patterns=interaction_patterns,
        context_features=activity_context_features,
    )

    automation_opportunity_features = extract_automation_opportunity_features(
        patterns=interaction_patterns,
        context_features=activity_context_features,
    )

    process_flow_features = extract_process_flow_features(
        events=events,
        relations=relations,
        case_object_type="purchase_order",
    )

    insights_df = build_insights_dataframe(activity_insights.insights)
    automation_df = pd.DataFrame(automation_opportunity_features.opportunities)

    pattern_summary_df = build_pattern_summary(insights_df)
    object_type_counts_df = build_object_type_counts(objects)

    start_activities_df = pd.DataFrame(process_flow_features.start_activities)
    end_activities_df = pd.DataFrame(process_flow_features.end_activities)
    activity_frequency_df = pd.DataFrame(process_flow_features.activity_frequency)
    directly_follows_df = pd.DataFrame(process_flow_features.directly_follows)
    variant_summary_df = pd.DataFrame(process_flow_features.variants)

    activity_context_df = pd.DataFrame(
        [
            {"activity": activity, **context}
            for activity, context in activity_context_features.activity_context.items()
        ]
    )

    purchase_orders = objects[objects[OBJECT_TYPE] == "purchase_order"]
    invoices = objects[objects[OBJECT_TYPE] == "invoice"]
    items = objects[objects[OBJECT_TYPE] == "item"]

    automation_candidates = automation_df[
        automation_df["automation_candidate"] == True
    ]

    overview_tab, flow_tab, variants_tab, insights_tab, automation_tab, technical_tab = st.tabs(
        [
            "Overview",
            "Process Flow",
            "Variants",
            "Insights",
            "Automation Opportunities",
            "Technical Data",
        ]
    )

    # ---------------- OVERVIEW ----------------
    with overview_tab:
        st.header("Executive Overview")

        show_metric_row(
            [
                ("Events", len(events)),
                ("Activities", events[ACTIVITY].nunique()),
                ("Objects", len(objects)),
                ("Object Types", objects[OBJECT_TYPE].nunique()),
            ]
        )

        show_metric_row(
            [
                ("Purchase Orders", len(purchase_orders)),
                ("Invoices", len(invoices)),
                ("Items", len(items)),
                ("Cases", process_flow_features.total_cases),
            ]
        )

        show_metric_row(
            [
                ("Variants", len(variant_summary_df)),
                ("Insights", len(insights_df)),
                ("Automation Candidates", len(automation_candidates)),
                ("Start Activities", len(start_activities_df)),
            ]
        )

        st.divider()

        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Object Type Distribution")
            st.dataframe(
                object_type_counts_df,
                use_container_width=True,
                hide_index=True,
            )

        with right_col:
            st.subheader("Interaction Pattern Summary")
            st.dataframe(
                pattern_summary_df,
                use_container_width=True,
                hide_index=True,
            )

    # ---------------- FLOW ----------------
    with flow_tab:
        st.header("Process Flow Analytics")

        st.subheader("Start Activities")
        st.dataframe(
            start_activities_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("End Activities")
        st.dataframe(
            end_activities_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Activity Frequency")
        st.dataframe(
            activity_frequency_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Directly-Follows Relations")
        st.dataframe(
            directly_follows_df,
            use_container_width=True,
            hide_index=True,
        )

    # ---------------- VARIANTS ----------------
    with variants_tab:
        st.header("Variant Analysis")

        st.dataframe(
            variant_summary_df,
            use_container_width=True,
            hide_index=True,
        )

        if not variant_summary_df.empty:
            top = variant_summary_df.iloc[0]
            st.info(f"Most common variant: {top['percentage']}%")
            st.write(top["variant"])

    # ---------------- INSIGHTS ----------------
    with insights_tab:
        st.header("Activity Insights")

        for _, row in insights_df.iterrows():
            st.subheader(row.get("activity", "-"))

            st.write(
                f"Pattern: {row.get('pattern_label', row.get('pattern', '-'))}"
            )

            st.write(f"Risk: {row.get('risk', '-')}")
            st.write(row.get("insight", "-"))
            st.write(row.get("recommendation", "-"))
            st.divider()

    # ---------------- AUTOMATION ----------------
    with automation_tab:
        st.header("Automation Opportunities")

        st.caption(
            "Rule-based automation opportunity scoring before AI reasoning."
        )

        if automation_df.empty:
            st.warning("No automation opportunities were generated.")
        else:
            display_columns = [
                "activity",
                "pattern",
                "automation_score",
                "automation_candidate",
                "recommended_automation_type",
                "frequency",
                "percentage_of_total_events",
                "average_position",
                "variants_containing_activity",
            ]

            st.subheader("Automation Opportunity Ranking")
            st.dataframe(
                automation_df[display_columns],
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Top Automation Recommendations")

            top_opportunities = automation_df.head(3)

            for _, row in top_opportunities.iterrows():
                st.subheader(row["activity"])
                st.write(f"Recommended type: {row['recommended_automation_type']}")
                st.write(f"Automation score: {row['automation_score']}")
                st.write(f"Candidate: {row['automation_candidate']}")

                st.write("Reasoning:")
                for reason in row["reasoning"]:
                    st.write(f"- {reason}")

                st.divider()

    # ---------------- TECHNICAL ----------------
    with technical_tab:
        st.header("Technical Data")

        st.subheader("Events")
        st.dataframe(events, use_container_width=True)

        st.subheader("Objects")
        st.dataframe(objects, use_container_width=True)

        st.subheader("Relations")
        st.dataframe(relations, use_container_width=True)

        st.subheader("Interaction Patterns")

        patterns_df = pd.DataFrame(
            [
                {"activity": activity, "pattern": pattern}
                for activity, pattern in interaction_patterns.activity_patterns.items()
            ]
        )

        st.dataframe(
            patterns_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Activity Context Features")
        st.dataframe(
            activity_context_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Automation Opportunity Features")
        st.dataframe(
            automation_df,
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()