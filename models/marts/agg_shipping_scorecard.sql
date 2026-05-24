{{
    config(
        materialized='table'
    )
}}

-- Scorecard for shipping mode x region combinations.
-- Feeds the "Shipping & Mode Performance" page of the Tableau dashboard.
-- Excludes noisy low-volume combos (< 50 line items).

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
FROM {{ ref('fct_orders') }}
GROUP BY 1, 2
HAVING COUNT(*) >= 50
ORDER BY revenue DESC
