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
from features.automation_decision_clusters import (
    extract_automation_decision_clusters,
)
from features.executive_kpis import calculate_executive_kpis
from features.process_flow_features import extract_process_flow_features
from features.process_performance_features import extract_process_performance_features
from ai.process_advisor import (
    answer_process_question,
    generate_process_advisor_summary,
)


DATA_PATH = "data/p2p_sample"

ACTIVITY = "ocel:activity"
OBJECT_TYPE = "ocel:type"

DECISION_CLUSTER_LABELS = {
    "rpa_or_workflow_automation": "RPA / Workflow Automation",
    "ai_assisted_automation": "AI-Assisted Automation",
    "human_in_the_loop": "Human-in-the-Loop",
    "low_automation_potential": "Low Automation Potential",
}


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


def build_cluster_dataframe(clusters: dict[str, list[dict]]) -> pd.DataFrame:
    rows: list[dict] = []

    for cluster_name, opportunities in clusters.items():
        for opportunity in opportunities:
            rows.append({
                "decision_cluster": cluster_name,
                "decision_cluster_label": DECISION_CLUSTER_LABELS.get(
                    cluster_name,
                    cluster_name,
                ),
                **opportunity,
            })

    return pd.DataFrame(rows)


def build_cluster_summary(clusters: dict[str, list[dict]]) -> pd.DataFrame:
    rows: list[dict] = []

    for cluster_name, label in DECISION_CLUSTER_LABELS.items():
        rows.append({
            "decision_cluster": label,
            "count": len(clusters.get(cluster_name, [])),
        })

    return pd.DataFrame(rows)


def keep_existing_columns(dataframe: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in dataframe.columns]


def format_number(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def format_percentage(value: int | float) -> str:
    return f"{float(value):.1f}%"


def format_days(value: int | float) -> str:
    return f"{float(value):.1f}d"


def format_currency(value: int | float) -> str:
    value = float(value)

    if value >= 1_000_000:
        return f"€ {value / 1_000_000:.1f}M"

    return f"€ {int(value):,}".replace(",", ".")


def format_count_columns(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    formatted_df = dataframe.copy()

    for column in columns:
        if column in formatted_df.columns:
            formatted_df[column] = formatted_df[column].apply(
                lambda value: format_number(value) if pd.notna(value) else value
            )

    return formatted_df


def show_metric_row(metrics: list[tuple[str, str | int | float]]) -> None:
    columns = st.columns(len(metrics))

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def show_list_section(title: str, items: list[str]) -> None:
    st.subheader(title)

    if not items:
        st.write("No items returned.")
        return

    for item in items:
        st.write(f"- {item}")


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

    process_flow_features = extract_process_flow_features(
        events=events,
        relations=relations,
        case_object_type="purchase_order",
    )

    process_performance_features = extract_process_performance_features(
        events=events,
        relations=relations,
        case_object_type="purchase_order",
    )

    automation_opportunity_features = extract_automation_opportunity_features(
        patterns=interaction_patterns,
        context_features=activity_context_features,
        performance_features=process_performance_features,
    )

    automation_decision_clusters = extract_automation_decision_clusters(
        automation_features=automation_opportunity_features,
    )

    executive_kpis = calculate_executive_kpis(
        events=events,
        objects=objects,
        relations=relations,
        activity_insights=activity_insights,
        case_object_type="purchase_order",
    )

    insights_df = build_insights_dataframe(activity_insights.insights)
    automation_df = pd.DataFrame(automation_opportunity_features.opportunities)
    cluster_df = build_cluster_dataframe(automation_decision_clusters.clusters)
    cluster_summary_df = build_cluster_summary(automation_decision_clusters.clusters)
    performance_df = pd.DataFrame(process_performance_features.activity_performance)

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

    if not automation_df.empty and "automation_candidate" in automation_df.columns:
        automation_candidates = automation_df[
            automation_df["automation_candidate"] == True
        ]
    else:
        automation_candidates = pd.DataFrame()

    (
        overview_tab,
        automation_tab,
        ai_advisor_tab,
        flow_tab,
        variants_tab,
        performance_tab,
        insights_tab,
        technical_tab,
    ) = st.tabs(
        [
            "Overview",
            "Automation Opportunities",
            "AI Advisor",
            "Process Flow",
            "Variants",
            "Performance",
            "Insights",
            "Technical Data",
        ]
    )

    with overview_tab:
        st.header("Executive Overview")

        show_metric_row(
            [
                ("Purchase Orders", format_number(len(purchase_orders))),
                ("Invoices", format_number(len(invoices))),
                ("Items", format_number(len(items))),
                (
                    "Total Process Value",
                    format_currency(executive_kpis.total_process_value),
                ),
            ]
        )

        show_metric_row(
            [
                ("Events", format_number(len(events))),
                ("Activities", format_number(events[ACTIVITY].nunique())),
                ("Objects", format_number(len(objects))),
                ("Object Types", format_number(objects[OBJECT_TYPE].nunique())),
            ]
        )

        show_metric_row(
            [
                (
                    "Avg Throughput Time",
                    format_days(executive_kpis.avg_throughput_days),
                ),
                ("Variants", format_number(len(variant_summary_df))),
                ("Automation Rate", format_percentage(executive_kpis.automation_rate)),
                ("Automation Candidates", format_number(len(automation_candidates))),
            ]
        )

        st.divider()

        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Object Type Distribution")
            st.dataframe(
                format_count_columns(object_type_counts_df, ["count"]),
                use_container_width=True,
                hide_index=True,
            )

        with right_col:
            st.subheader("Automation Decision Cluster Summary")
            st.dataframe(
                format_count_columns(cluster_summary_df, ["count"]),
                use_container_width=True,
                hide_index=True,
            )

    with automation_tab:
        st.header("Automation Opportunities")

        st.caption(
            "Rule-based automation opportunity scoring and decision clustering before AI reasoning."
        )

        if automation_df.empty:
            st.warning("No automation opportunities were generated.")
        else:
            display_columns = keep_existing_columns(
                automation_df,
                [
                    "activity",
                    "pattern",
                    "automation_score",
                    "automation_candidate",
                    "recommended_automation_type",
                    "automation_value_driver",
                    "frequency",
                    "percentage_of_total_events",
                    "average_position",
                    "variants_containing_activity",
                    "rework_rate",
                    "bottleneck_risk",
                    "stability_score",
                ],
            )

            st.subheader("Automation Opportunity Ranking")
            st.dataframe(
                format_count_columns(
                    automation_df[display_columns],
                    ["frequency", "variants_containing_activity"],
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Automation Decision Clusters")

            for cluster_name, opportunities in automation_decision_clusters.clusters.items():
                cluster_label = DECISION_CLUSTER_LABELS.get(cluster_name, cluster_name)

                st.markdown(f"### {cluster_label}")

                if not opportunities:
                    st.write("No activities in this cluster.")
                    continue

                cluster_opportunities_df = pd.DataFrame(opportunities)

                cluster_display_columns = keep_existing_columns(
                    cluster_opportunities_df,
                    [
                        "activity",
                        "automation_score",
                        "recommended_automation_type",
                        "automation_candidate",
                        "automation_value_driver",
                        "pattern",
                        "frequency",
                        "variants_containing_activity",
                        "rework_rate",
                        "bottleneck_risk",
                        "stability_score",
                    ],
                )

                st.dataframe(
                    format_count_columns(
                        cluster_opportunities_df[cluster_display_columns],
                        ["frequency", "variants_containing_activity"],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                explanation = opportunities[0].get("cluster_explanation", "-")
                st.info(explanation)

            st.subheader("Top Automation Recommendations")

            top_opportunities = automation_df.head(5)

            for _, row in top_opportunities.iterrows():
                st.subheader(row["activity"])
                st.write(f"Recommended type: {row['recommended_automation_type']}")
                st.write(f"Automation score: {row['automation_score']}")
                st.write(f"Candidate: {row['automation_candidate']}")

                if "automation_value_driver" in row:
                    st.write(f"Value driver: {row['automation_value_driver']}")

                if "rework_rate" in row:
                    st.write(f"Rework rate: {row['rework_rate']}%")

                if "bottleneck_risk" in row:
                    st.write(f"Bottleneck risk: {row['bottleneck_risk']}")

                if "stability_score" in row:
                    st.write(f"Stability score: {row['stability_score']}")

                st.write("Reasoning:")
                for reason in row["reasoning"]:
                    st.write(f"- {reason}")

                st.divider()

    with ai_advisor_tab:
        st.header("AI Process Advisor")

        st.caption(
            "Generates executive process improvement guidance and answers custom "
            "questions using the structured intelligence produced by the local analytics engine."
        )

        st.warning(
            "The AI Advisor uses the OpenAI API only when you click a button below. "
            "It does not send raw CSV files, only structured analytics outputs."
        )

        st.subheader("Executive Advisor Summary")

        if st.button("Generate AI Advisor Summary"):
            with st.spinner("Generating AI process advisor summary..."):
                try:
                    advisor_response = generate_process_advisor_summary(
                        process_flow_features=process_flow_features,
                        activity_insights=activity_insights,
                        automation_opportunity_features=automation_opportunity_features,
                        automation_decision_clusters=automation_decision_clusters,
                        process_performance_features=process_performance_features,
                    )

                    st.session_state["advisor_response"] = advisor_response.to_dict()

                except Exception as error:
                    st.error("AI Advisor generation failed.")
                    st.exception(error)

        advisor_response_data = st.session_state.get("advisor_response")

        if advisor_response_data:
            st.subheader("Executive Summary")
            st.write(advisor_response_data.get("executive_summary", ""))

            show_list_section(
                "Key Weaknesses",
                advisor_response_data.get("key_weaknesses", []),
            )

            show_list_section(
                "Automation Recommendations",
                advisor_response_data.get("automation_recommendations", []),
            )

            show_list_section(
                "Human-in-the-Loop Recommendations",
                advisor_response_data.get("human_in_the_loop_recommendations", []),
            )

            show_list_section(
                "AI-Assisted Recommendations",
                advisor_response_data.get("ai_assisted_recommendations", []),
            )

            show_list_section(
                "Next Steps",
                advisor_response_data.get("next_steps", []),
            )
        else:
            st.info("Click the button to generate the first AI advisor summary.")

        st.divider()

        st.subheader("Ask the Process Advisor")

        st.caption(
            "Ask a focused question about bottlenecks, rework, automation candidates, "
            "decision clusters, or process improvement priorities."
        )

        process_question = st.text_area(
            label="Your question",
            placeholder=(
                "Example: Which activities should be prioritized for automation and why?"
            ),
            height=120,
        )

        if st.button("Ask Question"):
            if not process_question.strip():
                st.warning("Please enter a question first.")
            else:
                with st.spinner("Answering process question..."):
                    try:
                        advisor_answer = answer_process_question(
                            process_flow_features=process_flow_features,
                            activity_insights=activity_insights,
                            automation_opportunity_features=automation_opportunity_features,
                            automation_decision_clusters=automation_decision_clusters,
                            process_performance_features=process_performance_features,
                            question=process_question,
                        )

                        st.session_state["advisor_question"] = process_question
                        st.session_state["advisor_answer"] = advisor_answer

                    except Exception as error:
                        st.error("AI question answering failed.")
                        st.exception(error)

        advisor_question = st.session_state.get("advisor_question")
        advisor_answer = st.session_state.get("advisor_answer")

        if advisor_question and advisor_answer:
            st.subheader("Question")
            st.write(advisor_question)

            st.subheader("Answer")
            st.write(advisor_answer)

    with flow_tab:
        st.header("Process Flow Analytics")

        st.subheader("Start Activities")
        st.dataframe(start_activities_df, use_container_width=True, hide_index=True)

        st.subheader("End Activities")
        st.dataframe(end_activities_df, use_container_width=True, hide_index=True)

        st.subheader("Activity Frequency")
        st.dataframe(
            format_count_columns(activity_frequency_df, ["count"]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Directly-Follows Relations")
        st.dataframe(
            format_count_columns(directly_follows_df, ["count"]),
            use_container_width=True,
            hide_index=True,
        )

    with variants_tab:
        st.header("Variant Analysis")

        st.dataframe(
            format_count_columns(variant_summary_df, ["count"]),
            use_container_width=True,
            hide_index=True,
        )

        if not variant_summary_df.empty:
            top = variant_summary_df.iloc[0]
            st.info(f"Most common variant: {top['percentage']}%")
            st.write(top["variant"])

    with performance_tab:
        st.header("Process Performance Intelligence")

        st.caption(
            "Operational pain signals used for continuous improvement and future AI reasoning."
        )

        if performance_df.empty:
            st.warning("No process performance features were generated.")
        else:
            st.subheader("Activity Performance Signals")
            st.dataframe(
                format_count_columns(
                    performance_df,
                    ["frequency", "rework_cases", "cases_with_activity", "total_cases"],
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("High Bottleneck Risk Activities")

            high_bottleneck_df = performance_df[
                performance_df["bottleneck_risk"] == "high"
            ]

            if high_bottleneck_df.empty:
                st.info("No high bottleneck risk activities found in the current dataset.")
            else:
                st.dataframe(
                    format_count_columns(
                        high_bottleneck_df,
                        ["frequency", "rework_cases", "cases_with_activity", "total_cases"],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            st.subheader("Low Stability Activities")

            low_stability_df = performance_df[
                performance_df["stability_score"] < 70
            ]

            if low_stability_df.empty:
                st.info("No low stability activities found in the current dataset.")
            else:
                st.dataframe(
                    format_count_columns(
                        low_stability_df,
                        ["frequency", "rework_cases", "cases_with_activity", "total_cases"],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

    with insights_tab:
        st.header("Activity Insights")

        for _, row in insights_df.iterrows():
            st.subheader(row.get("activity", "-"))
            st.write(f"Pattern: {row.get('pattern_label', row.get('pattern', '-'))}")
            st.write(f"Risk: {row.get('risk', '-')}")
            st.write(row.get("insight", "-"))
            st.write(row.get("recommendation", "-"))
            st.divider()

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

        st.dataframe(patterns_df, use_container_width=True, hide_index=True)

        st.subheader("Activity Context Features")
        st.dataframe(activity_context_df, use_container_width=True, hide_index=True)

        st.subheader("Automation Opportunity Features")
        st.dataframe(automation_df, use_container_width=True, hide_index=True)

        st.subheader("Automation Decision Cluster Features")
        st.dataframe(cluster_df, use_container_width=True, hide_index=True)

        st.subheader("Process Performance Features")
        st.dataframe(performance_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()