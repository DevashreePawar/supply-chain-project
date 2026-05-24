# Forecasting Notebook — Setup & Execution

## What this notebook does

`forecasting.ipynb` runs the entire Python forecasting pipeline:

1. Loads `data/agg_weekly_orders.csv` (3,541 weekly rows × top-5 categories from Snowflake)
2. Fits a **Prophet time-series model** per category (145 weeks of history)
3. Backtests on an **8-week holdout** to compute MAPE
4. Projects demand **4 weeks forward** with 80% confidence intervals
5. Flags inventory risk by comparing forecast demand against current stock
6. Writes three output CSVs to `data/`

---

## Prerequisites

Python 3.9 or higher. Install dependencies:

```bash
pip install pandas numpy matplotlib prophet statsmodels
```

> Prophet requires `pystan` (or `cmdstanpy`) as a backend. If installation fails on Apple Silicon:
> ```bash
> pip install prophet --no-binary :all:
> ```
> Or use conda:
> ```bash
> conda install -c conda-forge prophet
> ```

---

## Input

| File | Source | Description |
|------|--------|-------------|
| `data/agg_weekly_orders.csv` | Exported from `MARTS.AGG_WEEKLY_ORDERS` | Weekly order counts + revenue by category |

**Column names the notebook expects:**
`order_week`, `category_id`, `order_count`, `unique_orders`, `total_quantity`, `total_gross_sales`, `total_net_sales`, `total_profit`, `avg_profit_ratio`

---

## Outputs

| File | Rows | Description |
|------|------|-------------|
| `data/forecast_4w.csv` | 20 (5 categories × 4 weeks) | Raw notebook output, sorted by category then week |
| `data/forecast_4w_clean.csv` | 20 | Same data sorted by week then category — Tableau-friendly format |
| `data/inventory_health.csv` | 5 | Category, current stock estimate, 4-week forecast demand, gap, risk flag |
| `data/model_accuracy.csv` | 5 | Category, Prophet MAPE, avg actual demand, avg forecast |

> **Inventory stock estimate:** Current stock is approximated as `1.5× trailing 4-week average demand` (a conservative safety stock heuristic). To use real inventory levels, replace this one line with a direct query against your WMS.

---

## How to run

```bash
# From the project root
jupyter notebook notebooks/forecasting.ipynb
```

Then: **Kernel → Restart & Run All**

Confirm three CSVs land in `data/` with the expected row counts above.

---

## Understanding the outputs

See [FORECASTING_EXPLAINED.md](FORECASTING_EXPLAINED.md) for a full walkthrough of:
- How Prophet decomposes trend + seasonality + residuals
- Why MAPE is 168–481% and what that means for decision-making
- How to interpret 80% confidence intervals
- How to plug in real inventory data
