-- BUSINESS QUESTION: How is on-time delivery trending? Are we improving?
-- DEMONSTRATES: window functions (4-week moving average), DATE_TRUNC,
-- conditional aggregation.

WITH weekly AS (
    SELECT
        order_week,
        COUNT(*)                                AS orders,
        SUM(is_on_time_flag)                    AS on_time_orders,
        ROUND(AVG(is_on_time_flag) * 100, 2)    AS pct_on_time,
        ROUND(AVG(shipping_delay_days), 2)      AS avg_delay
    FROM {{ ref('fct_orders') }}
    GROUP BY order_week
)
SELECT
    order_week,
    orders,
    pct_on_time,
    avg_delay,
    ROUND(
        AVG(pct_on_time) OVER (
            ORDER BY order_week
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ), 2
    ) AS pct_on_time_4w_ma,
    pct_on_time - LAG(pct_on_time, 1) OVER (ORDER BY order_week) AS wow_delta
FROM weekly
ORDER BY order_week
