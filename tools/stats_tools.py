"""
tools/stats_tools.py
---------------------
Statistical profiling utilities for EDA.
All functions are pure and return serialisable dicts.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")


class StatsTools:
    """Comprehensive statistical profiling for any DataFrame."""

    def full_profile(self, df: pd.DataFrame) -> dict[str, Any]:
        """Run the complete profiling pipeline."""
        return {
            "overview":      self.overview(df),
            "column_stats":  self.column_stats(df),
            "missing":       self.missing_analysis(df),
            "correlations":  self.correlation_analysis(df),
            "outliers":      self.outlier_analysis(df),
            "data_quality":  self.data_quality_score(df),
            "distributions": self.distribution_tests(df),
        }

    def overview(self, df: pd.DataFrame) -> dict:
        num_cols  = df.select_dtypes(
            include="number"
        ).columns.tolist()
        cat_cols  = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()
        date_cols = df.select_dtypes(
            include=["datetime", "datetimetz"]
        ).columns.tolist()

        return {
            "rows":             int(len(df)),
            "columns":          int(len(df.columns)),
            "numeric_cols":     len(num_cols),
            "categorical_cols": len(cat_cols),
            "datetime_cols":    len(date_cols),
            "total_cells":      int(df.size),
            "missing_cells":    int(df.isnull().sum().sum()),
            "missing_pct":      round(
                df.isnull().sum().sum() / df.size * 100, 2
            ),
            "duplicate_rows":   int(df.duplicated().sum()),
            "memory_mb":        round(
                df.memory_usage(deep=True).sum() / 1e6, 3
            ),
            "column_names":     df.columns.tolist(),
            "dtypes": {
                c: str(t) for c, t in df.dtypes.items()
            },
        }

    def column_stats(self, df: pd.DataFrame) -> list[dict]:
        results = []
        for col in df.columns:
            series = df[col]
            base = {
                "column":        col,
                "dtype":         str(series.dtype),
                "missing_count": int(series.isnull().sum()),
                "missing_pct":   round(
                    series.isnull().mean() * 100, 2
                ),
                "unique_count":  int(series.nunique()),
                "unique_pct":    round(
                    series.nunique() / len(df) * 100, 2
                ) if len(df) > 0 else 0,
            }

            if pd.api.types.is_numeric_dtype(series):
                base.update({
                    "kind":     "numeric",
                    "mean":     round(float(series.mean()), 4)
                                if not series.isnull().all() else None,
                    "median":   round(float(series.median()), 4)
                                if not series.isnull().all() else None,
                    "std":      round(float(series.std()), 4)
                                if not series.isnull().all() else None,
                    "min":      round(float(series.min()), 4)
                                if not series.isnull().all() else None,
                    "max":      round(float(series.max()), 4)
                                if not series.isnull().all() else None,
                    "q1":       round(float(series.quantile(0.25)), 4)
                                if not series.isnull().all() else None,
                    "q3":       round(float(series.quantile(0.75)), 4)
                                if not series.isnull().all() else None,
                    "skewness": round(float(series.skew()), 4)
                                if not series.isnull().all() else None,
                    "kurtosis": round(float(series.kurtosis()), 4)
                                if not series.isnull().all() else None,
                    "zeros":    int((series == 0).sum()),
                    "negatives":int((series < 0).sum()),
                })
            else:
                top_vals = series.value_counts().head(5)
                base.update({
                    "kind":       "categorical",
                    "top_values": top_vals.index.tolist(),
                    "top_counts": top_vals.values.tolist(),
                    "avg_str_length": round(
                        series.dropna().astype(str)
                              .str.len().mean(), 1
                    ) if not series.isnull().all() else None,
                })

            results.append(base)
        return results

    def missing_analysis(self, df: pd.DataFrame) -> dict:
        missing     = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        cols_miss   = missing[missing > 0]

        return {
            "total_missing":    int(missing.sum()),
            "columns_affected": int((missing > 0).sum()),
            "per_column": [
                {
                    "column":   col,
                    "count":    int(cols_miss[col]),
                    "pct":      float(missing_pct[col]),
                    "severity": (
                        "critical" if missing_pct[col] > 50 else
                        "high"     if missing_pct[col] > 20 else
                        "medium"   if missing_pct[col] > 5  else
                        "low"
                    ),
                }
                for col in cols_miss.index
            ],
        }

    def correlation_analysis(self, df: pd.DataFrame) -> dict:
        num_df = df.select_dtypes(include="number")
        if num_df.shape[1] < 2:
            return {"matrix": {}, "strong_pairs": []}

        corr = num_df.corr().round(4)
        strong_pairs = []
        cols = corr.columns.tolist()

        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if abs(val) >= 0.5:
                    strong_pairs.append({
                        "col_a":     cols[i],
                        "col_b":     cols[j],
                        "r":         round(float(val), 4),
                        "strength": (
                            "very_strong" if abs(val) >= 0.9 else
                            "strong"      if abs(val) >= 0.7 else
                            "moderate"
                        ),
                        "direction": (
                            "positive" if val > 0 else "negative"
                        ),
                    })

        strong_pairs.sort(
            key=lambda x: abs(x["r"]), reverse=True
        )
        return {
            "matrix":       corr.fillna(0).to_dict(),
            "strong_pairs": strong_pairs,
        }

    def outlier_analysis(self, df: pd.DataFrame) -> list[dict]:
        results  = []
        num_cols = df.select_dtypes(include="number").columns

        for col in num_cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue

            q1  = series.quantile(0.25)
            q3  = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_mask  = (series < lower) | (series > upper)
            outlier_count = int(outlier_mask.sum())

            results.append({
                "column":        col,
                "outlier_count": outlier_count,
                "outlier_pct":   round(
                    outlier_count / len(series) * 100, 2
                ),
                "lower_fence":   round(float(lower), 4),
                "upper_fence":   round(float(upper), 4),
                "min_value":     round(float(series.min()), 4),
                "max_value":     round(float(series.max()), 4),
                "sample_outliers": series[outlier_mask].head(5).tolist(),
            })

        return sorted(
            results, key=lambda x: x["outlier_count"], reverse=True
        )

    def data_quality_score(self, df: pd.DataFrame) -> dict:
        total_cells    = df.size
        missing_cells  = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        completeness = max(
            0, 100 - (missing_cells / total_cells * 100)
        ) if total_cells else 100

        uniqueness = max(
            0, 100 - (duplicate_rows / len(df) * 100)
        ) if len(df) else 100

        inconsistency_count = 0
        for col in df.select_dtypes(include="object").columns:
            numeric_ratio = pd.to_numeric(
                df[col], errors="coerce"
            ).notna().mean()
            if numeric_ratio > 0.8:
                inconsistency_count += 1

        consistency = max(
            0,
            100 - (
                inconsistency_count /
                max(len(df.columns), 1) * 100
            )
        )

        overall = round(
            (completeness * 0.4 +
             uniqueness   * 0.3 +
             consistency  * 0.3), 1
        )

        return {
            "overall_score": overall,
            "completeness":  round(completeness, 1),
            "uniqueness":    round(uniqueness, 1),
            "consistency":   round(consistency, 1),
            "grade": (
                "A" if overall >= 90 else
                "B" if overall >= 75 else
                "C" if overall >= 60 else
                "D" if overall >= 45 else
                "F"
            ),
        }

    def distribution_tests(self, df: pd.DataFrame) -> list[dict]:
        results  = []
        num_cols = df.select_dtypes(include="number").columns

        for col in num_cols:
            series = df[col].dropna()
            if len(series) < 8:
                continue
            try:
                _, p_value = stats.shapiro(
                    series.sample(
                        min(len(series), 5000), random_state=42
                    )
                )
                skew = float(series.skew())
                results.append({
                    "column":    col,
                    "is_normal": bool(p_value > 0.05),
                    "shapiro_p": round(float(p_value), 6),
                    "skewness":  round(skew, 4),
                    "skew_type": (
                        "highly_right_skewed" if skew > 1    else
                        "right_skewed"        if skew > 0.5  else
                        "symmetric"           if abs(skew) <= 0.5 else
                        "left_skewed"         if skew > -1   else
                        "highly_left_skewed"
                    ),
                })
            except Exception:
                pass

        return results
