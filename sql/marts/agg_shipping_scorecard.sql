-- ============================================================================
-- marts/agg_shipping_scorecard.sql
-- Scorecard for shipping mode x region combinations.
-- Feeds the "Supplier & Shipping Performance" page of the Tableau dashboard.
-- ============================================================================

CREATE OR REPLACE TABLE MARTS.AGG_SHIPPING_SCORECARD AS
SELECT
    shipping_mode,
    region,
    COUNT(*)                                            AS line_items,
    COUNT(DISTINCT order_id)                            AS orders,
    SUM(net_sales)                                      AS revenue,
    ROUND(AVG(shipping_days_actual), 2)                 AS avg_shipping_days,
    ROUND(AVG(shipping_days_scheduled), 2)              AS avg_scheduled_days,
    ROUND(AVG(shipping_delay_days), 2)                  AS avg_delay_days,
    ROUND(AVG(is_late_flag) * 100, 1)                   AS pct_late,
    ROUND(AVG(is_on_time_flag) * 100, 1)                AS pct_on_time
FROM MARTS.FCT_ORDERS
GROUP BY 1, 2
HAVING COUNT(*) >= 50         -- exclude noisy low-volume combos
ORDER BY revenue DESC;

SELECT * FROM MARTS.AGG_SHIPPING_SCORECARD LIMIT 20;
