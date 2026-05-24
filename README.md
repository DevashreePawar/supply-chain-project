# Supply Chain Analytics — End-to-End Modern Data Stack

[![dbt CI](https://github.com/DevashreePawar/supply-chain-project/actions/workflows/dbt-ci.yml/badge.svg)](https://github.com/DevashreePawar/supply-chain-project/actions/workflows/dbt-ci.yml)
[![dbt Docs](https://github.com/DevashreePawar/supply-chain-project/actions/workflows/dbt-docs.yml/badge.svg)](https://devashreepawar.github.io/supply-chain-project/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?logo=streamlit&logoColor=white)](https://supply-chain-data.streamlit.app/)
[![dbt](https://img.shields.io/badge/dbt-1.11-orange?logo=dbt)](https://www.getdbt.com/)
[![Snowflake](https://img.shields.io/badge/Snowflake-data%20warehouse-29B5E8?logo=snowflake&logoColor=white)](https://snowflake.com)
[![OpenAI](https://img.shields.io/badge/GPT--4o--mini-NL%E2%86%92SQL-412991?logo=openai&logoColor=white)](https://platform.openai.com/)

> 180K orders → dbt-tested Snowflake warehouse → walk-forward-validated forecasts → Tableau dashboard → **AI app where you ask questions in plain English**.

---

## 🌐 Live Demos

| | URL | What it shows |
|---|---|---|
| 🤖 **AI Query App** | **[supply-chain-data.streamlit.app](https://supply-chain-data.streamlit.app/)** | Ask questions in English; GPT-4o-mini writes safe SQL against the dbt schema |
| 📖 **dbt Docs Site** | **[devashreepawar.github.io/supply-chain-project](https://devashreepawar.github.io/supply-chain-project/)** | Auto-generated docs with column-level descriptions + lineage graph |
| 📊 **Tableau Dashboard** | **[Tableau Public](https://public.tableau.com/app/profile/devashree.pawar/viz/SupplyChain_17795849723580/Dashboard1)** | 4-page interactive dashboard with filters and drill-down |
| 🧪 **CI Pipeline** | **[GitHub Actions](https://github.com/DevashreePawar/supply-chain-project/actions)** | 48 tests run on every PR; docs auto-deploy to GitHub Pages |

---

## 🏗️ Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │  GitHub Actions CI                          │
                     │  ✓ dbt build + 48 tests on every push       │
                     │  ✓ dbt docs auto-deploy to GitHub Pages     │
                     └─────────────────────────────────────────────┘
                                       │
   ┌────────────┐                      ▼                      ┌────────────────────┐
   │ DataCo CSV │ ──► Snowflake ──► dbt (9 models, 39 tests) ──┤ AI Query App      │
   │  180,519   │     SUPPLY_CHAIN    │       │                │  Streamlit +      │
   │  orders    │                     │       │                │  GPT-4o-mini      │
   └────────────┘                     │       │                │  + SQL safety     │
                                      │       │                └────────────────────┘
                                      │       │
                                      │       ▼
                                      │  ┌─────────────────────────┐
                                      │  │ Forecasting Package     │
                                      │  │ - 4 models benchmarked  │
                                      │  │ - Walk-forward CV       │
                                      │  │ - Stock-out risk scores │
                                      │  └─────────────────────────┘
                                      ▼
                                ┌──────────────┐
                                │ Tableau      │
                                │ Public       │
                                │ Dashboard    │
                                └──────────────┘
```

---

## 🧰 Tech Stack

| Layer | Tool | What it does here |
|---|---|---|
| **Storage** | Snowflake | 180,519 orders, star schema, separate `DBT_DEV` / `DBT_CI` schemas |
| **Transformation** | **dbt 1.11** | 3 staging views + 6 marts tables + 6 analyses, ref()-based DAG |
| **Data Quality** | dbt tests | 36 generic (unique, not_null, accepted_values, FK relationships) + 3 custom singular tests |
| **CI/CD** | GitHub Actions | Auto-test on PR, auto-deploy docs to GitHub Pages |
| **Forecasting** | Custom Python pkg | Naive + Seasonal Naive + Prophet + SARIMA behind one interface, walk-forward CV |
| **AI / NL→SQL** | OpenAI GPT-4o-mini | Reads dbt schema from `manifest.json`, generates safe SELECT queries |
| **App Framework** | Streamlit | Free deployment, prompt-caching enabled, ~$0.0003 per query |
| **Dashboard** | Tableau Public | 4-page interactive dashboard |
| **Memo** | Markdown → PDF | 3-finding executive summary with quantified impact |

---

## 🎯 What Makes This Project Notable

### 1. The AI layer reads from dbt — single source of truth

The Streamlit app's LLM prompt is built dynamically from `target/manifest.json` (dbt's documentation artifact). When you update a column description in `models/marts/_marts.yml`, the AI gets smarter automatically. No code change, no prompt edit. This is the modern data stack flywheel working end-to-end.

### 2. Forecast rigor — Naive beats Prophet on 3 of 5 categories

The original notebook reported MAPE of 168-481% from a single Prophet model. The v2 rigor pass added walk-forward cross-validation across 4 models — **actual median MAPE is 6.7-15.6%**, and Naive wins on most categories. Prophet only meaningfully helps on the largest category (-29.5% vs Naive on cat 17).

> The v1 numbers were a non-rigorous holdout calculation, not a real validation. Catching this kind of thing is exactly what walk-forward CV exists for. See [FORECASTING_EXPLAINED.md](notebooks/FORECASTING_EXPLAINED.md).

### 3. Reframed forecasting from point estimates to risk scores

Instead of *"order 472 units of category 45"* (false precision when intervals are wide), the deliverable is *"current stock-out risk is 99.99% — to keep risk under 5%, order 1,656 units"*. Decision-relevant under uncertainty. See [`data/stockout_risk_scores.csv`](data/stockout_risk_scores.csv).

### 4. Defense-in-depth SQL safety on the AI app

Three layers prevent the LLM from ever writing destructive SQL:
1. System prompt instructs SELECT-only
2. Regex-based [`streamlit_app/safety.py`](streamlit_app/safety.py) rejects DDL/DML keywords, strips comments + string literals before matching, rejects multi-statement queries, auto-adds `LIMIT 5000`
3. Snowflake role permissions (in production: a read-only role)

Even a perfect prompt injection cannot drop a table.

---

## 📊 Headline Findings

| Finding | Impact | Recommendation |
|---|---|---|
| **Standard Class late (38.1%)** | $1.9M goodwill loss (5% churn assumption — flagged as needing CRM calibration) | Pilot upgrade to Second Class for orders >$250 → ~$1.2M savings |
| **2 of 5 top categories stock-out CRITICAL** (cats 17, 43) | Revenue loss + 2-3× emergency procurement cost | Order 1,981 units total to hit 5% target risk; the other 3 categories show LOW risk and don't need expediting (v1 over-recommended) |
| **Same Day shipping has 45.7% on-time rate** | Underperforming a premium tier | Fix the carrier SLA before any volume-growth strategy. v1 recommendation to "bundle as free upgrade" needs reconsideration |

Full memo: [`memo/stakeholder_memo.pdf`](memo/stakeholder_memo.pdf).

---

## 📂 Project Structure

```
supply-chain-project/
├── README.md                    # This file
├── QUICKSTART.md                # 90-minute setup guide
├── requirements.txt             # All Python deps
├── run-dbt.sh                   # Loads .env + runs dbt with project-local profiles.yml
├── dbt_project.yml              # dbt project manifest
├── profiles.yml                 # Connection config (reads from env vars)
├── .env.example                 # Template for local credentials (real .env is gitignored)
│
├── .github/workflows/
│   ├── dbt-ci.yml               # Build + test on every PR/push
│   └── dbt-docs.yml             # Deploy dbt docs to GitHub Pages
│
├── models/                      # dbt models
│   ├── staging/                 # 3 cleaning views (stg_orders, stg_products, stg_customers)
│   └── marts/                   # 6 production tables (fct_orders, dim_*, agg_*)
├── macros/is_late.sql           # Reusable late-flag definition (single source of truth)
├── tests/                       # 3 custom singular tests
│   ├── assert_revenue_reconciliation.sql
│   ├── assert_late_flags_drift_within_threshold.sql
│   └── assert_no_future_orders.sql
├── analyses/                    # 6 dbt analyses (compiled but not materialized)
│
├── forecasting/                 # Custom Python package — Phase 5 rigor pass
│   ├── data.py                  # Load weekly aggregates, gap-fill
│   ├── diagnostics.py           # Per-category CV/outliers/structural breaks
│   ├── models.py                # 4 forecasters behind one interface
│   ├── cv.py                    # Walk-forward cross-validation
│   ├── metrics.py               # MAPE/sMAPE/MAE/RMSE
│   └── risk.py                  # Forecast distribution → stock-out probability
│
├── streamlit_app/               # The AI query app (Phase 3)
│   ├── app.py                   # Main Streamlit UI with dual mode (English / SQL)
│   ├── snowflake_client.py      # Connection pooling + schema browser
│   ├── schema_context.py        # Builds LLM prompt from dbt manifest.json + catalog.json
│   ├── llm_client.py            # OpenAI SDK with prompt caching
│   ├── safety.py                # SQL safety guards (defense in depth)
│   └── .streamlit/config.toml   # Navy + amber theme
│
├── notebooks/
│   ├── forecasting.ipynb        # v1 — original Prophet model (kept for reference)
│   ├── forecasting_v2.ipynb     # v2 — runs the forecasting/ package end-to-end
│   ├── FORECASTING_EXPLAINED.md # Methodology deep-dive (v1 vs v2 story)
│   └── README.md                # Notebook setup
│
├── data/                        # Generated outputs (gitignored except a handful)
│   ├── DataCoSupplyChainDataset.csv    # Raw input from Kaggle
│   ├── model_comparison.csv            # NEW — median MAPE per (cat × model)
│   ├── cv_results.csv                  # NEW — per-fold raw CV results
│   ├── forecast_4w_v2.csv              # NEW — best-model forecast per category
│   ├── stockout_risk_scores.csv        # NEW — risk-framed deliverable
│   └── (v1 outputs kept for comparison: forecast_4w.csv, inventory_health.csv, etc.)
│
├── target/                      # dbt build artifacts (mostly gitignored)
│   ├── manifest.json            # Tracked: read by Streamlit's schema_context.py
│   └── catalog.json             # Tracked: read by Streamlit's schema_context.py
│
├── sql/                         # Original SQL pipeline (pre-dbt; kept for reference)
├── tableau/                     # Wireframe + build guide for the Tableau dashboard
└── memo/                        # Executive memo + interpretation guide
```

---

## ⚡ Try the AI App in 30 Seconds

1. Open **[supply-chain-data.streamlit.app](https://supply-chain-data.streamlit.app/)**
2. Click one of the sample questions, OR type your own:
   - *"Which 5 categories drove the most profit in 2017?"*
   - *"Show me the late delivery trend by month for First Class"*
   - *"What's the average order value by customer segment?"*
3. Click **✨ Ask**
4. See the answer as a chart + table. Expand **"🔍 Generated SQL"** to audit the LLM's output.

Cost per question: **~$0.0003** (gpt-4o-mini with prompt caching).

---

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- A Snowflake account (free trial works)
- An OpenAI API key (free tier with $5 credit is enough)

### Setup

```bash
# 1. Clone
git clone https://github.com/DevashreePawar/supply-chain-project.git
cd supply-chain-project

# 2. Python env + deps
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Snowflake + OpenAI credentials
cp .env.example .env
# Edit .env and fill in your real values

# 4. Load raw data (one-time)
# Open sql/00_load_data.sql in Snowflake UI → create schema → load CSV via UI
# Detailed instructions in QUICKSTART.md
```

### Daily workflow

```bash
# Build the dbt project
./run-dbt.sh build

# Generate docs site
./run-dbt.sh docs generate
./run-dbt.sh docs serve     # opens at localhost:8080

# Run the AI app locally
cd streamlit_app && ../.venv/bin/streamlit run app.py     # localhost:8501

# Run the forecasting notebook
.venv/bin/jupyter notebook notebooks/forecasting_v2.ipynb
```

---

## 🧪 Data Quality — How We Catch Bugs

The dbt project has **48 automated tests** that run on every commit via GitHub Actions:

| Test type | Count | What it catches |
|---|---|---|
| `unique` | 6 | Duplicate primary keys |
| `not_null` | 12 | Missing required fields |
| `accepted_values` | 4 | Unexpected categorical values (e.g. typo'd shipping mode) |
| `relationships` | 3 | Foreign key orphans (every customer/product/date in fct_orders exists in its dim) |
| **Singular (custom)** | 3 | Business-rule violations: |
| | | • `assert_revenue_reconciliation` — fct_orders total == agg_weekly_orders total |
| | | • `assert_late_flags_drift_within_threshold` — monitors the documented dual-flag data quality issue |
| | | • `assert_no_future_orders` — catches date-parsing bugs producing year 9999 |

When a test fails, the CI workflow uploads the dbt logs as a downloadable artifact for debugging.

---

## 🔮 Forecasting — v1 vs v2

**v1** (`notebooks/forecasting.ipynb`): A single Prophet model evaluated on an 8-week holdout. Reported MAPE: 168-481%.

**v2** (`forecasting/` package + `notebooks/forecasting_v2.ipynb`): Walk-forward CV across 4 models. Actual median MAPE: **6.7-15.6%**.

| Category | Naive | Seasonal Naive | Prophet | SARIMA | **Winner** |
|---|---|---|---|---|---|
| 9  | **9.8%** | 14.9% | 12.4% | 15.6% | Naive |
| 17 | 10.5% | 8.2% | **7.4%** | 10.0% | Prophet (-29.5%) |
| 24 | **8.4%** | 10.0% | 9.7% | 11.6% | Naive |
| 43 | 8.7% | 9.3% | 8.6% | **8.4%** | SARIMA (-3.4%) |
| 45 | **6.7%** | 12.7% | 7.2% | 10.8% | Naive |

**Naive wins on 3 of 5 categories.** Prophet adds material value only on category 17. This is exactly the kind of finding walk-forward CV exists to surface.

The v2 deliverable in `data/stockout_risk_scores.csv` reframes the output from point forecasts to probabilistic risk scores. **2 of 5 categories are CRITICAL stock-out risk; the other 3 are LOW** (v1 said all 5 were at risk — that recommendation would have wasted ~60% of the emergency procurement spend).

Full methodology: [`notebooks/FORECASTING_EXPLAINED.md`](notebooks/FORECASTING_EXPLAINED.md).

---

## 🚨 Caveats (Honest Limitations)

I'd rather flag these than have an interviewer find them:

1. **The "$1.9M goodwill loss" uses a 5% churn assumption.** Common industry heuristic but not calibrated to this company. Production version would replace it with actual churn data from CRM.
2. **Current inventory is heuristic.** Set to `1.5× trailing 4-week mean` since we don't have a real WMS feed. Production: 1-line change to `pd.read_sql()`.
3. **The "Naive wins" categories may be sensitive to the last week of data.** If the data tail is anomalously low, Naive's forecast is too conservative. Production: add a "data-tail sanity check" before serving Naive forecasts. Flagged in FORECASTING_EXPLAINED.md.
4. **Same Day shipping recommendation needs revision.** The original memo suggests bundling Same Day as a free upgrade, but its on-time rate is only 45.7% — the SLA needs to be fixed before any volume play.
5. **The DataCo dataset is a Kaggle download.** Categories are anonymous numbers (Cat 17, Cat 24). A production version would use real product taxonomies.

---

## 🎓 Skills Demonstrated

| Domain | Specifics |
|---|---|
| **SQL** | Star schema design, window functions (RANK, moving averages, Pareto), cohort analysis, QUALIFY, conditional aggregation |
| **dbt** | Models, sources, macros, schema tests, custom singular tests, manifest.json introspection |
| **CI/CD** | GitHub Actions, repo secrets, env-isolated schemas (DBT_CI vs DBT_DEV), GitHub Pages deployment |
| **Snowflake** | Loading, role/warehouse management, INFORMATION_SCHEMA queries |
| **Python (Data Science)** | pandas, Prophet, SARIMA (statsmodels), walk-forward CV, MAPE/sMAPE/MAE/RMSE, probabilistic risk scoring |
| **Python (Engineering)** | Package structure, ABC base classes, dataclasses, type hints, error handling, secrets via dotenv |
| **AI / LLM** | OpenAI SDK, JSON-mode responses, prompt caching (~50% cost reduction), schema-aware system prompts, defense-in-depth safety |
| **Streamlit** | `@st.cache_resource` connection pooling, `st.session_state` widget patterns, Altair auto-charting, dual-mode UX |
| **Tableau** | Dashboard design, calculated fields, dual-axis charts, publishing to Tableau Public |
| **Communication** | Stakeholder memo (Finding → Why → Recommendation), honest caveats, methodology writeups |

---

## 📖 Where to Read More

| Topic | File |
|---|---|
| dbt pipeline walkthrough | [`sql/README.md`](sql/README.md) |
| Forecasting methodology (v1 vs v2) | [`notebooks/FORECASTING_EXPLAINED.md`](notebooks/FORECASTING_EXPLAINED.md) |
| Tableau dashboard build guide | [`tableau/TABLEAU_BUILD_GUIDE.md`](tableau/TABLEAU_BUILD_GUIDE.md) |
| Executive memo & interpretation | [`memo/README.md`](memo/README.md) |
| Initial setup walkthrough | [`QUICKSTART.md`](QUICKSTART.md) |

---

## 📄 License

MIT. Use freely as a reference for your own analytics-engineering projects.

---

**Built by [Devashree Pawar](https://github.com/DevashreePawar) · 2026**
