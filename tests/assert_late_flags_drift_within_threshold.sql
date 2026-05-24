-- ============================================================================
-- TEST: is_late_flag and is_on_time_flag must agree on at least 70% of rows.
--
-- WHY THIS MATTERS:
-- These two flags use different logic (DELIVERY_STATUS string vs day math)
-- and they DO disagree on some rows in the DataCo dataset — this is a known
-- and documented data quality issue (see macros/is_late.sql docstring).
--
-- We don't fail on ANY disagreement (that would always fail). We fail only
-- if agreement drops below 95% — a real signal that something upstream changed.
--
-- HOW IT WORKS:
-- "Agreement" = both flags say late, OR both say on-time.
-- We compute % agreement and fail if it falls below 95%.
--
-- CURRENT BASELINE (DataCo dataset): 97.55% agreement (4,423 of 180,519 disagree).
-- ============================================================================

WITH flag_comparison AS (
    SELECT
        COUNT(*) AS total_rows,
        SUM(CASE
            WHEN is_late_flag = 1 AND is_on_time_flag = 0 THEN 1   -- both say "late"
            WHEN is_late_flag = 0 AND is_on_time_flag = 1 THEN 1   -- both say "on time"
            ELSE 0
        END) AS agreeing_rows
    FROM {{ ref('fct_orders') }}
),
pct_agreement AS (
    SELECT
        total_rows,
        agreeing_rows,
        ROUND(agreeing_rows::FLOAT / total_rows * 100, 2) AS pct_agreement
    FROM flag_comparison
)
SELECT *
FROM pct_agreement
WHERE pct_agreement < 95
