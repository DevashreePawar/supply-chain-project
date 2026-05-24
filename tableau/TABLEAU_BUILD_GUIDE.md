# Tableau Build Guide — Step-by-Step

Build the 4-sheet dashboard in Tableau Public Desktop. Estimated time: 2–3 hours.

---

## Phase 1 — Connect to Data Sources

Open Tableau Public Desktop.

**Connect → Text File** → navigate to `data/` and add each CSV:

| CSV file | Used for |
|----------|----------|
| `weekly_orders_clean.csv` | Operations Overview sheet |
| `shipping_modes.csv` | Shipping Performance sheet |
| `inventory_health.csv` | Inventory Health sheet |
| `forecast_4w_clean.csv` | Demand Forecast sheet |

**For each CSV, set the correct data types:**

`forecast_4w_clean.csv`:
- `week` → Date
- `forecast_units`, `lower_80`, `upper_80` → Number (Decimal)
- `category_id` → String (it's a label, not a sum)

`weekly_orders_clean.csv`:
- `order_week` → Date
- `category_id` → String
- All other numeric columns → Number (Decimal)

---

## Phase 2 — Sheet 1: Operations Overview

**Source:** `weekly_orders_clean.csv`

1. **KPI tiles (4 BANs):** Create 4 text sheets (one per KPI), place at top:
   - Total Orders: `SUM([order_count])`
   - Total Revenue: `SUM([total_gross_sales])`
   - On-Time Rate: `AVG([on_time_rate])` formatted as %
   - Avg Delay Days: (calculated from raw data if available, or omit)

2. **Line chart — Weekly On-Time Rate:**
   - Columns: `order_week` (continuous)
   - Rows: `AVG([on_time_rate])`
   - Add reference line at 0.95 (95% target) — Right-click axis → Add Reference Line

3. **4-week moving average:** Create a calculated field:
   ```
   WINDOW_AVG(AVG([on_time_rate]), -3, 0)
   ```
   Add as a second line on the same chart.

---

## Phase 3 — Sheet 2: Shipping Performance

**Source:** `shipping_modes.csv`

1. **Bar chart — On-Time % by Shipping Mode:**
   - Columns: `[shipping_mode]`
   - Rows: `[on_time_percent]`
   - Sort: descending by `on_time_percent`
   - Color: Red if `on_time_percent < 70`, Green if ≥ 90, Amber otherwise
     ```
     IF [on_time_percent] < 70 THEN "Late"
     ELSEIF [on_time_percent] >= 90 THEN "On Track"
     ELSE "Watch"
     END
     ```

2. **Table below the chart:**
   - Rows: `[shipping_mode]`
   - Columns: `[order_count]`, `[on_time_percent]`, `[avg_delay_days]`, `[late_orders]`
   - Format `on_time_percent` as percentage with 1 decimal

---

## Phase 4 — Sheet 3: Inventory Health

**Source:** `inventory_health.csv`

1. **Summary table:**
   - Rows: `[category_id]`
   - Columns: `[current_stock]`, `[forecast_4w]`, `[gap]`, `[flag]`
   - Color `[gap]` red (all positive = stock-out risk)

2. **Calculated field — Days of Cover:**
   ```
   [current_stock] / ([forecast_4w] / 28)
   ```
   (forecast_4w is 4-week total; divide by 28 to get daily rate)

3. **Bar chart — Gap by Category:**
   - Columns: `[category_id]`
   - Rows: `[gap]`
   - Sort: descending
   - Color: Red for all (all are at risk)
   - Add reference line at 0

---

## Phase 5 — Sheet 4: Demand Forecast

**Source:** `forecast_4w_clean.csv`

1. **Line chart per category:**
   - Columns: `[week]` (continuous Date)
   - Rows: `[forecast_units]`
   - Color/Detail: `[category_id]`

2. **80% Confidence interval bands:**
   - Dual-axis: add `[lower_80]` and `[upper_80]` as a second axis
   - Right-click axis → Synchronize Axis
   - Change `lower_80`/`upper_80` marks to Area, reduce opacity to 20%
   - This creates the shaded confidence band behind the forecast line

3. **Model Accuracy table below chart:**
   - Source: `model_accuracy.csv` (add as a second data source)
   - Rows: `[category_id]`
   - Columns: `[mape]`, `[avg_actual]`, `[avg_forecast]`
   - Note: MAPE 168–481% reflects genuine demand volatility, not model failure

---

## Phase 6 — Build the Dashboard

1. New Dashboard sheet
2. Set size: **Fixed → 1200 × 800 px** (standard wide screen)
3. Layout: 2×2 grid

```
┌─────────────────────┬─────────────────────┐
│  Operations         │  Shipping           │
│  Overview           │  Performance        │
├─────────────────────┼─────────────────────┤
│  Inventory          │  Demand             │
│  Health             │  Forecast           │
└─────────────────────┴─────────────────────┘
```

4. Drag each sheet into its quadrant
5. Add a filter control: Drag `[category_id]` from any sheet → "Apply to worksheets → All using this data source"

---

## Phase 7 — Color Palette & Styling

Avoid the default Tableau blue-orange scheme. Use:

| Element | Color | Hex |
|---------|-------|-----|
| Primary lines / bars | Navy | `#003f5c` |
| Accent (alerts, targets) | Amber | `#ffa600` |
| Neutral backgrounds | Mid-grey | `#a5a5a5` |
| On-time / good | Green | `#2ca02c` |
| Late / risk | Red | `#d62728` |

Set in: Format → Workbook → Default Colors → Custom

---

## Phase 8 — Tooltips

Customize tooltips on each sheet to show human-readable context:

**Shipping Performance tooltip:**
```
Mode: <[shipping_mode]>
On-Time: <[on_time_percent]>%
Late Orders: <[late_orders]>
```

**Inventory Health tooltip:**
```
Category <[category_id]>
Stock: <[current_stock]> units
Forecast demand (4 weeks): <[forecast_4w]> units
Gap: <[gap]> units — STOCK-OUT RISK
```

---

## Phase 9 — Publish to Tableau Public

1. **File → Save to Tableau Public As…**
2. Sign in with your Tableau Public account
3. Name the workbook: `SupplyChain_Analytics`
4. Click Save — it opens in your browser at your public profile URL
5. Copy the URL: `https://public.tableau.com/app/profile/YOUR_USERNAME/viz/...`
6. Add this URL to the GitHub README as a badge or clickable link

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `forecast_units` column not found | Make sure you're using `forecast_4w_clean.csv`, not `forecast_4w.csv` |
| Date field not parsing | In Data Source tab, click the `Abc` icon on `week` and change to Date |
| Confidence band not showing | Check that `lower_80`/`upper_80` mark type is Area, not Line |
| Filter doesn't apply to all sheets | In filter dropdown: "Apply to worksheets → All using related data sources" |
