-- BUSINESS QUESTION: Where geographically do we have ops problems?
-- Which regions punch above their weight on revenue vs. complaints?
-- DEMONSTRATES: window function ranking, dense rank vs rank, ratios.

WITH region_metrics AS (
    SELECT
        region,
        market,
        COUNT(DISTINCT order_id)            AS orders,
        SUM(net_sales)                      AS revenue,
        SUM(profit)                         AS profit,
        AVG(is_late_flag) * 100             AS pct_late,
        AVG(shipping_delay_days)            AS avg_delay,
        COUNT(DISTINCT customer_id)         AS customers
    FROM {{ ref('fct_orders') }}
    GROUP BY region, market
)
SELECT
    region,
    market,
    orders,
    ROUND(revenue, 0)                                       AS revenue,
    ROUND(profit, 0)                                        AS profit,
    customers,
    ROUND(revenue / NULLIF(customers, 0), 2)                AS revenue_per_customer,
    ROUND(pct_late, 1)                                      AS pct_late,
    ROUND(avg_delay, 2)                                     AS avg_delay_days,
    RANK() OVER (ORDER BY revenue DESC)                     AS rank_by_revenue,
    RANK() OVER (ORDER BY pct_late DESC)                    AS rank_by_late_rate,
    CASE
        WHEN RANK() OVER (ORDER BY revenue DESC) <= 5
         AND pct_late > 50
        THEN 'PRIORITY: high revenue + high late rate'
        WHEN pct_late > 60
        THEN 'WATCH: very high late rate'
        ELSE NULL
    END                                                     AS flag
FROM region_metrics
ORDER BY revenue DESC
