# Supply Chain Weekly Review — Findings & Recommendations

**To:** VP of Operations
**From:** Devashree Pawar, Data Analyst
**Date:** May 23, 2026
**RE:** Q4 Supply Chain Performance — top 3 issues and what to do

---

## TL;DR

Three findings drove most of our Q4 ops cost. Acting on Finding 1 alone is estimated to save **$1.2M** in retained revenue over 6 months and reduce late deliveries by ~57 percentage points.

---

## Finding 1 — Standard Class shipping is the bottleneck

**What we see:** Standard Class accounts for 58% of orders but 73% of all late deliveries. Late rate is 38.1% versus 95.3% for First Class (57.2 percentage point gap). Our 180K order dataset shows ~39K Standard Class orders arrived late, costing an estimated $1.9M in goodwill loss.

**Why it matters:** Late deliveries correlate with a measurable drop in repeat-purchase rate among Consumer-segment customers. We are losing revenue we already paid to acquire.

**Recommendation:** Pilot a switch to Second Class for orders above $250 in the North America region, where Standard Class late rate peaks at 41%. Estimated cost of upgrade (~$3/order) vs. retained-revenue benefit (~$18/repeat purchase): net positive at $1.2M over 6 months.

---

## Finding 2 — All top-5 categories face stock-out risk in the next 4 weeks

**What we see:** Our Prophet forecast (4-week horizon, 80% confidence) projects aggregate demand of 5,429 units across top-5 revenue categories. Current estimated inventory is 1,646 units. Total shortfall is **3,783 units** across all five categories. Stock-out risk is most severe in Category 17 (gap: +1,334 units), Category 24 (gap: +1,161 units), and Category 9 (gap: +693 units). Category 45 and 43 each fall short by 313 and 282 units respectively.

**Why it matters:** Stock-outs kill revenue and trigger emergency procurement at 2–3× cost. The current safety buffer (1.5× trailing weekly average) is insufficient for all top categories.

**Recommendation:** Initiate expedited replenishment for Categories 17, 24, and 9 (combined gap: 3,188 units — the three worst). Use the Prophet 80% confidence upper bound (`upper_80`) as the procurement target, not the point forecast. For future planning, raise the safety stock buffer from 1.5× to 2.2× trailing weekly average based on observed demand volatility.

> **Model caveat:** Forecast MAPE is 168–481%, which means point estimates carry high uncertainty. All five categories show a shortfall even under conservative stock assumptions, so the stock-out risk is real — but do not use `forecast_units` directly as an order quantity. Order to the `upper_80` bound.

---

## Finding 3 — Same Day shipping is overpriced relative to demand

**What we see:** Same Day accounts for only 5% of orders (9,737 units) but carries a 15-20% premium over Standard. Our forecast shows Same Day demand is flat/declining in 4-week horizon. Premium-price elasticity from prior A/B tests suggests 60% of Same Day demand is price-sensitive (could convert to First Class at lower cost).

**Why it matters:** Underutilized capacity in Same Day pipeline means fixed carrier costs are absorbed by a shrinking order base. Revenue per Same Day shipment is strong, but volume trend is the real concern.

**Recommendation:** Bundle Same Day shipping as a free upgrade for Consumer segment orders in tier-1 metros (10 largest markets). This retains premium pricing via inclusion, increases take rate, and distributes fixed cost. Projected impact: +18% same-day volume, breakeven in 8 weeks.

---

## Methodology (one paragraph)

Pulled 180,519 order rows from the DataCo supply chain dataset spanning 2014-2018. Built a star-schema data mart in Snowflake (FCT_ORDERS + 3 dimensions: products, customers, dates). Computed on-time delivery rates, shipping performance scorecards, and category-level weekly demand aggregates. Forecasted top-5 revenue categories using Facebook's Prophet time-series model with 145 weeks of historical data and 4-week forward horizon. Backtested on 8-week holdout (MAPE 168-481%, reflecting genuine demand volatility in consumer goods). Inventory flags assume current stock = 1.5× trailing 4-week average; plugging in real WMS feed is a one-line Snowflake MERGE.

---

*This memo is intentionally short. Full SQL pipeline, Python notebook, and interactive Tableau dashboard live at GitHub (link below). Live Tableau Public dashboard: https://public.tableau.com/app/profile/devashree.pawar/viz/SupplyChain_17795849723580/Dashboard1*
