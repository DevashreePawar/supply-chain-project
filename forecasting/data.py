"""
Load weekly aggregates from Snowflake (or the CSV fallback) and clean them.

The cleaning step is important: gaps in weekly data break time-series models,
and outliers from one-off promotions cause Prophet to overfit.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


# Top 5 categories by revenue — same set the original notebook used.
TOP_CATEGORIES = [45, 17, 43, 9, 24]


def load_from_snowflake() -> pd.DataFrame:
    """Pull the AGG_WEEKLY_ORDERS table directly from Snowflake."""
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database="SUPPLY_CHAIN",
        schema="DBT_DEV_MARTS",
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT order_week, category_id, units_sold, orders, net_sales
        FROM agg_weekly_orders
        WHERE category_id IN (45, 17, 43, 9, 24)
        ORDER BY order_week, category_id
    """)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=[c[0].lower() for c in cur.description])
    cur.close()
    conn.close()
    return df


def load_from_csv() -> pd.DataFrame:
    """Fallback if Snowflake isn't reachable — use the local CSV."""
    csv_path = _PROJECT_ROOT / "data" / "weekly_orders_clean.csv"
    df = pd.read_csv(csv_path)
    df = df.rename(columns=str.lower)
    df = df[df["category_id"].isin(TOP_CATEGORIES)].copy()
    # CSV has total_quantity rather than units_sold, normalize the name
    if "total_quantity" in df.columns and "units_sold" not in df.columns:
        df = df.rename(columns={"total_quantity": "units_sold"})
    if "order_count" in df.columns and "orders" not in df.columns:
        df = df.rename(columns={"order_count": "orders"})
    return df[["order_week", "category_id", "units_sold", "orders", "total_net_sales"]].rename(
        columns={"total_net_sales": "net_sales"}
    )


def load_weekly_demand(source: str = "auto") -> pd.DataFrame:
    """Load weekly demand, preferring Snowflake but falling back to CSV.

    Returns a tidy DataFrame: order_week (datetime), category_id (int),
    units_sold, orders, net_sales.
    """
    if source == "auto":
        try:
            df = load_from_snowflake()
        except Exception:
            df = load_from_csv()
    elif source == "snowflake":
        df = load_from_snowflake()
    else:
        df = load_from_csv()

    df["order_week"] = pd.to_datetime(df["order_week"])
    df["category_id"] = df["category_id"].astype(int)
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0)
    return df.sort_values(["category_id", "order_week"]).reset_index(drop=True)


def fill_weekly_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """For each category, re-index to a complete weekly range. Missing weeks
    become 0 units (the category simply had no orders that week).

    Time-series models fail or behave erratically on irregular indexes. This
    enforces a strict weekly grid.
    """
    out = []
    for cat, group in df.groupby("category_id"):
        group = group.set_index("order_week").sort_index()
        full_range = pd.date_range(group.index.min(), group.index.max(), freq="W-MON")
        # Snap to the same day-of-week as the data
        actual_dow = group.index[0].dayofweek
        full_range = pd.date_range(
            group.index.min(),
            group.index.max(),
            freq=f"W-{['MON','TUE','WED','THU','FRI','SAT','SUN'][actual_dow]}"
        )
        group = group.reindex(full_range)
        group["category_id"] = cat
        group["units_sold"] = group["units_sold"].fillna(0)
        group["orders"] = group["orders"].fillna(0)
        group["net_sales"] = group["net_sales"].fillna(0)
        group.index.name = "order_week"
        out.append(group.reset_index())
    return pd.concat(out, ignore_index=True)


def get_category_series(df: pd.DataFrame, category_id: int) -> pd.Series:
    """Return a single category's univariate time series, indexed by week."""
    cat_df = df[df["category_id"] == category_id].copy()
    cat_df = cat_df.set_index("order_week").sort_index()
    return cat_df["units_sold"].astype(float)
