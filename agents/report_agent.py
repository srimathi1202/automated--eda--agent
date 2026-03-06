"""
agents/report_agent.py
-----------------------
Assembles all profile data, charts, and AI insights into a
single self-contained HTML dashboard file.
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.base_agent import BaseAgent
from config.settings import OUTPUTS_DIR


class ReportAgent(BaseAgent):
    """Builds the final HTML dashboard."""

    def __init__(self, verbose: bool = False):
        super().__init__("ReportAgent", verbose)

    def run(self, context: dict) -> dict[str, Any]:
        filename    = context.get("filename", "dataset")
        profile     = context["profile"]
        insights    = context["insights"]
        charts      = context["charts"]
        output_path = context.get("output_path") or str(
            OUTPUTS_DIR /
            f"eda_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        self.log_step("Assembling HTML dashboard")
        html = self._build_dashboard(
            filename, profile, insights, charts
        )
        Path(output_path).write_text(html, encoding="utf-8")
        self.log_step("Dashboard saved", output_path)

        return {"dashboard_path": output_path, "html": html}

    def _build_dashboard(
        self,
        filename: str,
        profile:  dict,
        insights: dict,
        charts:   dict,
    ) -> str:

        ov   = profile.get("overview", {})
        qual = profile.get("data_quality", {})
        miss = profile.get("missing", {})
        cols = profile.get("column_stats", [])
        corr = profile.get("correlations", {})
        now  = datetime.now().strftime("%B %d, %Y at %H:%M")

        score = qual.get("overall_score", 0)
        grade = qual.get("grade", "?")
        score_color = (
            "#4ade80" if score >= 90 else
            "#facc15" if score >= 75 else
            "#fb923c" if score >= 60 else
            "#f87171"
        )

        # Column stats table
        col_rows = ""
        for c in cols:
            kind  = c.get("kind", "")
            badge = (
                '<span class="badge badge-num">numeric</span>'
                if kind == "numeric"
                else '<span class="badge badge-cat">categorical</span>'
            )
            miss_v = c.get("missing_pct", 0)
            miss_c = (
                "text-red"    if miss_v > 20 else
                "text-yellow" if miss_v > 5  else
                "text-green"
            )
            if kind == "numeric":
                extra = (
                    f'{c.get("mean","—")} / {c.get("median","—")}'
                )
            else:
                tv    = c.get("top_values", [])
                extra = ", ".join(str(v) for v in tv[:3])

            col_rows += f"""
            <tr>
              <td><strong>{c["column"]}</strong></td>
              <td>{badge}</td>
              <td class="{miss_c}">{miss_v}%</td>
              <td>{c.get("unique_count","—")}</td>
              <td>{extra}</td>
            </tr>"""

        # Correlation table
        corr_rows = ""
        for p in corr.get("strong_pairs", [])[:8]:
            dir_color = (
                "#4ade80" if p["direction"] == "positive"
                else "#f87171"
            )
            corr_rows += f"""
            <tr>
              <td>{p["col_a"]}</td>
              <td>{p["col_b"]}</td>
              <td style="color:{dir_color};font-weight:700">
                {p["r"]}
              </td>
              <td><span class="badge badge-corr">
                {p["strength"].replace("_"," ")}
              </span></td>
            </tr>"""

        # Insight lists
        insight_items = "".join(
            f'<li class="insight-item">'
            f'<span class="insight-num">{i+1}</span>'
            f'{ins}</li>'
            for i, ins in enumerate(
                insights.get("key_insights", [])
            )
        )
        anomaly_items = "".join(
            f'<li class="anomaly-item">⚠️ {a}</li>'
            for a in insights.get("anomalies", [])
        )
        rec_items = "".join(
            f'<li class="rec-item">✅ {r}</li>'
            for r in insights.get("recommendations", [])
        )

        # Chart grids
        hist_grid = "".join(
            f'<div class="chart-card">{h["html"]}</div>'
            for h in charts.get("histograms", [])
        )
        bar_grid = "".join(
            f'<div class="chart-card">{b["html"]}</div>'
            for b in charts.get("bar_charts", [])
        )
        pie_grid = "".join(
            f'<div class="chart-card">{p["html"]}</div>'
            for p in charts.get("pie_charts", [])
        )
        scatter_grid = "".join(
            f'<div class="chart-card">'
            f'<div class="corr-label">r = {s["r"]}</div>'
            f'{s["html"]}</div>'
            for s in charts.get("scatter_plots", [])
        )
        violin_grid = "".join(
            f'<div class="chart-card">{v["html"]}</div>'
            for v in charts.get("violin_plots", [])
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>EDA Dashboard — {filename}</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0a0d16;--surface:#111827;--surface2:#1a2035;
  --border:#1e2d4a;--text:#e2e8f0;--muted:#64748b;
  --accent:#38bdf8;--purple:#a78bfa;--green:#4ade80;
  --yellow:#facc15;--red:#f87171;--orange:#fb923c;
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);
      font-family:'Syne',sans-serif;line-height:1.6}}
.sidebar{{
  position:fixed;top:0;left:0;width:220px;height:100vh;
  background:var(--surface);border-right:1px solid var(--border);
  padding:32px 0;z-index:100;
}}
.logo-wrap{{padding:0 24px 32px;border-bottom:1px solid var(--border)}}
.logo-text{{font-size:18px;font-weight:800;color:#fff}}
.logo-sub{{font-size:11px;color:var(--muted);margin-top:2px}}
.nav-sec{{padding:20px 24px 8px;font-size:10px;font-weight:700;
          color:var(--muted);letter-spacing:2px;text-transform:uppercase}}
.nav-link{{
  display:block;padding:10px 24px;color:var(--muted);
  text-decoration:none;font-size:13px;font-weight:600;
  border-left:3px solid transparent;transition:all 0.2s;
}}
.nav-link:hover{{
  color:var(--accent);background:rgba(56,189,248,0.05);
  border-left-color:var(--accent);
}}
.main{{margin-left:220px;min-height:100vh}}
.hero{{
  background:linear-gradient(135deg,#0d1f3c,#1a1040,#0d2a1f);
  padding:60px 48px;border-bottom:1px solid var(--border);
}}
.hero-badge{{
  display:inline-block;padding:4px 14px;
  background:rgba(56,189,248,0.1);
  border:1px solid rgba(56,189,248,0.3);
  border-radius:999px;font-size:11px;font-weight:700;
  color:var(--accent);letter-spacing:2px;
  text-transform:uppercase;margin-bottom:16px;
}}
.hero h1{{font-size:36px;font-weight:800;color:#fff;
          line-height:1.2;margin-bottom:8px}}
.hero-file{{font-family:'JetBrains Mono',monospace;
            font-size:14px;color:var(--muted)}}
.hero-meta{{margin-top:8px;font-size:12px;color:var(--muted)}}
.section{{padding:48px;border-bottom:1px solid var(--border)}}
.sec-title{{font-size:22px;font-weight:800;color:#fff;
            margin-bottom:4px;display:flex;align-items:center;gap:12px}}
.sec-sub{{color:var(--muted);font-size:13px;margin-bottom:32px}}
.kpi-grid{{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(160px,1fr));
  gap:16px;margin-bottom:32px;
}}
.kpi{{background:var(--surface2);border:1px solid var(--border);
      border-radius:14px;padding:24px 20px}}
.kpi-val{{font-size:32px;font-weight:800;color:var(--accent);line-height:1}}
.kpi-lbl{{font-size:11px;color:var(--muted);margin-top:6px;
          text-transform:uppercase;letter-spacing:1px;font-weight:700}}
.chart-grid{{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(480px,1fr));
  gap:20px;
}}
.chart-grid.sm{{
  grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
}}
.chart-card{{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:14px;padding:8px;overflow:hidden;position:relative;
}}
.corr-label{{
  position:absolute;top:16px;right:16px;
  background:rgba(167,139,250,0.15);
  border:1px solid rgba(167,139,250,0.3);
  color:var(--purple);font-size:12px;font-weight:700;
  padding:3px 10px;border-radius:6px;
  font-family:'JetBrains Mono',monospace;z-index:1;
}}
.qual-grid{{display:grid;grid-template-columns:280px 1fr;
            gap:24px;align-items:start}}
.qual-sub{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}}
.qual-box{{background:var(--surface2);border:1px solid var(--border);
           border-radius:12px;padding:20px;text-align:center}}
.q-val{{font-size:28px;font-weight:800}}
.q-lbl{{font-size:11px;color:var(--muted);margin-top:4px;
        text-transform:uppercase;letter-spacing:1px}}
.ins-grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.ins-box{{background:var(--surface2);border:1px solid var(--border);
          border-radius:14px;padding:28px}}
.ins-box h3{{font-size:13px;font-weight:700;text-transform:uppercase;
             letter-spacing:1.5px;margin-bottom:20px}}
.h3-ai{{color:var(--purple)}} .h3-warn{{color:var(--orange)}}
.h3-rec{{color:var(--green)}} .h3-story{{color:var(--accent)}}
ul.ins-list{{list-style:none;padding:0}}
.insight-item{{
  display:flex;gap:12px;align-items:flex-start;
  padding:10px 0;border-bottom:1px solid var(--border);
  font-size:13px;color:#cbd5e1;
}}
.insight-item:last-child{{border-bottom:none}}
.insight-num{{
  min-width:24px;height:24px;
  background:rgba(167,139,250,0.15);color:var(--purple);
  border-radius:6px;display:flex;align-items:center;
  justify-content:center;font-size:11px;font-weight:800;
}}
.anomaly-item{{padding:8px 0;border-bottom:1px solid var(--border);
               font-size:13px;color:#fcd34d;list-style:none}}
.rec-item{{padding:8px 0;border-bottom:1px solid var(--border);
           font-size:13px;color:#86efac;list-style:none}}
.story-text{{font-size:14px;color:#cbd5e1;
             line-height:1.8;font-style:italic}}
.tbl-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
thead tr{{background:var(--surface)}}
th{{padding:14px 16px;text-align:left;font-size:11px;font-weight:700;
    color:var(--muted);text-transform:uppercase;letter-spacing:1px;
    border-bottom:1px solid var(--border)}}
td{{padding:12px 16px;border-bottom:1px solid var(--border);
    vertical-align:middle}}
tr:hover td{{background:rgba(255,255,255,0.02)}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;
        font-size:10px;font-weight:700;
        text-transform:uppercase;letter-spacing:0.5px}}
.badge-num{{background:rgba(56,189,248,0.12);color:#38bdf8}}
.badge-cat{{background:rgba(167,139,250,0.12);color:#a78bfa}}
.badge-corr{{background:rgba(74,222,128,0.12);color:#4ade80}}
.text-red{{color:var(--red);font-weight:700}}
.text-yellow{{color:var(--yellow);font-weight:700}}
.text-green{{color:var(--green);font-weight:700}}
.footer{{padding:32px 48px;text-align:center;
         color:var(--muted);font-size:12px}}
::-webkit-scrollbar{{width:6px;height:6px}}
::-webkit-scrollbar-track{{background:var(--surface)}}
::-webkit-scrollbar-thumb{{background:#2d3748;border-radius:3px}}
@media(max-width:900px){{
  .sidebar{{display:none}}
  .main{{margin-left:0}}
  .hero,.section{{padding:32px 24px}}
  .chart-grid,.ins-grid,.qual-grid{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<nav class="sidebar">
  <div class="logo-wrap">
    <div class="logo-text">📊 EDA Agent</div>
    <div class="logo-sub">Automated Analysis</div>
  </div>
  <div class="nav-sec">Sections</div>
  <a href="#overview"      class="nav-link">🗂 Overview</a>
  <a href="#quality"       class="nav-link">🏅 Data Quality</a>
  <a href="#insights"      class="nav-link">🤖 AI Insights</a>
  <a href="#distributions" class="nav-link">📈 Distributions</a>
  <a href="#categories"    class="nav-link">🗃 Categories</a>
  <a href="#correlations"  class="nav-link">🔗 Correlations</a>
  <a href="#missing"       class="nav-link">❓ Missing Values</a>
  <a href="#outliers"      class="nav-link">🎯 Outliers</a>
  <a href="#columns"       class="nav-link">📋 Column Stats</a>
</nav>
<main class="main">
  <div class="hero">
    <div class="hero-badge">Automated EDA Report</div>
    <h1>{insights.get("headline","Exploratory Data Analysis Complete")}</h1>
    <div class="hero-file">📁 {filename}</div>
    <div class="hero-meta">Generated {now} · Powered by Claude AI</div>
  </div>

  <section class="section" id="overview">
    <div class="sec-title">🗂 Dataset Overview</div>
    <div class="sec-sub">High-level statistics about your dataset</div>
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-val">{ov.get("rows",0):,}</div>
        <div class="kpi-lbl">Total Rows</div></div>
      <div class="kpi"><div class="kpi-val">{ov.get("columns",0)}</div>
        <div class="kpi-lbl">Columns</div></div>
      <div class="kpi"><div class="kpi-val">{ov.get("numeric_cols",0)}</div>
        <div class="kpi-lbl">Numeric Cols</div></div>
      <div class="kpi"><div class="kpi-val">{ov.get("categorical_cols",0)}</div>
        <div class="kpi-lbl">Categorical Cols</div></div>
      <div class="kpi"><div class="kpi-val">{ov.get("missing_pct",0):.1f}%</div>
        <div class="kpi-lbl">Missing Data</div></div>
      <div class="kpi"><div class="kpi-val">{ov.get("duplicate_rows",0)}</div>
        <div class="kpi-lbl">Duplicates</div></div>
      <div class="kpi"><div class="kpi-val">{ov.get("memory_mb",0):.2f}</div>
        <div class="kpi-lbl">Size (MB)</div></div>
    </div>
    <div class="chart-grid" style="grid-template-columns:1fr 1fr;max-width:800px">
      <div class="chart-card">{charts.get("dtype_donut","")}</div>
      <div class="chart-card">{charts.get("quality_gauge","")}</div>
    </div>
  </section>

  <section class="section" id="quality">
    <div class="sec-title">🏅 Data Quality Score</div>
    <div class="sec-sub">Completeness, uniqueness and consistency</div>
    <div class="qual-grid">
      <div class="chart-card">{charts.get("quality_gauge","")}</div>
      <div class="qual-sub">
        <div class="qual-box">
          <div class="q-val" style="color:#38bdf8">
            {qual.get("completeness",0):.0f}%</div>
          <div class="q-lbl">Completeness</div>
        </div>
        <div class="qual-box">
          <div class="q-val" style="color:#a78bfa">
            {qual.get("uniqueness",0):.0f}%</div>
          <div class="q-lbl">Uniqueness</div>
        </div>
        <div class="qual-box">
          <div class="q-val" style="color:#4ade80">
            {qual.get("consistency",0):.0f}%</div>
          <div class="q-lbl">Consistency</div>
        </div>
        <div class="qual-box" style="grid-column:span 3">
          <div class="q-val"
            style="color:{score_color};font-size:48px">{grade}</div>
          <div class="q-lbl">Overall Grade · {score:.1f}/100</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="insights">
    <div class="sec-title">🤖 AI Insights</div>
    <div class="sec-sub">Generated by Claude AI</div>
    <div class="ins-grid">
      <div class="ins-box">
        <h3 class="h3-ai">🔍 Key Insights</h3>
        <ul class="ins-list">{insight_items}</ul>
      </div>
      <div style="display:flex;flex-direction:column;gap:20px">
        <div class="ins-box">
          <h3 class="h3-warn">⚠️ Anomalies</h3>
          <ul class="ins-list">
            {anomaly_items or
             "<li class='insight-item'>No anomalies detected.</li>"}
          </ul>
        </div>
        <div class="ins-box">
          <h3 class="h3-rec">✅ Recommendations</h3>
          <ul class="ins-list">{rec_items}</ul>
        </div>
      </div>
    </div>
    <div class="ins-box" style="margin-top:20px">
      <h3 class="h3-story">📖 Data Story</h3>
      <p class="story-text">{insights.get("data_story","")}</p>
    </div>
  </section>

  <section class="section" id="distributions">
    <div class="sec-title">📈 Numeric Distributions</div>
    <div class="sec-sub">Histograms, box plots and violin plots</div>
    <div class="chart-grid">{hist_grid}</div>
    {f'<div class="chart-card" style="margin-top:20px">{charts.get("box_plots","")}</div>'
     if charts.get("box_plots") else ""}
    <div class="chart-grid sm" style="margin-top:20px">{violin_grid}</div>
  </section>

  <section class="section" id="categories">
    <div class="sec-title">🗃 Categorical Analysis</div>
    <div class="sec-sub">Value counts and composition</div>
    <div class="chart-grid">{bar_grid}</div>
    <div class="chart-grid sm" style="margin-top:20px">{pie_grid}</div>
  </section>

  <section class="section" id="correlations">
    <div class="sec-title">🔗 Correlation Analysis</div>
    <div class="sec-sub">Relationships between numeric variables</div>
    <div class="chart-grid">
      <div class="chart-card">
        {charts.get("correlation_heatmap",
         "<p style='color:#64748b;padding:20px'>Not enough numeric columns.</p>")}
      </div>
      <div class="chart-card">{charts.get("scatter_matrix","")}</div>
    </div>
    <div class="chart-grid" style="margin-top:20px">{scatter_grid}</div>
    {f'''<div class="tbl-wrap" style="margin-top:24px">
      <table>
        <thead><tr>
          <th>Column A</th><th>Column B</th>
          <th>Correlation r</th><th>Strength</th>
        </tr></thead>
        <tbody>{corr_rows}</tbody>
      </table>
    </div>''' if corr_rows else ""}
  </section>

  <section class="section" id="missing">
    <div class="sec-title">❓ Missing Value Analysis</div>
    <div class="sec-sub">
      {miss.get("total_missing",0):,} missing cells across
      {miss.get("columns_affected",0)} columns
    </div>
    <div class="chart-grid">
      <div class="chart-card">{charts.get("missing_bar","")}</div>
      <div class="chart-card">{charts.get("missing_heatmap","")}</div>
    </div>
  </section>

  <section class="section" id="outliers">
    <div class="sec-title">🎯 Outlier Detection</div>
    <div class="sec-sub">IQR-based outlier detection</div>
    <div class="chart-card" style="max-width:900px">
      {charts.get("outlier_bar","")}
    </div>
  </section>

  <section class="section" id="columns">
    <div class="sec-title">📋 Column Statistics</div>
    <div class="sec-sub">Detailed per-column statistics</div>
    <div class="tbl-wrap">
      <table>
        <thead><tr>
          <th>Column</th><th>Type</th><th>Missing %</th>
          <th>Unique</th><th>Stats / Top Values</th>
        </tr></thead>
        <tbody>{col_rows}</tbody>
      </table>
    </div>
  </section>

  <div class="footer">
    📊 Automated EDA Agent · Powered by Claude AI · {now}
  </div>
</main>
</body>
</html>"""
