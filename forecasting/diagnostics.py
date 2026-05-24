"""
Root-cause analysis for why forecast MAPE is so high.

This module DOESN'T forecast — it diagnoses. The output explains which
categories are inherently hard to forecast and why, so we can:
  (a) calibrate expectations honestly
  (b) reframe the deliverable away from point forecasts where appropriate
  (c) flag categories where better data, not a better model, is the fix.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def basic_stats(series: pd.Series) -> dict:
    """Mean, median, std, min, max for a single category's weekly demand."""
    s = series.dropna()
    return {
        "n_weeks": int(s.shape[0]),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "std": float(s.std()),
        "min": float(s.min()),
        "max": float(s.max()),
        "zero_weeks": int((s == 0).sum()),
        "zero_pct": float((s == 0).mean() * 100),
    }


def coefficient_of_variation(series: pd.Series) -> float:
    """CV = std/mean. Higher = more volatile, harder to forecast.
    CV > 1 generally means demand is bursty; classical models struggle."""
    s = series.dropna()
    mean = s.mean()
    if mean == 0:
        return float("inf")
    return float(s.std() / mean)


def outlier_count(series: pd.Series, k: float = 3.0) -> dict:
    """Count outliers using two definitions:
       - z-score > k (assumes ~normal)
       - IQR method: outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] (robust)
    """
    s = series.dropna().astype(float)
    z_scores = np.abs(stats.zscore(s)) if s.std() > 0 else np.zeros(len(s))
    z_outliers = int((z_scores > k).sum())

    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    iqr_outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())

    return {
        "z_outliers": z_outliers,
        "iqr_outliers": iqr_outliers,
        "iqr_outlier_pct": float(iqr_outliers / len(s) * 100) if len(s) else 0.0,
    }


def structural_break_test(series: pd.Series) -> dict:
    """Compare the mean of the first half vs second half of the series.
    A large shift suggests a structural break — demand regime changed mid-history,
    making historical patterns less informative for the future.
    """
    s = series.dropna().astype(float)
    if len(s) < 20:
        return {"first_half_mean": float("nan"), "second_half_mean": float("nan"),
                "shift_pct": float("nan"), "p_value": float("nan")}
    mid = len(s) // 2
    first, second = s.iloc[:mid], s.iloc[mid:]
    first_mean, second_mean = first.mean(), second.mean()

    # Welch's t-test — doesn't assume equal variance between halves
    t_stat, p_value = stats.ttest_ind(first, second, equal_var=False, nan_policy="omit")
    shift_pct = ((second_mean - first_mean) / first_mean * 100) if first_mean != 0 else float("nan")

    return {
        "first_half_mean": float(first_mean),
        "second_half_mean": float(second_mean),
        "shift_pct": float(shift_pct),
        "p_value": float(p_value),
    }


def diagnose_category(series: pd.Series, category_id: int) -> dict:
    """Run all diagnostics on one category. Returns a flat dict."""
    out = {"category_id": category_id}
    out.update(basic_stats(series))
    out["cv"] = coefficient_of_variation(series)
    out.update(outlier_count(series))
    sb = structural_break_test(series)
    out.update({f"struct_{k}": v for k, v in sb.items()})

    # Bottom-line interpretation
    diagnoses = []
    if out["mean"] < 50:
        diagnoses.append("SMALL_BASELINE")  # MAPE blows up by definition
    if out["cv"] > 1.0:
        diagnoses.append("HIGH_VOLATILITY")
    if out["iqr_outlier_pct"] > 10:
        diagnoses.append("MANY_OUTLIERS")
    if abs(out["struct_shift_pct"]) > 50 and out["struct_p_value"] < 0.05:
        diagnoses.append("STRUCTURAL_BREAK")
    if out["zero_pct"] > 20:
        diagnoses.append("INTERMITTENT_DEMAND")
    out["diagnoses"] = ",".join(diagnoses) if diagnoses else "BENIGN"
    return out


def diagnose_all(df: pd.DataFrame) -> pd.DataFrame:
    """Run diagnose_category on every category in the dataframe."""
    rows = []
    for cat_id in sorted(df["category_id"].unique()):
        series = df[df["category_id"] == cat_id].set_index("order_week")["units_sold"]
        rows.append(diagnose_category(series, int(cat_id)))
    return pd.DataFrame(rows)
