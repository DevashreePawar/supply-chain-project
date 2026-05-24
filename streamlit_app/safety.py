"""
SQL safety guards for the LLM-generated query layer.

Defense in depth:
  1. SELECT-only enforcement       — reject anything that isn't a SELECT
  2. Keyword blocklist             — reject DDL / DML keywords explicitly
  3. Single-statement enforcement  — reject semicolon-chained queries
  4. Forced LIMIT clause           — add LIMIT 5000 if missing

These run AFTER the LLM returns SQL and BEFORE we send it to Snowflake.
Even if the LLM is jailbroken, malicious SQL cannot reach the warehouse.
"""

from __future__ import annotations

import re

# Keywords that are NEVER allowed in LLM-generated SQL.
# Whole-word match, case-insensitive.
_BLOCKED_KEYWORDS = {
    "DROP",
    "DELETE",
    "TRUNCATE",
    "UPDATE",
    "INSERT",
    "MERGE",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXECUTE",
    "CALL",
    "USE",
    "COPY",
    "PUT",
    "REMOVE",
    "UNDROP",
}

_DEFAULT_LIMIT = 5000


class UnsafeSQLError(ValueError):
    """Raised when LLM-generated SQL violates our safety guards."""


def _strip_comments_and_strings(sql: str) -> str:
    """Remove /* */ and -- comments, and string literals, so the keyword
    blocklist can't be bypassed by hiding DROP in a comment or string."""
    # Remove /* ... */ block comments
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Remove -- line comments
    sql = re.sub(r"--[^\n]*", " ", sql)
    # Remove '...' and "..." string literals
    sql = re.sub(r"'(?:''|[^'])*'", " ", sql)
    sql = re.sub(r'"(?:""|[^"])*"', " ", sql)
    return sql


def validate(sql: str) -> str:
    """Validate LLM-generated SQL and return a safe version with LIMIT applied.

    Raises UnsafeSQLError if the query is rejected.
    """
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise UnsafeSQLError("Empty query.")

    scrubbed = _strip_comments_and_strings(sql).upper()

    # Reject multiple statements (e.g. `SELECT ...; DROP TABLE x;`)
    if ";" in scrubbed:
        raise UnsafeSQLError(
            "Query contains multiple statements. Only single SELECT queries are allowed."
        )

    # Must start with SELECT or WITH
    first_token = scrubbed.lstrip("(").split(None, 1)[0] if scrubbed.lstrip("(") else ""
    if first_token not in ("SELECT", "WITH"):
        raise UnsafeSQLError(
            f"Only SELECT/WITH queries are allowed. Got: {first_token or '?'}"
        )

    # Blocklist whole-word match
    for kw in _BLOCKED_KEYWORDS:
        # \b matches word boundaries — so "INSERT" wouldn't match "INSERTED_AT"
        if re.search(rf"\b{kw}\b", scrubbed):
            raise UnsafeSQLError(f"Query contains forbidden keyword: {kw}")

    # Auto-add LIMIT if missing (don't override user-provided LIMIT)
    if not re.search(r"\bLIMIT\s+\d+\b", scrubbed):
        sql = f"{sql}\nLIMIT {_DEFAULT_LIMIT}"

    return sql
