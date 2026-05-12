from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

DEFAULT_MODEL = "gpt-4.1"


@dataclass(frozen=True)
class ProcessAdvisorResponse:
    executive_summary: str
    key_weaknesses: list[str]
    automation_recommendations: list[str]
    human_in_the_loop_recommendations: list[str]
    ai_assisted_recommendations: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "key_weaknesses": self.key_weaknesses,
            "automation_recommendations": self.automation_recommendations,
            "human_in_the_loop_recommendations": self.human_in_the_loop_recommendations,
            "ai_assisted_recommendations": self.ai_assisted_recommendations,
            "next_steps": self.next_steps,
        }


PROCESS_ADVISOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "executive_summary": {"type": "string"},
        "key_weaknesses": {
            "type": "array",
            "items": {"type": "string"},
        },
        "automation_recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "human_in_the_loop_recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "ai_assisted_recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "next_steps": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "executive_summary",
        "key_weaknesses",
        "automation_recommendations",
        "human_in_the_loop_recommendations",
        "ai_assisted_recommendations",
        "next_steps",
    ],
}


def build_process_advisor_payload(
    process_flow_features: Any,
    activity_insights: Any,
    automation_opportunity_features: Any,
    automation_decision_clusters: Any,
    process_performance_features: Any,
) -> dict[str, Any]:
    return {
        "process_flow": process_flow_features.to_dict(),
        "activity_insights": activity_insights.to_dict(),
        "automation_opportunities": automation_opportunity_features.to_dict(),
        "automation_decision_clusters": automation_decision_clusters.to_dict(),
        "process_performance": process_performance_features.to_dict(),
    }


def build_process_advisor_prompt(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(
        payload,
        indent=2,
        default=str,
    )

    return f"""
You are an expert Process Intelligence and Intelligent Automation advisor.

You are analyzing structured outputs from an Object-Centric Event Log analytics engine.

Produce a practical executive advisory summary.

Focus on:
1. Main process weaknesses
2. Bottleneck or stability risks
3. Rework or variance signals
4. Automation opportunities
5. RPA / workflow automation candidates
6. AI-assisted automation candidates
7. Human-in-the-loop areas
8. Concrete next steps for continuous improvement

Rules:
- Do not invent facts that are not supported by the provided data.
- If the dataset is small or weak, explicitly say so.
- Avoid generic consulting language.
- Refer to activity names when possible.
- Do not overclaim business impact.
- Keep the tone suitable for an executive process improvement audience.

Structured process intelligence payload:
{payload_json}
""".strip()


def parse_process_advisor_response(response_text: str) -> ProcessAdvisorResponse:
    parsed = json.loads(response_text)

    return ProcessAdvisorResponse(
        executive_summary=str(parsed["executive_summary"]),
        key_weaknesses=list(parsed["key_weaknesses"]),
        automation_recommendations=list(parsed["automation_recommendations"]),
        human_in_the_loop_recommendations=list(
            parsed["human_in_the_loop_recommendations"]
        ),
        ai_assisted_recommendations=list(parsed["ai_assisted_recommendations"]),
        next_steps=list(parsed["next_steps"]),
    )


def generate_process_advisor_summary(
    process_flow_features: Any,
    activity_insights: Any,
    automation_opportunity_features: Any,
    automation_decision_clusters: Any,
    process_performance_features: Any,
    model: str = DEFAULT_MODEL,
) -> ProcessAdvisorResponse:
    payload = build_process_advisor_payload(
        process_flow_features=process_flow_features,
        activity_insights=activity_insights,
        automation_opportunity_features=automation_opportunity_features,
        automation_decision_clusters=automation_decision_clusters,
        process_performance_features=process_performance_features,
    )

    prompt = build_process_advisor_prompt(payload)

    client = OpenAI()

    response = client.responses.create(
        model=model,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "process_advisor_response",
                "schema": PROCESS_ADVISOR_SCHEMA,
                "strict": True,
            }
        },
    )

    return parse_process_advisor_response(response.output_text)