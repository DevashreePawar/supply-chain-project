# SQL Pipeline — Execution Guide

This folder contains the full SQL pipeline: raw data load → staging → star schema → analytical queries.

---

## Folder Structure

```
sql/
├── 00_load_data.sql            # Step 0: Create database/schemas + load raw CSV
├── staging/
│   ├── stg_orders.sql          # Step 1a: Clean order rows, cast dates, derive flags
│   ├── stg_products.sql        # Step 1b: Deduplicate product attributes
│   └── stg_customers.sql       # Step 1c: Deduplicate customer attributes (PII excluded)
├── marts/
│   ├── dim_date.sql            # Step 2a: Date dimension (1,500 days)
│   ├── dim_product.sql         # Step 2b: Product dimension (dedup via ROW_NUMBER)
│   ├── dim_customer.sql        # Step 2c: Customer dimension + cohort dates
│   ├── fct_orders.sql          # Step 2d: Fact table (180.5K order-item rows)
│   ├── agg_weekly_orders.sql   # Step 2e: Weekly aggregates by category (notebook input)
│   └── agg_shipping_scorecard.sql  # Step 2f: Shipping mode × region scorecard
└── analysis/
    ├── 01_on_time_delivery_trend.sql
    ├── 02_top_categories_revenue.sql
    ├── 03_shipping_mode_performance.sql
    ├── 04_customer_segment_profitability.sql
    ├── 05_regional_performance.sql
    └── 06_cohort_repeat_purchase.sql
```

---

## Execution Order

Run files **in this exact order**. Each step depends on the previous.

### Step 0 — Load raw data

```sql
-- Run in Snowflake Worksheets
-- File: sql/00_load_data.sql
```

- Creates `SUPPLY_CHAIN` database with three schemas: `RAW`, `STAGING`, `MARTS`
- Creates `RAW.DATACO_ORDERS` (52 columns, all VARCHAR/FLOAT/INTEGER)
- **Load the CSV via Snowflake UI:** Right-click the table → Load Data → select `data/DataCoSupplyChainDataset.csv`
  - Encoding: `latin1`
  - Skip header: `1`
  - Field delimiter: `,`
  - Enclosed by: `"`

**Expected:** `SELECT COUNT(*) FROM RAW.DATACO_ORDERS;` → **180,519 rows**

---

### Step 1 — Staging views (run in any order)

```sql
-- sql/staging/stg_orders.sql
-- sql/staging/stg_products.sql
-- sql/staging/stg_customers.sql
```

These are `CREATE OR REPLACE VIEW` statements — they run instantly and don't materialise data.

**Sanity checks (run the SELECT at the bottom of each file):**

| File | Key check |
|------|-----------|
| stg_orders | ~180,519 rows; `pct_late` ≈ 55% |
| stg_products | ~118–200 distinct products |
| stg_customers | ~20,600 distinct customers |

> **Note on late flags:** `stg_orders` derives two delivery flags using **different logic**:
> - `is_late_flag` → based on `DELIVERY_STATUS = 'Late delivery'` (the status string)
> - `is_on_time_flag` → based on `DAYS_FOR_SHIPPING_REAL <= DAYS_FOR_SHIPMENT_SCHEDULED` (day math)
>
> These will disagree for some rows where the status string and the day delta are inconsistent.
> Use `is_late_flag` for memo/dashboard numbers (matches the DataCo dataset's own classification).
> Use `is_on_time_flag` for time-math-based analysis. Do not mix them in the same query.

---

### Step 2 — Marts (run in order: dimensions first, then fact, then aggregates)

```sql
-- 2a: sql/marts/dim_date.sql
-- 2b: sql/marts/dim_product.sql
-- 2c: sql/marts/dim_customer.sql
-- 2d: sql/marts/fct_orders.sql        ← depends on staging views
-- 2e: sql/marts/agg_weekly_orders.sql ← depends on fct_orders + dim_product
-- 2f: sql/marts/agg_shipping_scorecard.sql ← depends on fct_orders
```

**Expected row counts:**

| Table | Expected |
|-------|----------|
| `MARTS.DIM_DATE` | 1,500 |
| `MARTS.DIM_PRODUCT` | ~118 |
| `MARTS.DIM_CUSTOMER` | ~20,600 |
| `MARTS.FCT_ORDERS` | 180,519 |
| `MARTS.AGG_WEEKLY_ORDERS` | ~3,541 |
| `MARTS.AGG_SHIPPING_SCORECARD` | ~92 |

---

### Step 3 — Analytical queries (optional; run individually as needed)

These are standalone `SELECT` queries — they don't create tables. Run them to explore findings or export results.

| File | Business question | Key technique |
|------|-------------------|---------------|
| `01_on_time_delivery_trend.sql` | Is delivery improving over time? | 4-week moving avg (`ROWS BETWEEN`) |
| `02_top_categories_revenue.sql` | Which categories drive revenue? | `RANK()`, YoY pivot |
| `03_shipping_mode_performance.sql` | Which modes have systemic late problems? | Conditional aggregation, goodwill cost |
| `04_customer_segment_profitability.sql` | Which segments are most profitable? | Pareto / cumulative window |
| `05_regional_performance.sql` | Where are ops problems geographically? | Dual `RANK()`, priority flag |
| `06_cohort_repeat_purchase.sql` | Are customers sticking around? | Cohort retention, `DATEDIFF` |

---

## Snowflake-Specific Syntax Notes

- `QUALIFY` (used in `dim_product.sql`, `dim_customer.sql`) — Snowflake-native way to filter on window function results. On Postgres, wrap in a subquery: `WHERE rn = 1`.
- `TABLE(GENERATOR(ROWCOUNT => N))` (used in `dim_date.sql`) — Snowflake row generator for date spines. On Postgres, use a recursive CTE instead.
- `TRY_TO_TIMESTAMP` — Snowflake's null-safe timestamp cast. On Postgres, use `TO_TIMESTAMP` inside a `CASE WHEN` or `NULLIF`.
- `DATEDIFF('quarter', ...)` — Snowflake syntax. Postgres equivalent: `EXTRACT(quarter FROM ...) - EXTRACT(quarter FROM ...)` (adjusted for year).
