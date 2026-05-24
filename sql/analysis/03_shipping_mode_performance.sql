-- ============================================================================
-- analysis/03_shipping_mode_performance.sql
-- BUSINESS QUESTION: Are some shipping modes systematically worse?
-- How much late-delivery cost are we eating per mode?
-- DEMONSTRATES: conditional aggregation, derived business metrics.
-- ============================================================================

SELECT
    shipping_mode,
    COUNT(*)                                            AS line_items,
    COUNT(DISTINCT order_id)                            AS orders,
    ROUND(SUM(net_sales), 0)                            AS revenue,
    ROUND(SUM(profit), 0)                               AS profit,
    ROUND(AVG(shipping_days_actual), 2)                 AS avg_actual_days,
    ROUND(AVG(shipping_days_scheduled), 2)              AS avg_scheduled_days,
    ROUND(AVG(shipping_delay_days), 2)                  AS avg_delay_days,
    ROUND(AVG(is_late_flag) * 100, 1)                   AS pct_late,
    -- Revenue at risk: revenue from late orders
    ROUND(
        SUM(CASE WHEN is_late_flag = 1 THEN net_sales ELSE 0 END), 0
    )                                                   AS revenue_from_late_orders,
    -- Estimated goodwill cost: assume 5% of late-order revenue is "at risk"
    -- of churn (a reasonable industry assumption for ops memos)
    ROUND(
        SUM(CASE WHEN is_late_flag = 1 THEN net_sales ELSE 0 END) * 0.05, 0
    )                                                   AS est_goodwill_cost
FROM MARTS.FCT_ORDERS
GROUP BY shipping_mode
ORDER BY revenue DESC;
