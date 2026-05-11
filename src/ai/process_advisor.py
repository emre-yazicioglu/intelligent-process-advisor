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
    """
    AI-generated process advisor response.

    This object keeps the AI output structured so the dashboard can display it cleanly.
    """

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


def build_process_advisor_payload(
    process_flow_features: Any,
    activity_insights: Any,
    automation_opportunity_features: Any,
    automation_decision_clusters: Any,
    process_performance_features: Any,
) -> dict[str, Any]:
    """
    Build a compact structured payload for AI reasoning.

    We do not send raw CSVs or full dataframes to the AI.
    We send structured intelligence already calculated by our engine.
    """

    return {
        "process_flow": process_flow_features.to_dict(),
        "activity_insights": activity_insights.to_dict(),
        "automation_opportunities": automation_opportunity_features.to_dict(),
        "automation_decision_clusters": automation_decision_clusters.to_dict(),
        "process_performance": process_performance_features.to_dict(),
    }


def build_process_advisor_prompt(payload: dict[str, Any]) -> str:
    """
    Build the AI prompt.

    The AI should behave like a Process Intelligence advisor, not a generic chatbot.
    """

    payload_json = json.dumps(
        payload,
        indent=2,
        default=str,
    )

    return f"""
You are an expert Process Intelligence and Intelligent Automation advisor.

You are analyzing structured outputs from an Object-Centric Event Log analytics engine.

Your task:
Produce a practical executive advisory summary.

Focus on:
1. Main process weaknesses
2. Bottleneck or stability risks
3. Rework or variance signals
4. Automation opportunities
5. Which activities fit RPA / workflow automation
6. Which activities fit AI-assisted automation
7. Which activities should remain human-in-the-loop
8. Concrete next steps for continuous improvement

Rules:
- Do not invent facts that are not supported by the provided data.
- If the dataset is small or weak, explicitly say so.
- Avoid generic consulting language.
- Be specific and refer to activity names when possible.
- Keep the tone professional and suitable for an executive process improvement audience.
- Return only valid JSON.

Required JSON structure:
{{
  "executive_summary": "...",
  "key_weaknesses": ["..."],
  "automation_recommendations": ["..."],
  "human_in_the_loop_recommendations": ["..."],
  "ai_assisted_recommendations": ["..."],
  "next_steps": ["..."]
}}

Structured process intelligence payload:
{payload_json}
""".strip()


def parse_process_advisor_response(response_text: str) -> ProcessAdvisorResponse:
    """
    Convert AI JSON text into a typed response object.
    """

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "The AI response was not valid JSON. "
            "Try running the advisor again."
        ) from error

    return ProcessAdvisorResponse(
        executive_summary=str(parsed.get("executive_summary", "")),
        key_weaknesses=list(parsed.get("key_weaknesses", [])),
        automation_recommendations=list(parsed.get("automation_recommendations", [])),
        human_in_the_loop_recommendations=list(
            parsed.get("human_in_the_loop_recommendations", [])
        ),
        ai_assisted_recommendations=list(
            parsed.get("ai_assisted_recommendations", [])
        ),
        next_steps=list(parsed.get("next_steps", [])),
    )


def generate_process_advisor_summary(
    process_flow_features: Any,
    activity_insights: Any,
    automation_opportunity_features: Any,
    automation_decision_clusters: Any,
    process_performance_features: Any,
    model: str = DEFAULT_MODEL,
) -> ProcessAdvisorResponse:
    """
    Generate an AI-based process advisor summary.

    This is the first AI reasoning layer of the project.
    It depends on structured analytics created by the local feature engine.
    """

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
    )

    return parse_process_advisor_response(response.output_text)