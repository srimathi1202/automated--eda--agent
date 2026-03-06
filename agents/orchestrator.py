"""
agents/orchestrator.py
-----------------------
Master controller — coordinates all 5 agents in the correct
sequence and returns a unified result dict.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any

from agents.base_agent import BaseAgent
from agents.profiler_agent import ProfilerAgent
from agents.insight_agent import InsightAgent
from agents.chart_agent import ChartAgent
from agents.report_agent import ReportAgent
from agents.email_agent import EmailAgent


class OrchestratorAgent(BaseAgent):
    """Runs the full EDA pipeline end-to-end."""

    def __init__(self, verbose: bool = False):
        super().__init__("Orchestrator", verbose)
        self.profiler = ProfilerAgent(verbose)
        self.insight  = InsightAgent(verbose)
        self.charter  = ChartAgent(verbose)
        self.reporter = ReportAgent(verbose)
        self.emailer  = EmailAgent(verbose)

    def run(self, context: dict) -> dict[str, Any]:
        start = datetime.now()

        print("\n" + "="*60)
        print("  🤖  AUTOMATED EDA AGENT — STARTING PIPELINE")
        print("="*60)

        # Phase 1: Profile
        print("\n📊 Phase 1: Statistical Profiling")
        print("-" * 40)
        try:
            p1 = self.profiler.run(context)
        except Exception as e:
            return {
                "success": False,
                "error": f"ProfilerAgent: {e}"
            }
        context.update(p1)

        # Phase 2: AI Insights
        print("\n🧠 Phase 2: AI Insight Generation")
        print("-" * 40)
        try:
            p2 = self.insight.run(context)
        except Exception as e:
            print(f"  ⚠️  InsightAgent failed ({e}) — using fallback")
            p2 = {"insights": {
                "headline":  "EDA Complete",
                "key_insights": [
                    "Dataset profiled successfully."
                ],
                "anomalies": [],
                "recommendations": [
                    "Review the dashboard for statistics."
                ],
                "data_story": "Analysis complete.",
            }}
        context.update(p2)

        # Phase 3: Charts
        print("\n📈 Phase 3: Chart Generation")
        print("-" * 40)
        try:
            p3 = self.charter.run(context)
        except Exception as e:
            return {
                "success": False,
                "error": f"ChartAgent: {e}"
            }
        context.update(p3)

        # Phase 4: Report
        print("\n📝 Phase 4: Dashboard Assembly")
        print("-" * 40)
        try:
            p4 = self.reporter.run(context)
        except Exception as e:
            return {
                "success": False,
                "error": f"ReportAgent: {e}"
            }
        context.update(p4)

        # Phase 5: Email
        if context.get("email_recipient"):
            print("\n📧 Phase 5: Sending Email Report")
            print("-" * 40)
            try:
                p5 = self.emailer.run(context)
                context.update(p5)
            except Exception as e:
                print(f"  ⚠️  EmailAgent failed: {e}")

        duration = round(
            (datetime.now() - start).total_seconds(), 2
        )
        ov   = context["profile"]["overview"]
        qual = context["profile"]["data_quality"]

        return {
            "success":        True,
            "dashboard_path": context.get("dashboard_path"),
            "email_sent":     context.get("email_sent", False),
            "duration_sec":   duration,
            "summary": {
                "file":    context.get("filename"),
                "rows":    ov.get("rows"),
                "columns": ov.get("columns"),
                "quality": (
                    f"{qual.get('overall_score')} "
                    f"({qual.get('grade')})"
                ),
                "missing": f"{ov.get('missing_pct')}%",
            },
        }
