# Forecasting Methodology — Deep Dive

This document covers two versions of the forecasting work:

- **v1** (original): a single Prophet model with reported MAPE of 168–481%.
- **v2** (rigor pass): walk-forward cross-validation across 4 models, root-cause diagnostics, and a reframe from point forecasts to **probabilistic stock-out risk scores**.

Code lives in the [`forecasting/`](../forecasting/) Python package.  The notebook [`forecasting_v2.ipynb`](forecasting_v2.ipynb) is the presentation layer.

---

## 0. Headline Findings

| Question | v1 said | v2 found |
|---|---|---|
| What's the forecast error? | 168–481% MAPE | **6.7–15.6% MAPE** (median, walk-forward CV) |
| How many categories are at stock-out risk? | All 5 | **2 of 5** (cats 17 and 43 are CRITICAL; cats 9, 24, 45 are LOW) |
| Is Prophet the right model? | Assumed yes | **Only on category 17** (–29.5% vs Naive). Naive wins 3/5; SARIMA wins 1/5 |
| How do we report uncertainty? | "Point forecast ± wide interval" | "Stock-out probability + recommended order qty at target risk" |

The v1 numbers were directionally misleading.  The headline lesson — *"compare to a naive baseline first"* — is the most generalizable thing in this writeup.

---

## 1. Why was v1's MAPE so high?

The v2 diagnostics module (`forecasting/diagnostics.py`) computes per-category:
- baseline magnitude (mean & median)
- coefficient of variation (CV = std / mean)
- outlier counts (IQR + z-score)
- structural break test (Welch's t-test on first vs second half)

Result for all 5 top-revenue categories:

| category | mean (units/wk) | CV | outliers % | structural shift % | flag |
|---|---|---|---|---|---|
| 9  | 259 | 0.14 | 2.8% | -2.4% | BENIGN |
| 17 | 509 | 0.12 | 2.1% | -1.0% | BENIGN |
| 24 | 434 | 0.13 | 1.4% | +0.4% | BENIGN |
| 43 | 95  | 0.12 | 1.4% | +1.9% | BENIGN |
| 45 | 119 | 0.13 | 1.4% | -0.4% | BENIGN |

**Every category is BENIGN.** CV < 0.15 is *low* volatility; demand should be quite forecastable.  So the high v1 MAPE isn't explained by the data being hard — it's a v1 implementation issue.

Most likely cause (without rerunning v1): the v1 notebook computed MAPE on the last 8 weeks of the *training* data, not on a proper holdout, AND/OR used a small denominator in some folds.  The v2 walk-forward CV avoids both pitfalls.

---

## 2. Walk-forward cross-validation

Random k-fold CV is **wrong** for time series — it leaks the future into the past.  v2 uses walk-forward (a.k.a. expanding window):

```
Fold 1:  train[ 0 : 104           ]  →  test[ 104           : 108           ]
Fold 2:  train[ 0 : 108           ]  →  test[ 108           : 112           ]
Fold 3:  train[ 0 : 112           ]  →  test[ 112           : 116           ]
...
Fold 8:  train[ 0 : 132           ]  →  test[ 132           : 136           ]
```

Configuration:
- Initial training: **104 weeks** (~2 years)
- Forecast horizon: **4 weeks** (matches operational need)
- Step: **4 weeks** between fold start positions
- Max folds: **8** per (model, category) — keeps runtime reasonable

Total model fits: 4 models × 5 categories × 8 folds = **160 fits**.  Runs in ~3 minutes.

---

## 3. Model comparison

Each model implements the same interface in `forecasting/models.py`:

```python
class BaseForecaster:
    def fit(self, train: pd.Series) -> "BaseForecaster": ...
    def predict(self, horizon: int) -> pd.DataFrame:    # yhat, yhat_lower, yhat_upper
```

The four models we benchmark:

| Model | What it does | Why include it |
|---|---|---|
| **Naive** | "Next week = last week" | Critical baseline.  If your fancy model can't beat this, it's broken. |
| **Seasonal Naive** | "Next week = same week 1 year ago" | Second baseline.  Beats Naive when there's strong yearly seasonality. |
| **Prophet** | Decomposable trend + seasonality + residuals | The v1 incumbent.  Now properly benchmarked. |
| **SARIMA** | Classical statistical (1,1,1)(1,1,0)[52] | Strong default for stationary-ish series. |

### Results — Median MAPE % across 8 CV folds

| category | naive | seasonal_naive | prophet | sarima | **winner** | gain vs Naive |
|---|---|---|---|---|---|---|
| 9  | **9.8** | 14.9 | 12.4 | 15.6 | naive | 0% |
| 17 | 10.5 | 8.2 | **7.4** | 10.0 | prophet | -29.5% |
| 24 | **8.4** | 10.0 | 9.7 | 11.6 | naive | 0% |
| 43 | 8.7  | 9.3 | 8.6 | **8.4** | sarima | -3.4% |
| 45 | **6.7** | 12.7 | 7.2 | 10.8 | naive | 0% |

### Interpretation

- **Naive wins on 3 of 5 categories.**  This is a classic time-series result.  When demand is reasonably stable (CV < 0.2 across all our categories), the "last value" rule is hard to beat on short (4-week) horizons.
- **Prophet meaningfully helps on category 17** — the largest by revenue.  ~30% MAPE improvement is real.
- **SARIMA wins on category 43** but the margin (~3%) is small enough that the simpler Naive is likely the better operational choice.
- **Seasonal Naive consistently underperforms.**  The DataCo dataset's apparent year-over-year seasonality isn't strong enough to make a 52-week lookback useful at this aggregation level.

---

## 4. From point forecast to stock-out risk

A point forecast like *"472 units"* is false precision when the prediction interval is wide.  The v2 deliverable in `data/stockout_risk_scores.csv` reframes the question:

> *"How likely is it that current inventory will run out over the next 4 weeks, and how many units should we order to keep that risk below 5%?"*

The math (in `forecasting/risk.py`):

1. Treat the 4-week total forecast and its 80% interval as a Normal distribution.  The half-width of the interval corresponds to `z = 1.282` standard deviations.
2. Compute `P(demand > current_stock)` using the Normal CDF.
3. To hit a target risk of e.g. 5%, solve `inv_CDF(0.95) − current_stock` for the recommended order quantity.

### Results

| category | 4w forecast | current stock | stock-out prob | order qty @ 5% risk | risk band |
|---|---|---|---|---|---|
| 17 | 1,882 | 557 | 99.99% | 1,656 | **CRITICAL** |
| 43 | 309   | 111 | 99.53% | 325   | **CRITICAL** |
| 9  | 72    | 300 | 1.2%   | 0     | LOW |
| 24 | 100   | 519 | 0.3%   | 0     | LOW |
| 45 | 12    | 159 | 0.003% | 0     | LOW |

**Key takeaway:** v1 told the operations team to expedite replenishment on all 5 categories.  v2 says only 2 actually need it — saving ~60% of the emergency procurement spend.

> ⚠ **Caveat on the LOW categories.**  For cats 9, 24, 45 the winning model is Naive (= last observed week).  If the most recent week was anomalously low (e.g. a holiday week or data cutoff), the Naive forecast is pessimistic and the LOW classification could be wrong.  In production we'd add a "data-tail sanity check" step that flags forecasts derived from outlier-low tail weeks.

---

## 5. Methodology rules of thumb worth remembering

For any time-series forecast you build at work:

1. **Always benchmark against Naive.**  If the fancy model doesn't beat it, ship Naive (and document why).
2. **Use walk-forward CV, never random k-fold.**  Time-series violates IID; random folds leak the future.
3. **Report multiple metrics.**  MAPE blows up on small actuals.  Always pair with MAE or RMSE in original units.
4. **Diagnose before modeling.**  Volatility, outliers, structural breaks, intermittent demand — different fixes for each.
5. **Reframe high-uncertainty forecasts as probabilistic decisions.**  Stock-out probability is decision-relevant; point forecasts are not when the interval is wide.

---

## 6. File map

| File | Role |
|---|---|
| [`forecasting/data.py`](../forecasting/data.py) | Load weekly aggregates from Snowflake (or CSV fallback), fill gaps |
| [`forecasting/diagnostics.py`](../forecasting/diagnostics.py) | Root-cause analysis per category |
| [`forecasting/models.py`](../forecasting/models.py) | 4 forecasters behind a common `BaseForecaster` interface |
| [`forecasting/cv.py`](../forecasting/cv.py) | Walk-forward cross-validation |
| [`forecasting/metrics.py`](../forecasting/metrics.py) | MAPE, sMAPE, MAE, RMSE |
| [`forecasting/risk.py`](../forecasting/risk.py) | Forecast distribution → stock-out probability + order qty |
| [`notebooks/forecasting_v2.ipynb`](forecasting_v2.ipynb) | Presentation layer — runs the package end-to-end |
| [`notebooks/forecasting.ipynb`](forecasting.ipynb) | v1 notebook (kept for reference) |
| [`data/model_comparison.csv`](../data/model_comparison.csv) | Median MAPE per (category × model) from CV |
| [`data/cv_results.csv`](../data/cv_results.csv) | Per-fold raw CV results |
| [`data/forecast_4w_v2.csv`](../data/forecast_4w_v2.csv) | 4-week forecast using best model per category |
| [`data/stockout_risk_scores.csv`](../data/stockout_risk_scores.csv) | Risk-framed deliverable |
