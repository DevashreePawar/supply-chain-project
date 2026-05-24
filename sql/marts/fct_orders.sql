-- ============================================================================
-- marts/fct_orders.sql
-- The fact table. One row per order_item. This is what every analytical query
-- and the Tableau dashboard joins back to.
-- ============================================================================

CREATE OR REPLACE TABLE MARTS.FCT_ORDERS AS
SELECT
    o.order_item_id,
    o.order_id,
    o.customer_id,
    o.product_id,

    -- date keys (join to dim_date if needed)
    o.order_date,
    o.order_week,
    o.shipping_ts,

    -- shipping
    o.shipping_mode,
    o.shipping_days_actual,
    o.shipping_days_scheduled,
    o.shipping_delay_days,
    o.delivery_status,
    o.is_late_flag,
    o.is_on_time_flag,
    o.late_delivery_risk_flag,

    -- money
    o.quantity,
    o.unit_price,
    o.line_discount,
    o.line_discount_rate,
    o.gross_sales,
    o.net_sales,
    o.profit,
    o.profit_ratio,

    -- geo
    o.region,
    o.country,
    o.state,
    o.market,
    o.order_status,
    o.customer_segment

FROM STAGING.STG_ORDERS o;

-- Sanity checks
SELECT
    COUNT(*)                            AS line_items,
    COUNT(DISTINCT order_id)            AS distinct_orders,
    COUNT(DISTINCT customer_id)         AS distinct_customers,
    ROUND(SUM(net_sales), 0)            AS total_net_sales,
    ROUND(SUM(profit), 0)               AS total_profit,
    ROUND(AVG(is_late_flag) * 100, 1)   AS pct_late
FROM MARTS.FCT_ORDERS;
