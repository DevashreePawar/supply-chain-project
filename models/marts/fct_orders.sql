{{
    config(
        materialized='table'
    )
}}

-- Fact table. One row per order_item. The central table every analytical
-- query and the Tableau dashboard joins back to.

SELECT
    o.order_item_id,
    o.order_id,
    o.customer_id,
    o.product_id,

    -- date keys
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

FROM {{ ref('stg_orders') }} o
