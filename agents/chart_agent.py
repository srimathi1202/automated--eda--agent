"""
agents/chart_agent.py
----------------------
Autonomously decides which charts to generate based on column types,
then generates all of them as HTML snippets using ChartTools.
"""

from __future__ import annotations
from typing import Any

import pandas as pd
from agents.base_agent import BaseAgent
from tools.chart_tools import ChartTools


class ChartAgent(BaseAgent):
    """Generates the full chart suite for the dashboard."""

    MAX_HISTOGRAMS    = 8
    MAX_BAR_CHARTS    = 6
    MAX_PIE_CHARTS    = 4
    MAX_SCATTER_PAIRS = 3

    def __init__(self, verbose: bool = False):
        super().__init__("ChartAgent", verbose)
        self.ct = ChartTools()

    def run(self, context: dict) -> dict[str, Any]:
        df:      pd.DataFrame = context["df"]
        profile: dict         = context["profile"]

        self.log_step("Selecting and generating charts")

        charts: dict[str, Any] = {}

        # 1. Overview charts
        charts["dtype_donut"]   = self.ct.dtype_donut(df)
        charts["quality_gauge"] = self.ct.quality_gauge(
            profile["data_quality"]["overall_score"]
        )

        # 2. Missing values
        charts["missing_bar"]     = self.ct.missing_bar(df)
        charts["missing_heatmap"] = self.ct.missing_heatmap(df)

        # 3. Numeric distributions
        num_cols = df.select_dtypes(
            include="number"
        ).columns.tolist()

        charts["histograms"]   = []
        charts["box_plots"]    = []
        charts["violin_plots"] = []

        for col in num_cols[:self.MAX_HISTOGRAMS]:
            self.log(f"  histogram: {col}")
            charts["histograms"].append({
                "col":  col,
                "html": self.ct.histogram(df, col),
            })

        if num_cols:
            self.log("  box plots")
            charts["box_plots"] = self.ct.box_plot(df, num_cols)

        for col in num_cols[:3]:
            self.log(f"  violin: {col}")
            charts["violin_plots"].append({
                "col":  col,
                "html": self.ct.violin_plot(df, col),
            })

        # 4. Categorical charts
        cat_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        charts["bar_charts"] = []
        charts["pie_charts"] = []

        for col in cat_cols[:self.MAX_BAR_CHARTS]:
            if df[col].nunique() <= 50:
                self.log(f"  bar chart: {col}")
                charts["bar_charts"].append({
                    "col":  col,
                    "html": self.ct.bar_chart(df, col),
                })

        for col in cat_cols[:self.MAX_PIE_CHARTS]:
            if 2 <= df[col].nunique() <= 10:
                self.log(f"  pie chart: {col}")
                charts["pie_charts"].append({
                    "col":  col,
                    "html": self.ct.pie_chart(df, col),
                })

        # 5. Correlation
        if len(num_cols) >= 2:
            self.log("  correlation heatmap")
            charts["correlation_heatmap"] = (
                self.ct.correlation_heatmap(df)
            )
            charts["scatter_matrix"] = self.ct.scatter_matrix(df)

            strong_pairs = (
                profile.get("correlations", {})
                       .get("strong_pairs", [])
            )
            charts["scatter_plots"] = []
            for pair in strong_pairs[:self.MAX_SCATTER_PAIRS]:
                col_a, col_b = pair["col_a"], pair["col_b"]
                self.log(f"  scatter: {col_a} vs {col_b}")
                charts["scatter_plots"].append({
                    "x":    col_a,
                    "y":    col_b,
                    "r":    pair["r"],
                    "html": self.ct.scatter_plot(df, col_a, col_b),
                })

        # 6. Outliers
        charts["outlier_bar"] = self.ct.outlier_bar(
            profile.get("outliers", [])
        )

        total = (
            len(charts["histograms"]) +
            len(charts["bar_charts"]) +
            len(charts["pie_charts"]) +
            len(charts.get("scatter_plots", []))
        )
        self.log_step(
            "Charts complete",
            f"{total} individual charts generated"
        )

        return {"charts": charts}
