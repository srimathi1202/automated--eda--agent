"""
agents/insight_agent.py
------------------------
Sends the statistical profile to Claude and receives structured
natural-language insights and recommendations.
"""

from __future__ import annotations
import json
from typing import Any

from agents.base_agent import BaseAgent


INSIGHT_SYSTEM = """
You are a senior data scientist writing an EDA insight report.
Given a dataset statistical profile in JSON, produce structured insights.

Respond ONLY with a valid JSON object — no prose, no markdown fences.

Schema:
{
  "headline": "<one compelling sentence summarising the dataset>",
  "key_insights": [
    "<insight 1 — specific, data-driven, mention actual numbers>",
    "<insight 2>",
    "<insight 3>",
    "<insight 4>",
    "<insight 5>"
  ],
  "anomalies": [
    "<anomaly 1 — specific column name and the issue>",
    "<anomaly 2>"
  ],
  "recommendations": [
    "<actionable recommendation 1>",
    "<actionable recommendation 2>",
    "<actionable recommendation 3>"
  ],
  "data_story": "<2-3 sentence narrative about what story this data tells>"
}

Rules:
- Be specific — mention column names, percentages, values
- insights must be concrete, not generic
- Identify real patterns: skewness, outliers, correlations, missing data
- recommendations should be practical next steps for a data analyst
""".strip()


class InsightAgent(BaseAgent):
    """Uses Claude to generate natural-language EDA insights."""

    def __init__(self, verbose: bool = False):
        super().__init__("InsightAgent", verbose)

    def run(self, context: dict) -> dict[str, Any]:
        profile  = context["profile"]
        filename = context.get("filename", "dataset")

        self.log_step("Sending profile to Claude for insights")

        prompt = self._build_prompt(profile, filename)

        try:
            insights = self._call_claude_json(prompt, INSIGHT_SYSTEM)
        except Exception as e:
            self.log(f"Claude JSON parse failed: {e}. Falling back.")
            raw = self._call_claude(
                prompt, INSIGHT_SYSTEM, reset_history=True
            )
            insights = self._fallback_parse(raw)

        self.log_step(
            "Insights received",
            f"{len(insights.get('key_insights', []))} insights, "
            f"{len(insights.get('anomalies', []))} anomalies"
        )

        return {"insights": insights}

    def _build_prompt(self, profile: dict, filename: str) -> str:
        compact = {
            "filename":          filename,
            "overview":          profile.get("overview", {}),
            "missing":           profile.get("missing", {}),
            "data_quality":      profile.get("data_quality", {}),
            "correlations_top":  profile.get("correlations", {})
                                        .get("strong_pairs", [])[:5],
            "outliers_top":      profile.get("outliers", [])[:5],
            "distributions_top": profile.get("distributions", [])[:5],
            "column_stats_top":  profile.get("column_stats", [])[:10],
        }
        return (
            "Analyse this dataset profile and generate insights:\n\n"
            + json.dumps(compact, indent=2)
        )

    def _fallback_parse(self, raw: str) -> dict:
        return {
            "headline":        "EDA complete — see profile for details.",
            "key_insights":    [raw[:300]],
            "anomalies":       [],
            "recommendations": ["Review the full statistical profile."],
            "data_story":      "Analysis complete.",
        }
