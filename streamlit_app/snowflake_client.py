"""
Snowflake connection + query helpers for the Streamlit app.

Loads credentials from .env locally, falls back to st.secrets / env vars
when deployed on Streamlit Cloud.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

# Load .env from the project root (one level up from streamlit_app/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _get_credential(key: str) -> str:
    """Read a credential from env vars (loaded from .env locally, or set by
    Streamlit Cloud's secret manager) and fall back to st.secrets if needed."""
    # Primary path: env vars
    value = os.environ.get(key)
    if value:
        return value
    # Fallback: Streamlit secrets file (only used if no env var present).
    # Wrapped in try because st.secrets raises if no secrets.toml exists.
    try:
        return st.secrets[key]
    except Exception:
        raise RuntimeError(
            f"Missing credential: {key}. Set it in .env (local) or "
            f"Streamlit Cloud → App settings → Secrets."
        ) from None


@st.cache_resource(show_spinner="Connecting to Snowflake…")
def get_connection() -> snowflake.connector.SnowflakeConnection:
    """One Snowflake connection per Streamlit session (cached)."""
    return snowflake.connector.connect(
        account=_get_credential("SNOWFLAKE_ACCOUNT"),
        user=_get_credential("SNOWFLAKE_USER"),
        password=_get_credential("SNOWFLAKE_PASSWORD"),
        role=_get_credential("SNOWFLAKE_ROLE"),
        warehouse=_get_credential("SNOWFLAKE_WAREHOUSE"),
        database=_get_credential("SNOWFLAKE_DATABASE"),
        schema="DBT_DEV_MARTS",
        client_session_keep_alive=True,
    )


def run_query(sql: str) -> pd.DataFrame:
    """Execute a SQL query and return results as a pandas DataFrame.

    Caching here would be wrong — the user expects each click to actually run.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [col[0].lower() for col in cur.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()


@st.cache_data(ttl=600, show_spinner="Fetching schema…")
def list_tables() -> pd.DataFrame:
    """Return all tables/views across the project's marts + staging schemas."""
    sql = """
        SELECT table_schema, table_name, table_type, row_count
        FROM SUPPLY_CHAIN.INFORMATION_SCHEMA.TABLES
        WHERE table_schema IN ('DBT_DEV_MARTS', 'DBT_DEV_STAGING')
        ORDER BY table_schema, table_name
    """
    return run_query(sql)


@st.cache_data(ttl=600)
def describe_table(schema: str, table: str) -> pd.DataFrame:
    """Return column-level metadata for a single table."""
    sql = f"""
        SELECT column_name, data_type, is_nullable, comment
        FROM SUPPLY_CHAIN.INFORMATION_SCHEMA.COLUMNS
        WHERE table_schema = '{schema.upper()}'
          AND table_name = '{table.upper()}'
        ORDER BY ordinal_position
    """
    return run_query(sql)


def health_check() -> dict[str, Any]:
    """Lightweight ping — returns connection details for the sidebar."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_VERSION(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()")
        version, user, role, warehouse = cur.fetchone()
        cur.close()
        return {
            "status": "✅ Connected",
            "version": version,
            "user": user,
            "role": role,
            "warehouse": warehouse,
        }
    except Exception as e:
        return {"status": "❌ Disconnected", "error": str(e)}
