-- ============================================================================
-- analysis/04_customer_segment_profitability.sql
-- BUSINESS QUESTION: Which customer segments drive disproportionate profit?
-- Are we serving low-margin segments at high operational cost?
-- DEMONSTRATES: CTE composition, derived ratios, cumulative window functions.
-- ============================================================================

WITH segment_metrics AS (
    SELECT
        customer_segment,
        COUNT(DISTINCT customer_id)         AS customers,
        COUNT(DISTINCT order_id)            AS orders,
        SUM(net_sales)                      AS revenue,
        SUM(profit)                         AS profit,
        AVG(net_sales)                      AS avg_order_value,
        AVG(is_late_flag) * 100             AS pct_late,
        AVG(profit_ratio) * 100             AS avg_profit_margin
    FROM MARTS.FCT_ORDERS
    GROUP BY customer_segment
)
SELECT
    customer_segment,
    customers,
    orders,
    ROUND(orders::FLOAT / customers, 2)                     AS orders_per_customer,
    ROUND(revenue, 0)                                       AS revenue,
    ROUND(profit, 0)                                        AS profit,
    ROUND(avg_order_value, 2)                               AS aov,
    ROUND(pct_late, 1)                                      AS pct_late,
    ROUND(avg_profit_margin, 1)                             AS profit_margin_pct,
    -- Each segment's contribution to total profit
    ROUND(profit / SUM(profit) OVER () * 100, 1)            AS pct_of_total_profit,
    -- Cumulative profit when sorted high to low (Pareto)
    ROUND(
        SUM(profit) OVER (ORDER BY profit DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / SUM(profit) OVER () * 100, 1
    )                                                       AS cumulative_pct_of_profit
FROM segment_metrics
ORDER BY profit DESC;
