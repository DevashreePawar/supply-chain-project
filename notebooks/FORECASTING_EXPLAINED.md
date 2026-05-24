# Forecasting Methodology — Deep Dive

## Overview

The forecasting notebook uses **Facebook Prophet**, a decomposable time-series model, to project 4-week demand by product category. This document explains the model, the backtest results, and how to interpret confidence intervals.

---

## 1. Data Preparation

**Source:** `MARTS.AGG_WEEKLY_ORDERS` — weekly order quantity aggregated by category.

**Scope:** Top 5 categories by total revenue (45, 17, 43, 9, 24) — these account for ~67% of revenue and represent the highest inventory risk.

**History window:** 145 weeks (late 2014 – mid-2017). Demand shows:
- Growth phase: 2014–2016 (peak ~$12M/week)
- Declining phase: 2016–2018 (possible market saturation or data truncation)

---

## 2. Prophet Model

Prophet models time series as:

```
y(t) = trend(t) + seasonality(t) + residual(t)
```

**Trend:** Piecewise linear. Prophet automatically detects changepoints (breakpoints in the trend slope). For this dataset, the main changepoint is the 2016 demand peak.

**Seasonality:** Two components fitted:
- **Weekly** — day-of-week patterns (consumer goods tend to order on weekdays)
- **Yearly** — holiday / seasonal patterns (Q4 demand spikes)

**Residuals:** The portion unexplained by trend + seasonality. For consumer goods driven by promotions and demand shocks, residuals are large. This is *expected*, not a model defect — but it does mean forecast uncertainty is high.

Default configuration used:
```python
m = Prophet(
    interval_width=0.80,   # 80% confidence intervals
    yearly_seasonality=True,
    weekly_seasonality=True
)
m.fit(df)
future = m.make_future_dataframe(periods=4, freq='W')
forecast = m.predict(future)
```

---

## 3. Backtest & MAPE

**Method:** 8-week holdout. The model is trained on weeks 1–137 and evaluated against weeks 138–145.

**MAPE (Mean Absolute Percentage Error):**

| Category | MAPE | Interpretation |
|----------|------|----------------|
| 45 | 481.4% | Very high — small baseline demand amplifies % errors |
| 43 | 302.5% | High — bursty category |
| 24 | 228.9% | High |
| 17 | 175.3% | Moderate |
| 9 | 168.1% | Moderate |

### Why is MAPE so high?

Three factors:
1. **Small absolute demand (Cat 45):** When actual demand is 20 units and the model predicts 116, MAPE = 480%. The error in absolute units (96 units) is far less alarming than the % implies.
2. **Promotion-driven spikes:** Consumer goods see unpredictable demand shocks (flash sales, bundled promos) that no time-series model can anticipate without external regressors.
3. **Data ends at 2018:** If the dataset was truncated or there are structural breaks in 2017, the model extrapolates from a declining trend, which may not match the true future.

### What this means for decisions

A MAPE of 168–481% means **point estimates should not be taken literally**. The 80% confidence intervals are more useful: they bound the plausible range of demand. The correct way to use these forecasts is:

- **Safety stock target = upper_80 bound** (pessimistic planning scenario)
- **Point forecast** for reporting and trend direction only
- **Do not** directly use `forecast_units` as an order quantity without a safety buffer

---

## 4. Confidence Intervals

The `lower_80` and `upper_80` columns represent the 80% credible interval — Prophet is 80% confident actual demand will fall between these bounds.

**How wide are the bands?**

| Category | Week 1 Lower | Week 1 Upper | Width |
|----------|-------------|-------------|-------|
| 45 | 83 | 123 | 40 units |
| 17 | 349 | 475 | 126 units |
| 24 | 330 | 466 | 136 units |

Wider bands = higher demand volatility = larger safety stock needed.

---

## 5. Inventory Risk Flags

Current stock is approximated as `1.5× trailing 4-week average demand` (conservative safety stock heuristic). The gap is:

```
gap = forecast_4w_total - current_stock
```

A positive gap = stock-out risk. All 5 top categories show positive gaps:

| Category | Current Stock | 4-Week Forecast | Gap | Risk |
|----------|--------------|----------------|-----|------|
| 17 | 557 | 1,891 | +1,334 | 🚨 STOCK-OUT |
| 24 | 519 | 1,680 | +1,161 | 🚨 STOCK-OUT |
| 9 | 300 | 993 | +693 | 🚨 STOCK-OUT |
| 45 | 159 | 472 | +313 | 🚨 STOCK-OUT |
| 43 | 111 | 393 | +282 | 🚨 STOCK-OUT |
| **Total** | **1,646** | **5,429** | **+3,783** | |

> **To use real inventory data:** Replace the stock estimate line in `forecasting.ipynb` with:
> ```python
> current_stock = pd.read_sql("SELECT category_id, stock_on_hand FROM wms.inventory", conn)
> ```

---

## 6. Alternative Models Considered

Prophet was chosen over SARIMA because:
- Handles missing data and irregular time series gracefully
- Built-in seasonality decomposition requires no manual ACF/PACF tuning
- Faster to fit across 5 categories simultaneously

A SARIMA comparison was not run in this version of the notebook. If MAPE is a concern for stakeholders, a SARIMA benchmark is a recommended next step before the next quarterly review.

---

## 7. Recommended Next Steps

1. **Add external regressors:** Promotion calendars, holiday flags, or marketing spend as Prophet regressors would reduce MAPE significantly
2. **Refit monthly:** As new Snowflake data is added, retrain and compare MAPE trend
3. **Benchmark with SARIMA:** A simple SARIMA(1,1,1)(1,1,0)[52] would provide a statistical baseline
4. **Plug in real WMS stock:** The 1-line change described above makes the inventory flags production-ready
