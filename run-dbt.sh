#!/usr/bin/env bash
# ============================================================================
# run-dbt.sh
# Loads environment variables from .env, then runs dbt with all arguments
# passed through. Always uses the project-local profiles.yml.
#
# Examples:
#   ./run-dbt.sh debug
#   ./run-dbt.sh run
#   ./run-dbt.sh test
#   ./run-dbt.sh docs generate
#   ./run-dbt.sh run --select staging
# ============================================================================

set -euo pipefail

# Load .env if present
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
else
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in values." >&2
    exit 1
fi

# Use venv's dbt if available, else system dbt
DBT_BIN=".venv/bin/dbt"
if [ ! -x "$DBT_BIN" ]; then
    DBT_BIN="dbt"
fi

# Always read profiles.yml from the project directory (not ~/.dbt/)
export DBT_PROFILES_DIR="$(pwd)"

exec "$DBT_BIN" "$@"
