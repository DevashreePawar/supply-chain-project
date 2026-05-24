# Quickstart — Get to a Running Pipeline in 90 Minutes

Run these in order. Check off as you go.

## Manual prep (you, ~30 min)

- [ ] Sign up for **Kaggle** → download "DataCo Smart Supply Chain Dataset"
  https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
- [ ] Place `DataCoSupplyChainDataset.csv` into `data/`
- [ ] Sign up for **Snowflake free trial** → https://signup.snowflake.com/
  (Cloud: AWS, any US region. Note: account locator, username, password.)
- [ ] Sign up for **Tableau Public** → https://public.tableau.com/en-us/s/download
  Download Tableau Public Desktop (free)

## Database load (~15 min)

- [ ] Open Snowflake UI → Worksheets → paste `sql/00_load_data.sql` → Run
- [ ] In Snowflake: navigate to `SUPPLY_CHAIN.RAW.DATACO_ORDERS` → Load Data wizard → upload CSV (encoding: Latin-1, skip header: 1)
- [ ] Run the count query at the bottom of `00_load_data.sql` — expect ~180,519 rows

## Staging (~10 min)

- [ ] Run `sql/staging/stg_orders.sql`
- [ ] Run `sql/staging/stg_products.sql`
- [ ] Run `sql/staging/stg_customers.sql`
- [ ] Run the sanity check queries at the bottom of each — confirm reasonable numbers

## Marts (~15 min)

- [ ] Run `sql/marts/dim_date.sql`
- [ ] Run `sql/marts/dim_product.sql`
- [ ] Run `sql/marts/dim_customer.sql`
- [ ] Run `sql/marts/fct_orders.sql`
- [ ] Run `sql/marts/agg_weekly_orders.sql`
- [ ] Run `sql/marts/agg_shipping_scorecard.sql`

You now have a complete star schema. The rest of the weekend is forecasting + dashboard + memo.

## Analysis sample (~10 min, optional smoke test)

- [ ] Run `sql/analysis/01_on_time_delivery_trend.sql` — confirm results look sensible
- [ ] Run `sql/analysis/03_shipping_mode_performance.sql` — confirm Standard Class has high late rate

## Forecasting (Sunday morning)

- [ ] Export `MARTS.AGG_WEEKLY_ORDERS` to CSV → place in `data/agg_weekly_orders.csv`
- [ ] `pip install pandas numpy matplotlib prophet statsmodels`
- [ ] Open `notebooks/forecasting.ipynb` → Run All
- [ ] Confirm three CSVs land in `data/`: forecast_4w, inventory_health, model_accuracy

## Tableau (Sunday afternoon)

- [ ] Open Tableau Public Desktop
- [ ] Connect to Snowflake (or import the CSVs)
- [ ] Build 4 sheets matching `tableau/wireframe.md`
- [ ] Compose into a single dashboard
- [ ] File → Save to Tableau Public As…
- [ ] Copy the published URL

## Memo (Sunday afternoon, last hour)

- [ ] Open `memo/stakeholder_memo_template.md`
- [ ] Fill in the <X> placeholders with your actual numbers from the analytical queries
- [ ] Convert to PDF (any markdown-to-PDF tool; see `memo/README.md` for pandoc command)
- [ ] Save final PDF as `memo/stakeholder_memo.pdf` (overwrite the existing placeholder)

## Ship

- [ ] Push to GitHub: `supply-chain-analytics-dashboard`
- [ ] In repo README: add the Tableau Public link as a clickable badge
- [ ] Add the project + bullets to your data-analyst-version resume

Done.
