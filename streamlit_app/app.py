"""
Supply Chain Analytics — Streamlit App
---------------------------------------
Ask questions in plain English → GPT-4o-mini → SQL → Snowflake → chart.
Falls back to a raw SQL editor for power users.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from llm_client import generate_sql
from safety import UnsafeSQLError, validate
from snowflake_client import describe_table, health_check, list_tables, run_query

# ---------- Page setup ----------
st.set_page_config(
    page_title="Supply Chain Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Sidebar: connection + schema browser + mode toggle ----------
with st.sidebar:
    st.markdown("## 📦 Supply Chain Analytics")
    st.caption("dbt + Snowflake + OpenAI + Streamlit")

    st.divider()

    # Mode toggle
    mode = st.radio(
        "Mode",
        options=["🤖 Ask in English", "💻 Write SQL"],
        index=0,
        help="Ask: natural-language → GPT-4o-mini → SQL. SQL: bring your own.",
    )

    st.divider()

    # Connection status
    st.markdown("### Snowflake")
    hc = health_check()
    if hc.get("status", "").startswith("✅"):
        st.success(hc["status"])
        st.caption(
            f"**Role:** `{hc['role']}`  \n"
            f"**Warehouse:** `{hc['warehouse']}`  \n"
            f"**User:** `{hc['user']}`"
        )
    else:
        st.error(hc["status"])
        st.code(hc.get("error", ""), language="text")
        st.stop()

    st.divider()

    # Schema browser
    st.markdown("### 📂 Schema")
    tables_df = list_tables()
    if not tables_df.empty:
        selected_table = st.selectbox(
            "Tables & views",
            options=tables_df.apply(
                lambda r: f"{r['table_schema']}.{r['table_name']}", axis=1
            ).tolist(),
        )
        if selected_table:
            schema_name, table_name = selected_table.split(".")
            with st.expander("📋 Columns", expanded=False):
                cols_df = describe_table(schema_name, table_name)
                if not cols_df.empty:
                    st.dataframe(
                        cols_df[["column_name", "data_type"]],
                        use_container_width=True,
                        hide_index=True,
                    )


# ---------- Auto-chart helper ----------
def auto_chart(df: pd.DataFrame) -> alt.Chart | None:
    if df.empty or len(df.columns) < 2:
        return None
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
    if not numeric_cols:
        return None
    x_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
    y_col = numeric_cols[0]
    is_temporal = any(
        kw in x_col.lower() for kw in ("date", "week", "month", "year", "time", "ts")
    )
    if is_temporal:
        return (
            alt.Chart(df)
            .mark_line(point=True, color="#ffa600")
            .encode(
                x=alt.X(f"{x_col}:T", title=x_col),
                y=alt.Y(f"{y_col}:Q", title=y_col),
                tooltip=list(df.columns),
            )
            .properties(height=380)
        )
    return (
        alt.Chart(df)
        .mark_bar(color="#ffa600")
        .encode(
            x=alt.X(f"{x_col}:N", sort="-y", title=x_col),
            y=alt.Y(f"{y_col}:Q", title=y_col),
            tooltip=list(df.columns),
        )
        .properties(height=380)
    )


def render_results(df: pd.DataFrame) -> None:
    """Common result renderer for both modes."""
    if df.empty:
        st.info("Query returned no rows.")
        return
    st.markdown(f"### Results — {len(df):,} row{'s' if len(df) != 1 else ''}")
    chart = auto_chart(df)
    if chart is not None:
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# MAIN AREA
# ============================================================================

st.title("Ask your supply chain data")

# ----------------------------------------------------------------------------
# MODE 1: Natural language
# ----------------------------------------------------------------------------
if mode == "🤖 Ask in English":
    st.markdown(
        "Ask a question about deliveries, revenue, inventory, or customer behaviour. "
        "GPT-4o-mini converts your question to SQL, which runs against the dbt-tested "
        "Snowflake schema."
    )

    # Sample questions to lower the blank-page intimidation
    st.markdown("**💡 Try one of these:**")
    sample_cols = st.columns(3)
    SAMPLES = [
        "What was the late delivery rate by shipping mode in 2017?",
        "Which 5 product categories had the highest revenue?",
        "How did weekly order volume trend over time?",
    ]

    if "nl_question" not in st.session_state:
        st.session_state.nl_question = ""

    for col, sample in zip(sample_cols, SAMPLES):
        if col.button(sample, use_container_width=True):
            st.session_state.nl_question = sample

    question = st.text_input(
        "Your question",
        key="nl_question",
        placeholder="e.g. What's our average order value by customer segment?",
        label_visibility="collapsed",
    )

    ask = st.button("✨ Ask", type="primary", disabled=not question.strip())

    if ask and question.strip():
        try:
            with st.spinner("🤔 GPT-4o-mini is writing SQL…"):
                gen = generate_sql(question)
        except Exception as e:
            st.error(f"LLM call failed: {e}")
            st.stop()

        # Show the explanation prominently
        st.info(f"💬 **{gen.explanation}**")

        # Safety check
        try:
            safe_sql = validate(gen.sql)
        except UnsafeSQLError as e:
            st.error(f"🛡️ Query rejected by safety guard: {e}")
            with st.expander("Show rejected SQL"):
                st.code(gen.sql, language="sql")
            st.stop()

        # Show the SQL (collapsed by default — audit trail)
        with st.expander("🔍 Generated SQL", expanded=False):
            st.code(safe_sql, language="sql")
            st.caption(
                f"Model: `{gen.model}` · "
                f"Prompt tokens: {gen.prompt_tokens:,} "
                f"(cached: {gen.cached_tokens:,}) · "
                f"Output tokens: {gen.completion_tokens:,}"
            )

        # Execute
        try:
            with st.spinner("⚡ Running on Snowflake…"):
                df = run_query(safe_sql)
        except Exception as e:
            st.error("Query failed.")
            st.code(str(e), language="text")
            st.stop()

        render_results(df)

        # Track history
        history = st.session_state.setdefault("nl_history", [])
        history.insert(0, {
            "question": question,
            "sql": safe_sql,
            "rows": len(df),
            "tokens": gen.prompt_tokens + gen.completion_tokens,
        })
        st.session_state.nl_history = history[:10]


# ----------------------------------------------------------------------------
# MODE 2: Raw SQL
# ----------------------------------------------------------------------------
else:
    st.markdown(
        "Type a SQL query — results appear as a table and an auto-picked chart."
    )

    st.markdown("**🚀 Try a preset:**")
    preset_cols = st.columns(4)
    PRESETS = {
        "Revenue by category": """SELECT p.category_name, ROUND(SUM(o.net_sales)) AS revenue
FROM fct_orders o
JOIN dim_product p USING (product_id)
GROUP BY p.category_name
ORDER BY revenue DESC
LIMIT 10""",
        "Late % by shipping mode": """SELECT shipping_mode, ROUND(AVG(is_late_flag) * 100, 1) AS pct_late
FROM fct_orders
GROUP BY shipping_mode
ORDER BY pct_late DESC""",
        "Weekly order volume": """SELECT order_week, SUM(orders) AS orders
FROM agg_weekly_orders
GROUP BY order_week
ORDER BY order_week""",
        "Top regions by revenue": """SELECT region, ROUND(SUM(net_sales)) AS revenue
FROM fct_orders
GROUP BY region
ORDER BY revenue DESC
LIMIT 10""",
    }

    if "sql_editor" not in st.session_state:
        st.session_state.sql_editor = list(PRESETS.values())[0]

    for col, (label, sql) in zip(preset_cols, PRESETS.items()):
        if col.button(label, use_container_width=True):
            st.session_state.sql_editor = sql

    st.text_area(
        "SQL query",
        height=160,
        key="sql_editor",
        label_visibility="collapsed",
    )

    if st.button("▶️  Run query", type="primary"):
        sql = st.session_state.sql_editor.strip()
        if not sql:
            st.warning("Enter a SQL query first.")
            st.stop()
        try:
            with st.spinner("Running on Snowflake…"):
                df = run_query(sql)
        except Exception as e:
            st.error("Query failed.")
            st.code(str(e), language="text")
            st.stop()
        render_results(df)


# ----------------------------------------------------------------------------
# Recent questions panel
# ----------------------------------------------------------------------------
if "nl_history" in st.session_state and st.session_state.nl_history:
    st.divider()
    with st.expander("🕘 Recent questions"):
        for i, h in enumerate(st.session_state.nl_history, 1):
            st.markdown(f"**{i}.** {h['question']}")
            st.caption(f"{h['rows']:,} rows · {h['tokens']:,} tokens")
            st.code(h["sql"], language="sql")
