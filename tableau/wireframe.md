# Tableau Dashboard Wireframe — 4 pages

All 4 pages share a left filter pane: Date Range, Region, Customer Segment, Shipping Mode.

Color palette: navy + amber accent + red/green for status. Avoid the default blue-orange Tableau palette — recruiters see it 100 times a day.

Connect to data sources (in Tableau Desktop or Tableau Public):
- Snowflake live connection → `MARTS.FCT_ORDERS`, `MARTS.AGG_WEEKLY_ORDERS`, `MARTS.AGG_SHIPPING_SCORECARD`
- Or CSV exports of the same tables
- Plus `data/forecast_4w.csv`, `data/inventory_health.csv`, `data/model_accuracy.csv`

---

## Page 1 — Operations Overview (the page the VP looks at first)

```
┌────────────────────────────────────────────────────────────────────┐
│  SUPPLY CHAIN | Operations Overview      Last refresh: <date>      │
├────────────────────────────────────────────────────────────────────┤
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │
│ │ Orders    │ │ Revenue   │ │ On-Time % │ │ Avg Delay │           │
│ │  68,234   │ │ $34.2M    │ │   47.8%   │ │   0.4 d   │           │
│ │  ↑ 4% YoY │ │  ↑ 7% YoY │ │  ↓ 2 pts  │ │  flat     │           │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘           │
├────────────────────────────────────────────────────────────────────┤
│ Weekly On-Time Delivery %    (target line at 95%)                  │
│                                                                    │
│        ─── actual    ── 4-week moving avg    ╌╌╌ target            │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Late Rate by Region (map)        │   Top 10 Late Combos (bar)     │
│                                   │   shipping_mode + region       │
└────────────────────────────────────────────────────────────────────┘
```

Source tables: `fct_orders` (for KPIs), `analysis/01_on_time_delivery_trend.sql` (for line chart), `agg_shipping_scorecard` (for map + bar).

---

## Page 2 — Shipping & Mode Performance

```
┌────────────────────────────────────────────────────────────────────┐
│  Shipping Modes — On-Time % vs Volume                              │
│  Scatter: x = orders, y = on-time %, size = revenue, color = late% │
├────────────────────────────────────────────────────────────────────┤
│  Shipping Mode Table                                               │
│  ┌─────────────────┬───────┬────────┬─────────┬──────────────┐    │
│  │ Mode            │ Orders│ On-Time│ Avg Delay│ Goodwill Cost│    │
│  ├─────────────────┼───────┼────────┼─────────┼──────────────┤    │
│  │ Standard Class  │  ...  │  ...   │  ...    │  ...         │    │
│  │ Second Class    │  ...  │  ...   │  ...    │  ...         │    │
│  │ First Class     │  ...  │  ...   │  ...    │  ...         │    │
│  │ Same Day        │  ...  │  ...   │  ...    │  ...         │    │
│  └─────────────────┴───────┴────────┴─────────┴──────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

Source: `analysis/03_shipping_mode_performance.sql`.

---

## Page 3 — Inventory Health

```
┌────────────────────────────────────────────────────────────────────┐
│  Inventory Status — Top 5 Categories                               │
│                                                                    │
│  STOCK-OUT RISK 🔴                  OVERSTOCK RISK 🟡              │
│  ┌──────────────────┐               ┌──────────────────┐           │
│  │ Category A: 1.2k │               │ Category D: 4.1k │           │
│  │ stock=800        │               │ stock=900        │           │
│  └──────────────────┘               └──────────────────┘           │
├────────────────────────────────────────────────────────────────────┤
│  Days-of-Cover by Category (bar, sorted asc — red bars first)      │
│  current_stock / avg_daily_demand                                  │
├────────────────────────────────────────────────────────────────────┤
│  Profit by Category (treemap, color = margin %)                    │
└────────────────────────────────────────────────────────────────────┘
```

Source: `data/inventory_health.csv` (from notebook) + `analysis/02_top_categories_revenue.sql`.

---

## Page 4 — Demand Forecast

```
┌────────────────────────────────────────────────────────────────────┐
│  4-Week Demand Forecast — Top 5 Categories                         │
│                                                                    │
│  Line chart per category: historical (solid) + forecast (dashed)   │
│  with 80% CI band                                                  │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Model Accuracy Table                                              │
│  ┌─────────────┬──────────────┬─────────────┬─────────┐            │
│  │ Category    │ Prophet MAPE │ SARIMA MAPE │ Winner  │            │
│  ├─────────────┼──────────────┼─────────────┼─────────┤            │
│  │ ...         │     12.3%    │    16.8%    │ Prophet │            │
│  └─────────────┴──────────────┴─────────────┴─────────┘            │
└────────────────────────────────────────────────────────────────────┘
```

Source: `data/forecast_4w.csv` + `data/model_accuracy.csv`.

---

## How to publish (the resume-link payoff)

1. Tableau Desktop → File → Save to Tableau Public As…
2. Sign in / create free Tableau Public account
3. The published URL goes on your resume as a clickable link: `https://public.tableau.com/app/profile/devashree/viz/SupplyChainOps`
4. Add the same link as a badge in the GitHub README

Recruiters who see "Tableau dashboard published" on a resume but cannot click anything always assume the candidate cannot actually produce one. A live link removes that doubt instantly.
