"""
Walk-forward cross-validation for time-series forecasting.

Random k-fold CV is WRONG for time series — it leaks the future into the past.
Walk-forward CV preserves temporal ordering:

    Fold 1:  train[ 0 : N         ]  →  test[ N         : N+horizon         ]
    Fold 2:  train[ 0 : N+step    ]  →  test[ N+step    : N+step+horizon    ]
    Fold 3:  train[ 0 : N+2*step  ]  →  test[ N+2*step  : N+2*step+horizon  ]
    ...

Also called "expanding window" CV.  An alternative is "rolling window" where
the train set has a fixed length — left as a future enhancement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pandas as pd

from .metrics import all_metrics
from .models import BaseForecaster, get_model


@dataclass
class CVFold:
    fold_id: int
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    train: pd.Series
    test: pd.Series


def make_folds(
    series: pd.Series,
    initial_train_size: int = 100,
    horizon: int = 4,
    step: int = 4,
    max_folds: int | None = None,
) -> Iterator[CVFold]:
    """Generate walk-forward CV folds.

    Args:
        series: Univariate time series indexed by datetime.
        initial_train_size: Min weeks of training data before first fold.
        horizon: Weeks ahead to forecast (test set size).
        step: Weeks between fold start positions.
        max_folds: Cap number of folds (None = all possible).
    """
    n = len(series)
    fold_id = 0
    train_size = initial_train_size

    while train_size + horizon <= n:
        if max_folds is not None and fold_id >= max_folds:
            break
        train = series.iloc[:train_size]
        test = series.iloc[train_size:train_size + horizon]
        yield CVFold(
            fold_id=fold_id,
            train_end=train.index[-1],
            test_start=test.index[0],
            test_end=test.index[-1],
            train=train,
            test=test,
        )
        train_size += step
        fold_id += 1


def evaluate_model(
    model_name: str,
    series: pd.Series,
    category_id: int,
    initial_train_size: int = 100,
    horizon: int = 4,
    step: int = 4,
    max_folds: int | None = None,
) -> list[dict]:
    """Run walk-forward CV for one model on one category's series.

    Returns a list of dicts (one per fold) with metrics + metadata.
    """
    results = []
    for fold in make_folds(series, initial_train_size, horizon, step, max_folds):
        model = get_model(model_name)
        try:
            model.fit(fold.train)
            pred = model.predict(horizon)
            # Align test/predicted by position (both have the same horizon length)
            metrics = all_metrics(fold.test.values, pred["yhat"].values[:horizon])
            results.append({
                "category_id": category_id,
                "model": model_name,
                "fold_id": fold.fold_id,
                "train_end": fold.train_end,
                "test_start": fold.test_start,
                "test_end": fold.test_end,
                "train_size": len(fold.train),
                **metrics,
            })
        except Exception as e:
            results.append({
                "category_id": category_id,
                "model": model_name,
                "fold_id": fold.fold_id,
                "train_end": fold.train_end,
                "test_start": fold.test_start,
                "test_end": fold.test_end,
                "train_size": len(fold.train),
                "mape": float("nan"),
                "smape": float("nan"),
                "mae": float("nan"),
                "rmse": float("nan"),
                "error": str(e),
            })
    return results


def evaluate_all_models(
    weekly_df: pd.DataFrame,
    model_names: list[str],
    categories: list[int],
    **cv_kwargs,
) -> pd.DataFrame:
    """Run all (model × category) combinations through CV.
    Returns a long DataFrame: one row per (model, category, fold).
    """
    from .data import get_category_series

    all_rows = []
    for cat_id in categories:
        series = get_category_series(weekly_df, cat_id)
        for model_name in model_names:
            results = evaluate_model(model_name, series, cat_id, **cv_kwargs)
            all_rows.extend(results)
    return pd.DataFrame(all_rows)
