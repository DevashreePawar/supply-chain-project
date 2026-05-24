# Executive Memo — Structure & Interpretation Guide

## Files

| File | Description |
|------|-------------|
| `stakeholder_memo_template.md` | Editable markdown version of the memo |
| `stakeholder_memo.pdf` | Final PDF for stakeholder distribution |

---

## Memo Structure

The memo follows a strict **Finding → Why → Recommendation** structure for each of the 3 findings. This format is standard for data-driven ops memos and is designed for a VP with limited time.

```
Finding:        What the data shows (metric + comparison)
Why it matters: Business impact (revenue, cost, churn, efficiency)
Recommendation: Specific, actionable, with estimated impact
```

---

## Where the Numbers Come From

| Memo claim | Source |
|------------|--------|
| Standard Class late rate (38.1%) | `sql/analysis/03_shipping_mode_performance.sql` → `pct_late` for Standard Class |
| First Class on-time rate (95.3%) | Same query |
| ~39K late Standard Class orders | `shipping_modes.csv` → `late_orders` column |
| $1.9M goodwill loss estimate | `est_goodwill_cost` in query 03 (= 5% of late-order revenue; see caveat below) |
| 4-week demand forecast (6,359 units aggregate) | `data/forecast_4w.csv` → sum of `forecast_units` across all categories |
| Current inventory (1,646 units) | `data/inventory_health.csv` → sum of `current_stock` |
| Shortfall (3,783 units) | `data/inventory_health.csv` → sum of `gap`; worst categories: 17 (+1,334), 24 (+1,161), 9 (+693) |
| Same Day on-time rate (45.7%) | `shipping_modes.csv` → `on_time_percent` for Same Day |
| Same Day share (5% of orders) | 9,737 ÷ 180,519 total orders |

---

## Important Caveats

### Goodwill cost ($1.9M)
The $1.9M figure is derived from a **5% churn assumption**: 5% of revenue from late orders is estimated as goodwill/retention loss. This is a common heuristic in logistics ops memos. The 5% is **not calibrated to this specific company** — it should be replaced with actual churn data from a CRM before presenting to finance.

### MAPE (168–481%)
The Prophet forecast model has very high MAPE. This does not invalidate the stock-out flags — all categories face a shortfall even under conservative stock assumptions. However, the point forecast quantities should **not** be used as literal order quantities. Use the `upper_80` confidence bound as the procurement target.

### Same Day recommendation
Same Day shipping has a 45.7% on-time rate — lower than Second Class (76.6%). The "bundle as free upgrade" recommendation is a volume strategy, but it requires addressing the on-time failure rate first. As written, the recommendation should include a prerequisite: fix the Same Day carrier SLA before marketing it as a premium tier.

---

## How to Convert Template to PDF

**Option 1 — Pandoc (recommended):**
```bash
pandoc memo/stakeholder_memo_template.md -o memo/stakeholder_memo.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt
```

**Option 2 — VS Code:**
Install the "Markdown PDF" extension → right-click the `.md` file → "Markdown PDF: Export (pdf)"

**Option 3 — Any online converter:**
Upload the `.md` file to [md2pdf.com](https://md2pdf.com) or similar.
