"""
Forecast error metrics.

Why we report multiple metrics (not just MAPE):
- MAPE blows up when actuals are small (a tiny baseline produces huge %).
- sMAPE is symmetric but still scale-dependent.
- MAE/RMSE are in original units — interpretable, comparable across models
  for the same category, NOT comparable across categories.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def mape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Mean Absolute Percentage Error. Skips rows where actual == 0."""
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    mask = actual != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - forecast[mask]) / actual[mask])) * 100)


def smape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Symmetric MAPE — bounded in [0, 200%], better behaved near zero."""
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    denom = (np.abs(actual) + np.abs(forecast)) / 2.0
    mask = denom != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs(actual[mask] - forecast[mask]) / denom[mask]) * 100)


def mae(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Mean Absolute Error — in original units."""
    return float(np.mean(np.abs(np.asarray(actual) - np.asarray(forecast))))


def rmse(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Root Mean Squared Error — penalizes large errors more than MAE."""
    diff = np.asarray(actual, dtype=float) - np.asarray(forecast, dtype=float)
    return float(np.sqrt(np.mean(diff ** 2)))


def all_metrics(actual: np.ndarray, forecast: np.ndarray) -> dict[str, float]:
    """Compute all four metrics and return as a dict."""
    return {
        "mape": mape(actual, forecast),
        "smape": smape(actual, forecast),
        "mae": mae(actual, forecast),
        "rmse": rmse(actual, forecast),
    }


def summarize_by_category(per_fold_metrics: list[dict]) -> pd.DataFrame:
    """Aggregate per-fold metrics into category-level summary statistics."""
    df = pd.DataFrame(per_fold_metrics)
    grouped = df.groupby(["category_id", "model"]).agg(
        mean_mape=("mape", "mean"),
        median_mape=("mape", "median"),
        mean_smape=("smape", "mean"),
        mean_mae=("mae", "mean"),
        mean_rmse=("rmse", "mean"),
        n_folds=("mape", "count"),
    ).reset_index()
    return grouped
