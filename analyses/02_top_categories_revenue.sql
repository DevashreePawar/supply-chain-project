-- BUSINESS QUESTION: Which categories drive revenue and profit?
-- Which ones are growing or shrinking year-over-year?
-- DEMONSTRATES: window functions (RANK, % of total), conditional aggregation,
-- year-over-year comparison.

WITH category_yearly AS (
    SELECT
        p.category_name,
        EXTRACT(year FROM o.order_date) AS year,
        SUM(o.net_sales)                AS revenue,
        SUM(o.profit)                   AS profit,
        COUNT(DISTINCT o.order_id)      AS orders
    FROM {{ ref('fct_orders') }} o
    JOIN {{ ref('dim_product') }} p USING (product_id)
    GROUP BY 1, 2
),
pivoted AS (
    SELECT
        category_name,
        SUM(CASE WHEN year = 2016 THEN revenue ELSE 0 END) AS rev_2016,
        SUM(CASE WHEN year = 2017 THEN revenue ELSE 0 END) AS rev_2017,
        SUM(revenue)                                       AS total_revenue,
        SUM(profit)                                        AS total_profit
    FROM category_yearly
    GROUP BY category_name
)
SELECT
    category_name,
    total_revenue,
    total_profit,
    ROUND(total_profit / NULLIF(total_revenue, 0) * 100, 2)  AS profit_margin_pct,
    RANK() OVER (ORDER BY total_revenue DESC)               AS revenue_rank,
    ROUND(
        total_revenue / SUM(total_revenue) OVER () * 100, 2
    )                                                       AS pct_of_total_revenue,
    rev_2016,
    rev_2017,
    ROUND(
        (rev_2017 - rev_2016) / NULLIF(rev_2016, 0) * 100, 2
    )                                                       AS yoy_growth_pct
FROM pivoted
ORDER BY total_revenue DESC
LIMIT 15
