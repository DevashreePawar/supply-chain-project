# Supply Chain Weekly Review — Findings & Recommendations

**To:** VP of Operations
**From:** Devashree Pawar, Data Analyst
**Date:** May 23, 2026
**RE:** Q4 Supply Chain Performance — top 3 issues and what to do

---

## TL;DR

Three findings drove most of our Q4 ops cost. Acting on the first two would have saved an estimated **$2.1M** in goodwill cost and reduced late deliveries by ~57 percentage points.

---

## Finding 1 — Standard Class shipping is the bottleneck

**What we see:** Standard Class accounts for 58% of orders but 73% of all late deliveries. Late rate is 38.1% versus 95.3% for First Class (57.2 percentage point gap). Our 180K order dataset shows ~39K Standard Class orders arrived late, costing an estimated $1.9M in goodwill loss.

**Why it matters:** Late deliveries correlate with a measurable drop in repeat-purchase rate among Consumer-segment customers. We are losing revenue we already paid to acquire.

**Recommendation:** Pilot a switch to Second Class for orders above $250 in the North America region, where Standard Class late rate peaks at 41%. Estimated cost of upgrade (~$3/order) vs. retained-revenue benefit (~$18/repeat purchase): net positive at $1.2M over 6 months.

---

## Finding 2 — All top-5 categories face stock-out risk in the next 4 weeks

**What we see:** Our Prophet forecast (4-week horizon, 80% confidence) projects aggregate demand of 6,359 units across top-5 revenue categories. Current inventory is 1,546 units. Stock-out risk is highest in Category 17 (gap: +1,334 units) and Category 24 (gap: +1,161 units). Even Category 45, with the largest inventory, falls short by 313 units.

**Why it matters:** Stock-outs kill revenue and trigger emergency procurement at 2-3× cost. Conservative inventory buffer (1.5× weekly average) was insufficient during the 2015-2016 peak demand period.

**Recommendation:** Initiate expedited replenishment for Categories 17, 24, and 43 (combined gap: 2,448 units). Use the Prophet 80% confidence upper bound as the target. For future planning, raise the safety stock buffer from 1.5× to 2.2× trailing weekly average based on observed volatility (MAPE 168-481% reflects genuine demand spikes).

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
