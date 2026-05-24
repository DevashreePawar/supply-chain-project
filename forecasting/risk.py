"""
Reframe point forecasts as probabilistic stock-out risk + order recommendations.

Why this exists:
    "Forecast = 472 units" is false precision when MAPE is 200%.
    "Stock-out risk = 23% under your current safety stock policy" is
    decision-relevant under exactly the same forecast uncertainty.

The reframe works by treating the prediction interval as a proxy for the
demand distribution, then computing the tail probability beyond current stock.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _interval_to_normal(yhat: float, yhat_lower: float, yhat_upper: float,
                        ci_width: float = 0.8) -> tuple[float, float]:
    """Convert a (point, lower, upper) interval into (mean, std) of an
    assumed normal distribution.

    If the interval is 80% (default), z = 1.282 corresponds to the half-width.
    """
    if ci_width == 0.8:
        z = 1.282
    elif ci_width == 0.9:
        z = 1.645
    elif ci_width == 0.95:
        z = 1.960
    else:
        # Inverse-CDF for normal; statsmodels has this but use scipy
        from scipy.stats import norm
        z = norm.ppf(0.5 + ci_width / 2.0)

    half_width = (yhat_upper - yhat_lower) / 2.0
    std = half_width / z if z > 0 else 0.0
    return float(yhat), max(float(std), 1e-6)  # clamp std away from zero


def stockout_probability(
    forecast_total_units: float,
    forecast_lower: float,
    forecast_upper: float,
    current_stock_units: float,
    ci_width: float = 0.8,
) -> float:
    """Probability that demand exceeds current stock over the forecast window.

    Returns a value in [0, 1].
    """
    from scipy.stats import norm

    mean, std = _interval_to_normal(
        forecast_total_units, forecast_lower, forecast_upper, ci_width
    )
    # P(demand > stock) = 1 - CDF(stock)
    return float(1.0 - norm.cdf(current_stock_units, loc=mean, scale=std))


def recommended_order_quantity(
    forecast_total_units: float,
    forecast_lower: float,
    forecast_upper: float,
    current_stock_units: float,
    target_risk: float = 0.05,
    ci_width: float = 0.8,
) -> float:
    """Smallest order quantity that keeps stock-out risk at or below `target_risk`.

    Args:
        forecast_*: forecast distribution parameters (point + bounds)
        current_stock_units: how many units we already have
        target_risk: acceptable probability of stock-out (default 5%)

    Returns: additional units to order (rounded up to nearest integer).
    """
    from scipy.stats import norm

    mean, std = _interval_to_normal(
        forecast_total_units, forecast_lower, forecast_upper, ci_width
    )
    # We want stock_level such that P(demand > stock_level) <= target_risk
    # i.e., stock_level >= inv_CDF(1 - target_risk)
    required_stock = norm.ppf(1.0 - target_risk, loc=mean, scale=std)
    order_qty = max(0.0, required_stock - current_stock_units)
    return float(np.ceil(order_qty))


def build_risk_table(
    forecasts_by_category: dict[int, pd.DataFrame],
    current_stock_by_category: dict[int, float],
    target_risks: list[float] = (0.05, 0.10, 0.20),
) -> pd.DataFrame:
    """For each category, compute:
       - 4-week forecast total (point + interval)
       - current stock
       - stock-out probability under current stock
       - recommended order qty at each target_risk level

    Args:
        forecasts_by_category: {category_id: forecast DataFrame with
            yhat/yhat_lower/yhat_upper columns}
        current_stock_by_category: {category_id: units on hand}
    """
    rows = []
    for cat_id, fc in forecasts_by_category.items():
        total_point = float(fc["yhat"].sum())
        total_lower = float(fc["yhat_lower"].sum())
        total_upper = float(fc["yhat_upper"].sum())
        current_stock = float(current_stock_by_category.get(cat_id, 0))

        row = {
            "category_id": cat_id,
            "forecast_4w_units": total_point,
            "forecast_lower_80": total_lower,
            "forecast_upper_80": total_upper,
            "current_stock_units": current_stock,
            "stockout_prob_current": stockout_probability(
                total_point, total_lower, total_upper, current_stock
            ),
        }
        for risk in target_risks:
            qty = recommended_order_quantity(
                total_point, total_lower, total_upper, current_stock, target_risk=risk
            )
            row[f"order_qty_at_{int(risk*100)}pct_risk"] = qty
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("stockout_prob_current", ascending=False)
    df["risk_band"] = pd.cut(
        df["stockout_prob_current"],
        bins=[-0.001, 0.05, 0.20, 0.50, 1.001],
        labels=["LOW (<5%)", "MEDIUM (5-20%)", "HIGH (20-50%)", "CRITICAL (>50%)"],
    )
    return df
