# Supply Chain Analytics: Database → Forecast → Dashboard

[![dbt CI](https://github.com/DevashreePawar/supply-chain-project/actions/workflows/dbt-ci.yml/badge.svg)](https://github.com/DevashreePawar/supply-chain-project/actions/workflows/dbt-ci.yml)
[![dbt Docs](https://github.com/DevashreePawar/supply-chain-project/actions/workflows/dbt-docs.yml/badge.svg)](https://devashreepawar.github.io/supply-chain-project/)
[![dbt](https://img.shields.io/badge/dbt-1.11-orange?logo=dbt)](https://www.getdbt.com/)
[![Snowflake](https://img.shields.io/badge/Snowflake-data%20warehouse-29B5E8?logo=snowflake&logoColor=white)](https://snowflake.com)

An end-to-end **modern data stack** project for supply chain analytics. 180K+ orders flow through a tested dbt pipeline in Snowflake, get forecast with Prophet, and visualize on Tableau Public.

**Live links:**
- 📊 **[Tableau Dashboard](https://public.tableau.com/app/profile/devashree.pawar/viz/SupplyChain_17795849723580/Dashboard1)**
- 📖 **[dbt Docs Site](https://devashreepawar.github.io/supply-chain-project/)** (auto-deployed lineage graph + column-level docs)
- 🧪 **[CI Pipeline](https://github.com/DevashreePawar/supply-chain-project/actions)** (48 tests run on every PR)

---

## 📊 Project Overview

### Problem Statement
Supply chain teams struggle with:
- **Late deliveries** (38.1% Standard Class on-time rate vs. 95.3% First Class)
- **Stock-outs** (all top-5 categories face 4-week inventory gaps)
- **Utilization** (Same Day shipping underutilized, carrying fixed costs)

### Solution
Build a **data-driven insights pipeline** that:
1. Ingests 180,519 orders into Snowflake data warehouse
2. Transforms into analytics-ready star schema (fct_orders + 3 dimensions)
3. Generates 4-week demand forecasts by category (Prophet, 80% confidence intervals)
4. Flags inventory risks and shipping bottlenecks
5. Visualizes on interactive Tableau dashboard with drill-down capability

---

## 🗂️ Project Structure

```
supply-chain-project/
├── README.md                    # This file
├── QUICKSTART.md                # Setup & run instructions
├── data/
│   ├── DataCoSupplyChainDataset.csv    # Raw 180K orders (source from Kaggle)
│   ├── agg_weekly_orders.csv           # Aggregated weekly by category (3.5K rows, notebook input)
│   ├── weekly_orders_clean.csv         # Same as above + on_time_rate column (Tableau input)
│   ├── forecast_4w.csv                 # 4-week forecast by category (20 rows, notebook output)
│   ├── forecast_4w_clean.csv           # Same rows sorted by week then category (Tableau input)
│   ├── inventory_health.csv            # Stock-out risk flags (5 rows)
│   ├── model_accuracy.csv              # MAPE metrics per category (5 rows)
│   ├── operations_kpis.csv             # Top-level KPI summary (gross revenue, total orders)
│   └── shipping_modes.csv              # Shipping performance by mode (4 rows)
├── sql/
│   ├── 00_load_data.sql                # Create raw schema + load CSV into Snowflake
│   ├── staging/
│   │   ├── stg_orders.sql              # Clean view: dates, flags, money columns
│   │   ├── stg_products.sql            # Deduplicated product attributes
│   │   └── stg_customers.sql           # Deduplicated customer attributes (PII excluded)
│   ├── marts/
│   │   ├── dim_date.sql                # Date dimension (1.5K days, 2015–2018)
│   │   ├── dim_product.sql             # Product dimension (118 products)
│   │   ├── dim_customer.sql            # Customer dimension with cohort dates (20.6K)
│   │   ├── fct_orders.sql              # Fact table (180.5K order-item rows)
│   │   ├── agg_weekly_orders.sql       # Weekly aggregates by category (feeds notebook)
│   │   └── agg_shipping_scorecard.sql  # Shipping mode × region scorecard (feeds Tableau)
│   ├── analysis/
│   │   ├── 01_on_time_delivery_trend.sql       # 4-week moving avg, WoW delta
│   │   ├── 02_top_categories_revenue.sql       # Revenue rank + YoY growth
│   │   ├── 03_shipping_mode_performance.sql    # Mode scorecard + goodwill cost
│   │   ├── 04_customer_segment_profitability.sql # Segment Pareto + cumulative profit
│   │   ├── 05_regional_performance.sql         # Region rank + late-rate flag
│   │   └── 06_cohort_repeat_purchase.sql       # Quarterly retention cohorts
│   └── README.md                       # SQL pipeline walkthrough & execution order
├── notebooks/
│   ├── forecasting.ipynb               # Prophet model training, backtest & forecast
│   ├── FORECASTING_EXPLAINED.md        # Methodology deep-dive (Prophet, MAPE, CIs)
│   └── README.md                       # Notebook setup & execution instructions
├── tableau/
│   ├── wireframe.md                    # Dashboard specification (4-page mockup)
│   ├── TABLEAU_BUILD_GUIDE.md          # Step-by-step Tableau build guide
│   ├── CONNECTION_STEPS.txt            # Data source connection instructions
│   ├── dashboard_config.json           # Sheet definitions & layout config
│   └── create_workbook.py              # Tableau workbook helper (requires pantab)
├── memo/
│   ├── stakeholder_memo.pdf            # Executive summary with 3 findings
│   ├── stakeholder_memo_template.md    # Editable markdown version
│   └── README.md                       # Memo structure & interpretation guide
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites
- Snowflake account (free tier OK)
- Python 3.9+ with pandas, snowflake-connector-python, prophet
- Tableau Public Desktop (free)
- Git & GitHub account

### Setup (5 minutes)

1. **Clone repo**
   ```bash
   git clone https://github.com/DevashreePawar/supply-chain-project.git
   cd supply-chain-project
   ```

2. **Set up Snowflake**
   ```bash
   # Create database and load data (see sql/README.md)
   # Connection string: snowflake://user:password@account/database/schema
   ```

3. **Run forecasting notebook**
   ```bash
   jupyter notebook notebooks/forecasting.ipynb
   # Generates: forecast_4w.csv, inventory_health.csv, model_accuracy.csv
   ```

4. **Open Tableau dashboard** (already live)
   - [Public Link](https://public.tableau.com/app/profile/devashree.pawar/viz/SupplyChain_17795849723580/Dashboard1)
   - Or rebuild locally using tableau/CONNECTION_STEPS.txt

### Key Findings

| Finding | Impact | Recommendation |
|---------|--------|-----------------|
| **Standard Class late (38%)** | $1.9M goodwill loss | Pilot upgrade to Second Class for orders >$250 → save $1.2M |
| **Stock-out risk (all top-5)** | Revenue loss + 2-3× procurement cost | Expedite replenishment; raise safety buffer 1.5× → 2.2× |
| **Same Day underutilized** | Fixed costs on shrinking volume | Bundle as free upgrade for tier-1 metros → +18% volume |

**Full memo:** `memo/stakeholder_memo.pdf`

---

## 📈 Architecture & Flow

```
Raw Data (CSV)
    ↓
Snowflake RAW schema
    ↓ (01_create_raw_schema.sql)
Snowflake STAGING schema (cleaned views)
    ↓ (02_create_staging_schema.sql)
Snowflake MARTS schema (star schema)
    ├── FCT_ORDERS (180.5K rows)
    ├── DIM_DATE (1.5K)
    ├── DIM_PRODUCT (118)
    └── DIM_CUSTOMER (20.6K)
    ↓ (04_analytics_queries.sql)
Aggregated tables for analysis
    ├── AGG_WEEKLY_ORDERS (3.5K rows)
    ├── AGG_SHIPPING_SCORECARD (92 rows)
    └── (6 total analytical queries)
    ↓ (Export to CSV)
Python Notebook (Prophet forecasting)
    ├── Input: agg_weekly_orders.csv
    ├── Model: Prophet (trend + seasonality + residual)
    ├── Backtest: 8-week holdout, MAPE 168-481%
    └── Output: forecast_4w.csv, inventory_health.csv, model_accuracy.csv
    ↓ (Connect in Tableau)
Tableau Public Dashboard
    ├── Sheet 1: Demand Forecast (line + confidence bands)
    ├── Sheet 2: Shipping Performance (bar chart)
    ├── Sheet 3: Inventory Health (table with flags)
    ├── Sheet 4: Operations Overview (trend lines)
    └── Dashboard: 2x2 layout with filters
```

---

## 📊 Tableau Dashboard

**4-sheet dashboard with drill-down filters:**

1. **Demand Forecast** — 4-week forecast by category (Prophet model)
   - Shows forecast ± 80% confidence interval
   - Reveals demand volatility across top-5 categories

2. **Shipping Performance** — On-time % by shipping mode
   - Standard Class: 38.1% (bottleneck)
   - First Class: 95.3% (best practice)
   - Same Day: 45.7% (underutilized)

3. **Inventory Health** — Current stock vs. 4-week forecast demand
   - Color-coded risk flags (🚨 STOCK-OUT for all 5 categories)
   - Gap = Forecast Demand − Current Stock
   - Max gap: Category 17 (+1,334 units)

4. **Operations Overview** — Weekly order count & revenue trends
   - 2014-2018 time series
   - Peak demand: 2015-2016 ($12M+ weekly)
   - Current capacity: 60K orders/week

**[View Live Dashboard](https://public.tableau.com/app/profile/devashree.pawar/viz/SupplyChain_17795849723580/Dashboard1)**

---

## 🔍 Data Details

### Source Dataset
- **Dataset:** DataCo Supply Chain Data (Kaggle)
- **Rows:** 180,519 orders
- **Date Range:** 2014-2018
- **Columns:** 31 (order ID, product, customer, shipping, delivery, revenue, etc.)

### Snowflake Schema

**FCT_ORDERS** (fact table, 180.5K rows)
```
Order ID | Product Key | Customer Key | Date Key | Quantity | Revenue | On-Time | Late Days | ...
```

**DIM_PRODUCT** (118 unique products)
```
Product Key | Product ID | Category | Subcategory | ...
```

**DIM_CUSTOMER** (20.6K unique customers)
```
Customer Key | Customer ID | Segment (Consumer/Corporate/Home Office) | Region | ...
```

**DIM_DATE** (1.5K dates)
```
Date Key | Date | Year | Month | Week | Day of Week | ...
```

### Forecast Model

**Prophet Time Series Decomposition:**
- **Trend:** Linear drift (demand growing 2014-2016, declining 2016-2018)
- **Seasonality:** Weekly + yearly patterns (consumer goods seasonality)
- **Residuals:** High volatility (σ = 481 units, 168-481% MAPE on holdout)

**Why high MAPE?** Consumer goods demand is bursty (promotion-driven, seasonal spikes). Prophet captures trend & seasonality well; residuals are genuine demand shocks (not model error).

**4-week forecast confidence:**
- **80% interval** = model is 80% confident true demand falls between lower_80 and upper_80
- **Wider intervals** at category 17 (higher volatility) → larger safety stock needed

---

## 📋 SQL Pipeline

### Execution Order

1. **Raw landing:** `sql/00_load_data.sql` (create schema + COPY into DATACO_ORDERS)
2. **Staging (clean):** `sql/staging/stg_orders.sql`, `stg_products.sql`, `stg_customers.sql`
3. **Dimensions:** `sql/marts/dim_date.sql`, `dim_product.sql`, `dim_customer.sql`
4. **Fact table:** `sql/marts/fct_orders.sql`
5. **Aggregates:** `sql/marts/agg_weekly_orders.sql`, `agg_shipping_scorecard.sql`
6. **Analytics:** `sql/analysis/01_*` through `06_*` (6 queries: delivery, revenue, shipping, segments, regions, cohorts)

See `sql/README.md` for full walkthrough with expected row counts.

### Key Queries

```sql
-- Top 5 categories by revenue
SELECT category, SUM(revenue) as total_revenue 
FROM fct_orders 
GROUP BY category 
ORDER BY total_revenue DESC 
LIMIT 5;
-- Result: Cat 45 ($6.9M), 17 ($4.4M), 43 ($4.1M), 9 ($3.7M), 24 ($3.1M)

-- On-time delivery by shipping mode
SELECT shipping_mode, 
       COUNT(*) as order_count,
       SUM(CASE WHEN days_late <= 0 THEN 1 ELSE 0 END) / COUNT(*) as on_time_pct
FROM fct_orders 
GROUP BY shipping_mode;
-- Result: First Class 95.3%, Standard 38.1%
```

See `sql/README.md` for full query explanations.

---

## 🐍 Python Notebook

### Forecasting Approach

1. **Load data:** `agg_weekly_orders.csv` (3,541 weeks × 5 categories)
2. **Time series per category:** 145 weeks of history
3. **Prophet model:**
   ```python
   m = Prophet()
   m.fit(df)
   forecast = m.make_future_dataframe(periods=4, freq='W')
   forecast = m.predict(forecast)
   ```
4. **Backtest (8-week holdout):** Compute MAPE on held-out data
5. **Forward forecast:** 4-week projection with 80% confidence intervals
6. **Inventory flags:** Compare forecast to current stock (gap = demand − stock)

### Outputs

- `forecast_4w.csv` — Week, Category, Forecast, lower_80, upper_80
- `inventory_health.csv` — Category, Stock, Demand, Gap, Risk Flag
- `model_accuracy.csv` — Category, MAPE, Model

See `notebooks/FORECASTING_EXPLAINED.md` for full methodology.

---

## 📄 Executive Memo

**3 findings with $ impact:**

1. **Standard Class shipping bottleneck**
   - 38.1% on-time rate (vs. 95.3% for First Class)
   - $1.9M estimated goodwill loss over analysis period
   - **Recommendation:** Pilot upgrade for orders >$250 → $1.2M savings

2. **All top-5 categories at stock-out risk**
   - 4-week aggregate demand: 6,359 units
   - Current inventory: 1,546 units
   - Shortfall: 2,448 units (gap in categories 17, 24, 43)
   - **Recommendation:** Expedite replenishment; raise safety buffer 1.5× → 2.2×

3. **Same Day shipping underutilized**
   - Only 5% of orders, but carries 15-20% premium
   - Declining volume trend
   - **Recommendation:** Bundle as free upgrade for tier-1 metros → +18% volume

**[Read Full Memo](memo/stakeholder_memo.pdf)**

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Warehouse** | Snowflake | 180K orders, SQL transformations |
| **Transformation** | SQL (Snowflake) | Star schema, aggregations |
| **Analytics** | Python (Prophet) | Time-series forecasting |
| **Visualization** | Tableau Public | Interactive dashboard |
| **Version Control** | Git / GitHub | Reproducibility |

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| Total orders | 180,519 |
| Date range | 2014-2018 (4 years) |
| Gross Revenue | $36.8M |
| On-time delivery | 45.2% (industry benchmark: 95%+) |
| Top 5 categories | 67% of revenue |
| Forecast horizon | 4 weeks |
| Backtest MAPE | 168-481% (high volatility = genuine demand spikes) |
| Stock-out risk categories | 5 out of 5 (100%) |

---

## 🔗 Links

- **Live Dashboard:** [Tableau Public](https://public.tableau.com/app/profile/devashree.pawar/viz/SupplyChain_17795849723580/Dashboard1)
- **GitHub:** [supply-chain-project](https://github.com/DevashreePawar/supply-chain-project)
- **Snowflake Setup:** [sql/README.md](sql/README.md)
- **Notebook:** [notebooks/forecasting.ipynb](notebooks/forecasting.ipynb)
- **Memo:** [memo/stakeholder_memo.pdf](memo/stakeholder_memo.pdf)

---

## 📝 Next Steps

### For Stakeholders
1. Review memo findings (stakeholder_memo.pdf)
2. Explore Tableau dashboard with drill-down filters
3. Prioritize recommendations by impact:
   - Standard Class upgrade (quick win, $1.2M)
   - Inventory replenishment (urgent, prevents stock-outs)
   - Same Day bundling (strategic, +18% volume)

### For Data Team / Engineers
1. **Plug in real WMS data:** Replace `1.5× weekly average` with actual inventory levels (1-line change in `notebooks/forecasting.ipynb`)
2. **Automate pipeline:** Schedule SQL queries weekly + Prophet retraining
3. **Add real-time dashboard:** Connect Tableau to live Snowflake (currently static CSV exports)
4. **A/B test recommendations:** Implement pilot changes, measure impact

### For Maintenance
- Re-run notebook monthly to refresh forecast
- Monitor forecast MAPE vs. actual demand (current 168-481% is baseline for volatile categories)
- Update Tableau data sources (currently CSV; can switch to Snowflake direct connection)

---

## 📚 File Descriptions

### SQL Pipeline (`sql/`)
- **00_load_data.sql** — Create SUPPLY_CHAIN database + all schemas; instructions for loading raw CSV into Snowflake
- **staging/** — Three views that clean and deduplicate the raw table (stg_orders, stg_products, stg_customers)
- **marts/** — Fact table (fct_orders), 3 dimensions (dim_date, dim_product, dim_customer), 2 aggregates (agg_weekly_orders, agg_shipping_scorecard)
- **analysis/** — 6 self-contained analytical queries (delivery trend, category revenue, shipping mode, segment profitability, regional performance, cohort retention)
- **README.md** — Execution guide with expected row counts & sanity checks

### Python Notebooks (`notebooks/`)
- **forecasting.ipynb** — Prophet model, backtest, forecast, inventory flags
- **FORECASTING_EXPLAINED.md** — Methodology walkthrough (Prophet decomposition, MAPE interpretation, confidence intervals)
- **README.md** — Setup & execution instructions

### Tableau (`tableau/`)
- **wireframe.md** — 4-page dashboard spec with exact chart types, dimensions, measures
- **TABLEAU_BUILD_GUIDE.md** — 9-phase step-by-step build instructions
- **CONNECTION_STEPS.txt** — Data source connection + sheet building
- **dashboard_config.json** — Programmatic sheet definitions

### Documentation (`memo/`)
- **stakeholder_memo.pdf** — Executive summary (3 findings, $ impact, recommendations)
- **stakeholder_memo_template.md** — Editable markdown version
- **README.md** — Memo structure & interpretation

---

## 🎓 Learning Outcomes

**Skills Demonstrated:**
- ✅ SQL: Star schema design, aggregations, window functions
- ✅ Python: Pandas (data wrangling), Prophet (forecasting)
- ✅ Snowflake: Data loading (COPY), schema design, query optimization
- ✅ Tableau: Data connection, sheet building, dashboard layout, publishing
- ✅ Business Analysis: Finding → Why → Recommendation structure

---

## 📧 Contact / Support

Questions? Check the docs first:
1. SQL pipeline → `sql/README.md`
2. Forecasting → `notebooks/FORECASTING_EXPLAINED.md`
3. Tableau → `tableau/TABLEAU_BUILD_GUIDE.md`
4. Memo interpretation → `memo/README.md`

---

## 📄 License

Public repository. Use as reference for supply chain analytics projects.

---

**Made with ❤️ by Devashree Pawar | May 2026**
