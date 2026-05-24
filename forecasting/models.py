"""
Four forecast models behind a single interface.

The interface is intentionally minimal:
    forecaster.fit(train)              # train is a pd.Series indexed by week
    pred = forecaster.predict(h)       # h is horizon in weeks
    pred is a pd.DataFrame with columns: yhat, yhat_lower, yhat_upper

Adding new models = subclass BaseForecaster.

Why these four:
- Naive          → critical baseline. If Prophet can't beat "last week", it's broken.
- SeasonalNaive  → second baseline. Beats Naive on data with weekly/yearly seasonality.
- Prophet        → the model in our existing notebook. Now properly benchmarked.
- SARIMA         → classical statistical baseline. Often hard to beat for clean data.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class BaseForecaster(ABC):
    """Common interface for all forecast models."""

    name: str = "base"

    @abstractmethod
    def fit(self, train: pd.Series) -> "BaseForecaster":
        """Train on a series indexed by datetime."""

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """Return forecast for the next `horizon` periods.
        Output: DataFrame with columns yhat, yhat_lower (10th pctl),
        yhat_upper (90th pctl), indexed by forecast date.
        """


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

class NaiveForecaster(BaseForecaster):
    """The dumbest baseline: predict last observed value forever.
    For a model to be useful, it must beat this."""

    name = "naive"

    def fit(self, train: pd.Series) -> "NaiveForecaster":
        self._last_value = float(train.iloc[-1])
        self._last_date = train.index[-1]
        self._train_std = float(train.std())
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        freq = pd.infer_freq(pd.DatetimeIndex([self._last_date]).union(
            pd.date_range(self._last_date, periods=2, freq="W")
        )) or "W"
        future_dates = pd.date_range(
            start=self._last_date + pd.Timedelta(weeks=1),
            periods=horizon,
            freq="W-" + ["MON","TUE","WED","THU","FRI","SAT","SUN"][self._last_date.dayofweek]
        )
        # Use empirical std for 80% CI (z=1.282)
        ci_half = 1.282 * self._train_std
        return pd.DataFrame({
            "yhat": [self._last_value] * horizon,
            "yhat_lower": [max(0, self._last_value - ci_half)] * horizon,
            "yhat_upper": [self._last_value + ci_half] * horizon,
        }, index=future_dates)


class SeasonalNaiveForecaster(BaseForecaster):
    """Predict next week = same week one year ago. Strong baseline if there's
    yearly seasonality."""

    name = "seasonal_naive"
    SEASON = 52  # weeks in a year

    def fit(self, train: pd.Series) -> "SeasonalNaiveForecaster":
        self._train = train.copy()
        self._train_std = float(train.std())
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        last = self._train.index[-1]
        future_dates = pd.date_range(
            start=last + pd.Timedelta(weeks=1),
            periods=horizon,
            freq="W-" + ["MON","TUE","WED","THU","FRI","SAT","SUN"][last.dayofweek]
        )
        # Look back 52 weeks per future date
        predictions = []
        for d in future_dates:
            lookback = d - pd.Timedelta(weeks=self.SEASON)
            # Find the closest available date <= lookback
            available = self._train.index[self._train.index <= lookback]
            if len(available):
                predictions.append(float(self._train.loc[available[-1]]))
            else:
                # Series doesn't go back a full year — fall back to mean
                predictions.append(float(self._train.mean()))
        ci_half = 1.282 * self._train_std
        return pd.DataFrame({
            "yhat": predictions,
            "yhat_lower": [max(0, p - ci_half) for p in predictions],
            "yhat_upper": [p + ci_half for p in predictions],
        }, index=future_dates)


# ---------------------------------------------------------------------------
# Prophet
# ---------------------------------------------------------------------------

class ProphetForecaster(BaseForecaster):
    """Wrap Facebook Prophet behind our common interface."""

    name = "prophet"

    def __init__(self, interval_width: float = 0.8):
        self.interval_width = interval_width

    def fit(self, train: pd.Series) -> "ProphetForecaster":
        from prophet import Prophet

        df = pd.DataFrame({"ds": train.index, "y": train.values})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._model = Prophet(
                interval_width=self.interval_width,
                weekly_seasonality=False,  # data is already weekly aggregates
                yearly_seasonality=True,
                daily_seasonality=False,
            )
            self._model.fit(df)
        self._last_date = train.index[-1]
        self._last_dow = self._last_date.dayofweek
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        freq = "W-" + ["MON","TUE","WED","THU","FRI","SAT","SUN"][self._last_dow]
        future = self._model.make_future_dataframe(periods=horizon, freq=freq)
        forecast = self._model.predict(future)
        # Take only the future portion
        future_only = forecast.tail(horizon).set_index("ds")[
            ["yhat", "yhat_lower", "yhat_upper"]
        ].copy()
        # Floor at zero (negative demand is nonsensical)
        for col in future_only.columns:
            future_only[col] = future_only[col].clip(lower=0)
        return future_only


# ---------------------------------------------------------------------------
# SARIMA
# ---------------------------------------------------------------------------

class SARIMAForecaster(BaseForecaster):
    """Classical statistical model. Order chosen with sensible defaults
    rather than grid search (which doubles runtime per category)."""

    name = "sarima"

    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 1, 0, 52)):
        self.order = order
        self.seasonal_order = seasonal_order

    def fit(self, train: pd.Series) -> "SARIMAForecaster":
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                self._model = SARIMAX(
                    train,
                    order=self.order,
                    seasonal_order=self.seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                ).fit(disp=False, maxiter=50)
            except Exception:
                # Fallback to non-seasonal if SARIMA fails to converge
                self._model = SARIMAX(train, order=(1, 1, 1)).fit(disp=False, maxiter=50)
        self._last_date = train.index[-1]
        return self

    def predict(self, horizon: int) -> pd.DataFrame:
        forecast = self._model.get_forecast(steps=horizon)
        mean = forecast.predicted_mean
        ci = forecast.conf_int(alpha=0.2)  # 80% CI
        df = pd.DataFrame({
            "yhat": mean.clip(lower=0).values,
            "yhat_lower": ci.iloc[:, 0].clip(lower=0).values,
            "yhat_upper": ci.iloc[:, 1].clip(lower=0).values,
        }, index=mean.index)
        return df


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_MODELS = {
    "naive": NaiveForecaster,
    "seasonal_naive": SeasonalNaiveForecaster,
    "prophet": ProphetForecaster,
    "sarima": SARIMAForecaster,
}


def get_model(name: str) -> BaseForecaster:
    if name not in ALL_MODELS:
        raise KeyError(f"Unknown model: {name}. Available: {list(ALL_MODELS)}")
    return ALL_MODELS[name]()
