{{
    config(
        materialized='table'
    )
}}

-- Weekly aggregate by category. This is the table the forecasting notebook
-- reads from (pre-aggregating in SQL keeps Python lean).

SELECT
    o.order_week,
    p.department_name,
    p.category_name,
    p.category_id,
    COUNT(DISTINCT o.order_id)              AS orders,
    SUM(o.quantity)                         AS units_sold,
    SUM(o.gross_sales)                      AS gross_sales,
    SUM(o.net_sales)                        AS net_sales,
    SUM(o.profit)                           AS profit,
    AVG(o.is_late_flag) * 100               AS pct_late,
    AVG(o.shipping_delay_days)              AS avg_delay_days
FROM {{ ref('fct_orders') }} o
JOIN {{ ref('dim_product') }} p USING (product_id)
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3
