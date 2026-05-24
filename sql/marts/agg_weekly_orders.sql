-- ============================================================================
-- marts/agg_weekly_orders.sql
-- Weekly aggregate by category. This is the table the forecasting notebook
-- reads from. Pre-aggregating in SQL keeps Python lean.
-- ============================================================================

CREATE OR REPLACE TABLE MARTS.AGG_WEEKLY_ORDERS AS
SELECT
    o.order_week,
    p.department_name,
    p.category_name,
    COUNT(DISTINCT o.order_id)              AS orders,
    SUM(o.quantity)                         AS units_sold,
    SUM(o.net_sales)                        AS revenue,
    SUM(o.profit)                           AS profit,
    AVG(o.is_late_flag) * 100               AS pct_late,
    AVG(o.shipping_delay_days)              AS avg_delay_days
FROM MARTS.FCT_ORDERS o
JOIN MARTS.DIM_PRODUCT p USING (product_id)
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;

SELECT MIN(order_week) AS first_week, MAX(order_week) AS last_week,
       COUNT(DISTINCT order_week) AS weeks,
       COUNT(DISTINCT category_name) AS categories
FROM MARTS.AGG_WEEKLY_ORDERS;
