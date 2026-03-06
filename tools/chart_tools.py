"""
tools/chart_tools.py
---------------------
Plotly-based chart generators.
Every method returns an HTML string (self-contained Plotly figure).
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# Shared colour palette
PALETTE    = px.colors.qualitative.Bold
SEQUENTIAL = "Teal"
DIVERGING  = "RdBu"
BG_COLOR   = "#0f1117"
PAPER_COLOR= "#1a1d2e"
FONT_COLOR = "#e2e8f0"
GRID_COLOR = "#2d3748"

LAYOUT_BASE = dict(
    paper_bgcolor=PAPER_COLOR,
    plot_bgcolor=BG_COLOR,
    font=dict(
        color=FONT_COLOR,
        family="'Syne', sans-serif",
        size=13
    ),
    margin=dict(l=50, r=30, t=50, b=50),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
    yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
)


class ChartTools:
    """Factory for generating Plotly charts as HTML snippets."""

    def _to_html(self, fig: go.Figure) -> str:
        return fig.to_html(
            full_html=False,
            include_plotlyjs=False,
            config={
                "displayModeBar": False,
                "responsive": True
            },
        )

    def _apply_layout(
        self, fig: go.Figure, title: str = ""
    ) -> go.Figure:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=15, color="#94a3b8")
            ),
            **LAYOUT_BASE
        )
        return fig

    # ── Distribution charts ────────────────────────────────────────────

    def histogram(self, df: pd.DataFrame, col: str) -> str:
        """Histogram with KDE overlay."""
        series = df[col].dropna()
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=series,
            name=col,
            marker_color="#38bdf8",
            opacity=0.75,
            nbinsx=30,
        ))
        try:
            from scipy.stats import gaussian_kde
            kde   = gaussian_kde(series)
            x_rng = np.linspace(
                series.min(), series.max(), 200
            )
            scale = (
                len(series) *
                (series.max() - series.min()) / 30
            )
            fig.add_trace(go.Scatter(
                x=x_rng,
                y=kde(x_rng) * scale,
                mode="lines",
                name="KDE",
                line=dict(color="#f472b6", width=2),
            ))
        except Exception:
            pass
        return self._to_html(
            self._apply_layout(fig, f"Distribution — {col}")
        )

    def box_plot(
        self, df: pd.DataFrame, cols: list[str]
    ) -> str:
        """Box plots for multiple numeric columns."""
        fig = go.Figure()
        for i, col in enumerate(cols[:12]):
            fig.add_trace(go.Box(
                y=df[col].dropna(),
                name=col,
                marker_color=PALETTE[i % len(PALETTE)],
                boxmean=True,
            ))
        fig.update_layout(showlegend=False)
        return self._to_html(
            self._apply_layout(fig, "Box Plots — Numeric Columns")
        )

    def violin_plot(self, df: pd.DataFrame, col: str) -> str:
        fig = go.Figure(go.Violin(
            y=df[col].dropna(),
            box_visible=True,
            meanline_visible=True,
            fillcolor="#818cf8",
            opacity=0.6,
            line_color="#c7d2fe",
            name=col,
        ))
        return self._to_html(
            self._apply_layout(fig, f"Violin — {col}")
        )

    # ── Categorical charts ─────────────────────────────────────────────

    def bar_chart(
        self, df: pd.DataFrame, col: str, top_n: int = 15
    ) -> str:
        counts = df[col].value_counts().head(top_n).reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(
            counts, x=col, y="count",
            color="count",
            color_continuous_scale=SEQUENTIAL,
        )
        fig.update_layout(
            coloraxis_showscale=False,
            showlegend=False
        )
        return self._to_html(
            self._apply_layout(fig, f"Value Counts — {col}")
        )

    def pie_chart(
        self, df: pd.DataFrame, col: str, top_n: int = 8
    ) -> str:
        counts = df[col].value_counts().head(top_n)
        fig = go.Figure(go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.4,
            marker=dict(colors=PALETTE),
        ))
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label"
        )
        return self._to_html(
            self._apply_layout(fig, f"Composition — {col}")
        )

    # ── Correlation charts ─────────────────────────────────────────────

    def correlation_heatmap(self, df: pd.DataFrame) -> str:
        num_df = df.select_dtypes(include="number")
        if num_df.shape[1] < 2:
            return (
                "<p style='color:#94a3b8'>"
                "Not enough numeric columns.</p>"
            )
        corr = num_df.corr().round(3)
        fig  = go.Figure(go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            colorscale=DIVERGING,
            zmid=0,
            text=corr.values.round(2),
            texttemplate="%{text}",
            textfont=dict(size=10),
        ))
        fig.update_layout(
            height=max(400, len(corr) * 45)
        )
        return self._to_html(
            self._apply_layout(fig, "Correlation Matrix")
        )

    def scatter_plot(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        color_col: str | None = None,
    ) -> str:
        fig = px.scatter(
            df, x=x_col, y=y_col,
            color=color_col,
            opacity=0.7,
            trendline="ols",
            color_discrete_sequence=PALETTE,
        )
        return self._to_html(
            self._apply_layout(fig, f"{x_col} vs {y_col}")
        )

    def scatter_matrix(self, df: pd.DataFrame) -> str:
        num_df = df.select_dtypes(include="number").iloc[:, :6]
        if num_df.shape[1] < 2:
            return (
                "<p style='color:#94a3b8'>"
                "Need at least 2 numeric columns.</p>"
            )
        fig = px.scatter_matrix(
            num_df,
            color_discrete_sequence=PALETTE,
            opacity=0.5
        )
        fig.update_traces(
            diagonal_visible=False,
            marker=dict(size=3)
        )
        fig.update_layout(height=600)
        return self._to_html(
            self._apply_layout(fig, "Scatter Matrix")
        )

    # ── Missing values ─────────────────────────────────────────────────

    def missing_bar(self, df: pd.DataFrame) -> str:
        missing = df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=True)
        if missing.empty:
            return (
                "<p style='color:#4ade80;font-size:14px'>"
                "✅ No missing values found!</p>"
            )
        pct = (missing / len(df) * 100).round(2)
        fig = go.Figure(go.Bar(
            x=pct.values,
            y=pct.index,
            orientation="h",
            marker=dict(
                color=pct.values,
                colorscale="Reds",
                cmin=0, cmax=100,
            ),
            text=[f"{v:.1f}%" for v in pct.values],
            textposition="outside",
        ))
        fig.update_layout(
            xaxis_title="Missing %",
            height=max(300, len(missing) * 35),
        )
        return self._to_html(
            self._apply_layout(fig, "Missing Values by Column")
        )

    def missing_heatmap(self, df: pd.DataFrame) -> str:
        sample      = df.sample(
            min(len(df), 200), random_state=42
        )
        null_matrix = sample.isnull().astype(int)
        fig = go.Figure(go.Heatmap(
            z=null_matrix.T.values,
            x=list(range(len(null_matrix))),
            y=null_matrix.columns.tolist(),
            colorscale=[
                [0, "#1e293b"], [1, "#f87171"]
            ],
            showscale=False,
        ))
        fig.update_layout(
            xaxis_title="Row index (sample)",
            height=max(300, len(df.columns) * 25),
        )
        return self._to_html(
            self._apply_layout(
                fig, "Missing Value Pattern Heatmap"
            )
        )

    # ── Overview charts ────────────────────────────────────────────────

    def dtype_donut(self, df: pd.DataFrame) -> str:
        dtype_counts: dict[str, int] = {}
        for dtype in df.dtypes:
            if pd.api.types.is_numeric_dtype(dtype):
                dtype_counts["Numeric"] = (
                    dtype_counts.get("Numeric", 0) + 1
                )
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                dtype_counts["Datetime"] = (
                    dtype_counts.get("Datetime", 0) + 1
                )
            elif pd.api.types.is_bool_dtype(dtype):
                dtype_counts["Boolean"] = (
                    dtype_counts.get("Boolean", 0) + 1
                )
            else:
                dtype_counts["Categorical"] = (
                    dtype_counts.get("Categorical", 0) + 1
                )

        fig = go.Figure(go.Pie(
            labels=list(dtype_counts.keys()),
            values=list(dtype_counts.values()),
            hole=0.55,
            marker=dict(colors=[
                "#38bdf8", "#a78bfa",
                "#4ade80", "#fb923c"
            ]),
        ))
        fig.update_traces(textinfo="label+percent")
        return self._to_html(
            self._apply_layout(fig, "Column Types")
        )

    def outlier_bar(self, outlier_data: list[dict]) -> str:
        if not outlier_data:
            return (
                "<p style='color:#4ade80;font-size:14px'>"
                "✅ No outliers detected!</p>"
            )
        df_o = pd.DataFrame(outlier_data).head(12)
        fig  = px.bar(
            df_o,
            x="column",
            y="outlier_pct",
            color="outlier_pct",
            color_continuous_scale="Oranges",
            text="outlier_count",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Column",
            yaxis_title="Outlier %",
        )
        return self._to_html(
            self._apply_layout(
                fig, "Outliers by Column (IQR method)"
            )
        )

    def quality_gauge(self, score: float) -> str:
        color = (
            "#4ade80" if score >= 90 else
            "#facc15" if score >= 75 else
            "#fb923c" if score >= 60 else
            "#f87171"
        )
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": "Data Quality Score",
                "font": {"color": FONT_COLOR}
            },
            number={
                "font": {"color": color, "size": 48},
                "suffix": "%"
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": FONT_COLOR
                },
                "bar": {"color": color},
                "bgcolor": BG_COLOR,
                "steps": [
                    {"range": [0,  45],  "color": "#1f1f2e"},
                    {"range": [45, 60],  "color": "#1f2433"},
                    {"range": [60, 75],  "color": "#1f2b33"},
                    {"range": [75, 90],  "color": "#1f3324"},
                    {"range": [90, 100], "color": "#1f3327"},
                ],
                "threshold": {
                    "line": {"color": "#fff", "width": 2},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        ))
        fig.update_layout(
            paper_bgcolor=PAPER_COLOR,
            height=280
        )
        return self._to_html(fig)
