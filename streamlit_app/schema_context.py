"""
Reads dbt's manifest.json and produces a compact schema description string
suitable for passing to an LLM as system-prompt context.

The descriptions in the output come straight from your _staging.yml / _marts.yml
YAML files. Updating those files updates the LLM's understanding — for free.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# Project root (one level up from streamlit_app/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_PATH = _PROJECT_ROOT / "target" / "manifest.json"
_CATALOG_PATH = _PROJECT_ROOT / "target" / "catalog.json"

# Only expose these schemas to the LLM. We intentionally exclude RAW to
# discourage the LLM from generating queries against the wide raw table.
_ALLOWED_SCHEMAS = {"DBT_DEV_MARTS", "DBT_DEV_STAGING", "DBT_CI"}

# Map model name → friendly hint when descriptions are missing.
_FALLBACK_HINTS = {
    "fct_orders": "Fact table. One row per order_item. 180,519 rows.",
    "dim_customer": "Customer dimension (~20.6K customers) with cohort dates.",
    "dim_product": "Product dimension (~118 products) with price_band.",
    "dim_date": "Date dimension (1,500 days from 2014-12-29).",
    "agg_weekly_orders": "Weekly aggregate by category. Feeds the forecasting notebook.",
    "agg_shipping_scorecard": "Shipping mode × region scorecard.",
}


@lru_cache(maxsize=1)
def _load_manifest() -> dict:
    if not _MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"dbt manifest not found at {_MANIFEST_PATH}. "
            f"Run `./run-dbt.sh docs generate` first."
        )
    with _MANIFEST_PATH.open() as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    """catalog.json has the ACTUAL columns from Snowflake (manifest.json has
    only the columns we documented in YAML). Merging both gives full coverage."""
    if not _CATALOG_PATH.exists():
        return {}
    with _CATALOG_PATH.open() as f:
        return json.load(f)


def _catalog_columns_for(unique_id: str) -> dict[str, str]:
    """Return {column_name: data_type} dict from catalog.json for a given model."""
    catalog = _load_catalog()
    node = catalog.get("nodes", {}).get(unique_id, {})
    return {
        col_name.lower(): info.get("type", "")
        for col_name, info in node.get("columns", {}).items()
    }


def _format_model(node: dict) -> str | None:
    """Format one dbt model as a TABLE block for the LLM context.

    Merges two sources:
      - manifest.json columns (descriptions we wrote in YAML)
      - catalog.json columns (actual columns from Snowflake)
    Any column in the warehouse is exposed; descriptions added where we have them.
    """
    schema = node.get("schema", "").upper()
    if schema not in _ALLOWED_SCHEMAS:
        return None

    name = node["name"]
    description = (
        node.get("description")
        or _FALLBACK_HINTS.get(name)
        or "(no description provided)"
    )

    # Merge sources: catalog is the authoritative column list; manifest adds descriptions
    catalog_cols = _catalog_columns_for(node["unique_id"])
    documented = {k.lower(): v for k, v in node.get("columns", {}).items()}

    lines = [f"TABLE: {name}", f"  -- {description.strip()}"]

    if not catalog_cols:
        # Catalog wasn't generated yet — fall back to documented columns only
        catalog_cols = {k: "" for k in documented}

    for col_name, col_type in catalog_cols.items():
        doc = documented.get(col_name, {})
        col_desc = (doc.get("description") or "").strip().replace("\n", " ")
        type_str = f" [{col_type.lower()}]" if col_type else ""
        desc_str = f" — {col_desc}" if col_desc else ""
        lines.append(f"  • {col_name}{type_str}{desc_str}")

    return "\n".join(lines)


@lru_cache(maxsize=1)
def build_schema_context() -> str:
    """Build the full schema description string for the LLM system prompt."""
    manifest = _load_manifest()
    nodes = manifest.get("nodes", {})

    # Order: facts → dims → aggregates → staging.  Helps the LLM prioritize
    # the right tables.
    priority = {"fct_": 0, "dim_": 1, "agg_": 2, "stg_": 3}

    model_nodes = [
        node
        for node in nodes.values()
        if node.get("resource_type") == "model"
    ]
    model_nodes.sort(
        key=lambda n: (
            min((rank for prefix, rank in priority.items() if n["name"].startswith(prefix)), default=99),
            n["name"],
        )
    )

    blocks = []
    for node in model_nodes:
        block = _format_model(node)
        if block:
            blocks.append(block)

    return "\n\n".join(blocks)


def get_table_names() -> list[str]:
    """List of fully-qualified table names the LLM is allowed to use."""
    manifest = _load_manifest()
    return [
        node["name"]
        for node in manifest.get("nodes", {}).values()
        if node.get("resource_type") == "model"
        and node.get("schema", "").upper() in _ALLOWED_SCHEMAS
    ]
