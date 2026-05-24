"""
OpenAI client for natural-language → SQL conversion.

Uses GPT-4o-mini by default (cheap, fast, accurate enough for analytical SQL).
Prompt caching reduces cost ~50% from the 2nd query onwards.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from schema_context import build_schema_context

# Load env vars from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _get_secret(key: str, default: str | None = None) -> str | None:
    value = os.environ.get(key)
    if value:
        return value
    try:
        return st.secrets[key]
    except Exception:
        return default


@dataclass
class SQLGeneration:
    sql: str
    explanation: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int


def _build_system_prompt() -> str:
    schema = build_schema_context()
    return f"""You are a SQL expert for a supply-chain analytics warehouse running on Snowflake.

Your job: convert the user's natural-language question into a single, safe SELECT query
against the tables described below.

# Schema

{schema}

# Rules

1. Generate **exactly one** SELECT (or WITH) statement. No DDL, no DML, no semicolons separating statements.
2. Refer to tables by their unqualified name (e.g. `fct_orders`, `dim_product`). Do NOT prefix with schema/database.
3. Use Snowflake SQL syntax. `DATEADD`, `DATE_TRUNC`, `EXTRACT(... FROM ...)`, `QUALIFY`, etc.
4. Always include a `LIMIT` clause (max 5000) unless the user asks for an aggregate that returns few rows.
5. For "late delivery" questions, use `is_late_flag` (canonical), not `is_on_time_flag` (different logic).
6. When dates are mentioned, the dataset covers 2014-2018. Use `order_date` for filtering.
7. If the question is ambiguous, make a reasonable assumption and note it in your explanation.
8. If the question can't be answered from the schema, return an error in the SQL field as a comment.

# Output format

Return JSON only, matching this schema:
{{
  "sql": "<the SQL query>",
  "explanation": "<one or two sentences in plain English explaining what the query does>"
}}

# Example

User question: "What was the late delivery rate for Standard Class shipping in 2017?"

Response:
{{
  "sql": "SELECT ROUND(AVG(is_late_flag) * 100, 1) AS late_rate_pct FROM fct_orders WHERE shipping_mode = 'Standard Class' AND EXTRACT(YEAR FROM order_date) = 2017 LIMIT 1",
  "explanation": "Computes the percentage of Standard Class orders in 2017 that were marked as late deliveries."
}}
"""


def generate_sql(question: str) -> SQLGeneration:
    """Convert a natural-language question to SQL using GPT-4o-mini."""
    api_key = _get_secret("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Set it in .env (local) or Streamlit Cloud secrets."
        )

    model = _get_secret("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    system_prompt = _build_system_prompt()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,    # deterministic — same Q always returns same SQL
        max_tokens=600,
    )

    raw = response.choices[0].message.content or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"LLM returned non-JSON response: {raw[:200]}")

    sql = payload.get("sql", "").strip()
    explanation = payload.get("explanation", "").strip()
    if not sql:
        raise RuntimeError("LLM did not return a SQL query.")

    usage = response.usage
    return SQLGeneration(
        sql=sql,
        explanation=explanation,
        model=model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cached_tokens=getattr(usage, "prompt_tokens_details", None).cached_tokens
            if getattr(usage, "prompt_tokens_details", None) else 0,
    )
