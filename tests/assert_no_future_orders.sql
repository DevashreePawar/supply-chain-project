-- ============================================================================
-- TEST: No order_date should be in the future.
--
-- WHY THIS MATTERS:
-- A common bug class in data pipelines: dates getting parsed wrong (e.g.,
-- "01/02/2026" interpreted as MM/DD vs DD/MM, or '0000' year padded to '2000'
-- becoming '20000'). These bugs sail through type checks but produce
-- order_dates in year 9999 or other obvious nonsense.
--
-- This test catches that the moment it would happen on a future data load.
--
-- HOW IT WORKS:
-- Returns any row where order_date is later than CURRENT_DATE.
-- Test passes when zero rows are returned.
-- ============================================================================

SELECT
    order_item_id,
    order_id,
    order_date
FROM {{ ref('fct_orders') }}
WHERE order_date > CURRENT_DATE
LIMIT 10
