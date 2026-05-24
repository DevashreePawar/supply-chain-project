-- ============================================================================
-- TEST: Revenue must reconcile between fct_orders and agg_weekly_orders.
--
-- WHY THIS MATTERS:
-- If our aggregation in agg_weekly_orders.sql ever introduces a join bug
-- (fan-out, missing rows, wrong GROUP BY), the totals will silently drift.
-- This test catches that the moment it happens.
--
-- HOW IT WORKS:
-- We compute total net_sales two different ways and compare. They must
-- match within $1 (tiny rounding tolerance).
--
-- FAILURE LOOKS LIKE:
-- Test returns one row with the two totals — easy to investigate.
-- ============================================================================

WITH fct_total AS (
    SELECT ROUND(SUM(net_sales), 2) AS total_net_sales
    FROM {{ ref('fct_orders') }}
),
agg_total AS (
    SELECT ROUND(SUM(net_sales), 2) AS total_net_sales
    FROM {{ ref('agg_weekly_orders') }}
)
SELECT
    fct_total.total_net_sales AS fct_orders_total,
    agg_total.total_net_sales AS agg_weekly_orders_total,
    ABS(fct_total.total_net_sales - agg_total.total_net_sales) AS difference
FROM fct_total, agg_total
WHERE ABS(fct_total.total_net_sales - agg_total.total_net_sales) > 1
