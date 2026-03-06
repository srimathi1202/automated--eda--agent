"""
tests/test_tools.py
--------------------
Unit tests for StatsTools, ChartTools, and EmailTools.
Run with: pytest tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.stats_tools import StatsTools
from tools.chart_tools import ChartTools


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "age":      [25, 30, np.nan, 35, 200, 28, 32, 40, 29, 31],
        "salary":   [50000, 60000, 55000, np.nan, 70000,
                     52000, 63000, 80000, 58000, 61000],
        "city":     ["NY", "LA", "NY", "Chicago", "LA",
                     None, "NY", "Chicago", "LA", "NY"],
        "category": ["A", "B", "A", "C", "B",
                     "A", "C", "B", "A", "C"],
        "score":    [4.5, 3.8, 4.2, 4.9, 3.5,
                     4.1, 4.7, 3.9, 4.6, 4.3],
    })


# ── StatsTools Tests ───────────────────────────────────────────────────

class TestStatsTools:
    st = StatsTools()

    def test_overview_keys(self, sample_df):
        ov = self.st.overview(sample_df)
        for key in [
            "rows", "columns", "numeric_cols",
            "categorical_cols", "missing_pct", "duplicate_rows"
        ]:
            assert key in ov

    def test_overview_values(self, sample_df):
        ov = self.st.overview(sample_df)
        assert ov["rows"]    == 10
        assert ov["columns"] == 5

    def test_column_stats_numeric(self, sample_df):
        stats    = self.st.column_stats(sample_df)
        age_stat = next(
            s for s in stats if s["column"] == "age"
        )
        assert age_stat["kind"] == "numeric"
        assert "mean"   in age_stat
        assert "std"    in age_stat
        assert "median" in age_stat

    def test_column_stats_categorical(self, sample_df):
        stats     = self.st.column_stats(sample_df)
        city_stat = next(
            s for s in stats if s["column"] == "city"
        )
        assert city_stat["kind"] == "categorical"
        assert "top_values" in city_stat

    def test_missing_analysis(self, sample_df):
        miss = self.st.missing_analysis(sample_df)
        assert miss["total_missing"]    > 0
        assert miss["columns_affected"] > 0
        assert all(
            "column" in c for c in miss["per_column"]
        )

    def test_correlation_analysis(self, sample_df):
        corr = self.st.correlation_analysis(sample_df)
        assert "matrix"       in corr
        assert "strong_pairs" in corr

    def test_correlation_insufficient_columns(self):
        df   = pd.DataFrame({"a": [1, 2, 3]})
        corr = self.st.correlation_analysis(df)
        assert corr["matrix"] == {}

    def test_outlier_analysis(self, sample_df):
        outliers = self.st.outlier_analysis(sample_df)
        assert isinstance(outliers, list)
        age_out = next(
            (o for o in outliers if o["column"] == "age"),
            None
        )
        assert age_out is not None
        assert age_out["outlier_count"] >= 1

    def test_data_quality_score(self, sample_df):
        qual = self.st.data_quality_score(sample_df)
        assert 0 <= qual["overall_score"] <= 100
        assert qual["grade"] in ["A", "B", "C", "D", "F"]
        assert "completeness" in qual
        assert "uniqueness"   in qual

    def test_distribution_tests(self, sample_df):
        dists = self.st.distribution_tests(sample_df)
        assert isinstance(dists, list)
        for d in dists:
            assert "column"    in d
            assert "is_normal" in d
            assert "skewness"  in d

    def test_full_profile_keys(self, sample_df):
        profile = self.st.full_profile(sample_df)
        for key in [
            "overview", "column_stats", "missing",
            "correlations", "outliers",
            "data_quality", "distributions"
        ]:
            assert key in profile


# ── ChartTools Tests ───────────────────────────────────────────────────

class TestChartTools:
    ct = ChartTools()

    def test_histogram_returns_html(self, sample_df):
        html = self.ct.histogram(sample_df, "age")
        assert "<div" in html

    def test_box_plot_returns_html(self, sample_df):
        html = self.ct.box_plot(
            sample_df, ["age", "salary", "score"]
        )
        assert "<div" in html

    def test_bar_chart_returns_html(self, sample_df):
        html = self.ct.bar_chart(sample_df, "city")
        assert "<div" in html

    def test_pie_chart_returns_html(self, sample_df):
        html = self.ct.pie_chart(sample_df, "category")
        assert "<div" in html

    def test_correlation_heatmap_html(self, sample_df):
        html = self.ct.correlation_heatmap(sample_df)
        assert "<div" in html or "<p" in html

    def test_missing_bar_html(self, sample_df):
        html = self.ct.missing_bar(sample_df)
        assert "<div" in html or "<p" in html

    def test_missing_bar_no_missing(self):
        df   = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6]
        })
        html = self.ct.missing_bar(df)
        assert "No missing" in html

    def test_dtype_donut_html(self, sample_df):
        html = self.ct.dtype_donut(sample_df)
        assert "<div" in html

    def test_quality_gauge_html(self):
        html = self.ct.quality_gauge(85.5)
        assert "<div" in html

    def test_outlier_bar_no_outliers(self):
        html = self.ct.outlier_bar([])
        assert "No outliers" in html

    def test_scatter_plot_html(self, sample_df):
        html = self.ct.scatter_plot(
            sample_df, "age", "salary"
        )
        assert "<div" in html

    def test_violin_plot_html(self, sample_df):
        html = self.ct.violin_plot(sample_df, "score")
        assert "<div" in html

    def test_missing_heatmap_html(self, sample_df):
        html = self.ct.missing_heatmap(sample_df)
        assert "<div" in html
