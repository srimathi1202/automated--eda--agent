"""
agents/profiler_agent.py
-------------------------
Loads the dataset and produces a full statistical profile.
"""

from __future__ import annotations
from typing import Any

import pandas as pd
from agents.base_agent import BaseAgent
from tools.stats_tools import StatsTools


class ProfilerAgent(BaseAgent):
    """Loads data and generates a comprehensive statistical profile."""

    def __init__(self, verbose: bool = False):
        super().__init__("ProfilerAgent", verbose)
        self.stats = StatsTools()

    def run(self, context: dict) -> dict[str, Any]:
        path = context["input_path"]
        self.log_step("Loading dataset", path)

        df = self._load(path)
        self.log_step(
            "Profiling",
            f"{df.shape[0]} rows × {df.shape[1]} cols"
        )

        profile = self.stats.full_profile(df)

        quality = profile["data_quality"]
        self.log_step(
            "Profile complete",
            f"Quality score: {quality['overall_score']} "
            f"({quality['grade']})"
        )

        return {
            "df":       df,
            "profile":  profile,
            "filename": path.split("/")[-1],
        }

    def _load(self, path: str) -> pd.DataFrame:
        """Load CSV or Excel into a DataFrame."""
        if path.endswith((".xlsx", ".xls")):
            return pd.read_excel(path)
        return pd.read_csv(path)
