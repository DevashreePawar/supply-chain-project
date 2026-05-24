"""
Supply chain demand forecasting package.

Modules:
    data         — Load and clean weekly aggregates from Snowflake
    diagnostics  — Root-cause analysis for high MAPE
    models       — Four forecasters behind one interface (Naive, SeasonalNaive,
                   Prophet, SARIMA)
    cv           — Walk-forward cross-validation
    metrics      — Forecast error metrics (MAPE, sMAPE, MAE, RMSE)
    risk         — Reframe point forecasts as probabilistic stock-out risk
"""

__version__ = "0.2.0"
