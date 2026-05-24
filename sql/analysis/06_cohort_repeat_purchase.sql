-- ============================================================================
-- analysis/06_cohort_repeat_purchase.sql
-- BUSINESS QUESTION: Are customers acquired in 2017 sticking around?
-- How does repeat-purchase rate compare across acquisition cohorts?
-- DEMONSTRATES: cohort analysis pattern, multiple CTEs, joining facts to dims.
-- This is the most "data-science-y" of the analytical queries — including it
-- shows you can do customer analytics, not just operations.
-- ============================================================================

WITH customer_first_quarter AS (
    SELECT
        customer_id,
        DATE_TRUNC('quarter', MIN(order_date)) AS cohort_quarter
    FROM MARTS.FCT_ORDERS
    GROUP BY customer_id
),
customer_activity AS (
    SELECT
        o.customer_id,
        c.cohort_quarter,
        DATE_TRUNC('quarter', o.order_date)             AS activity_quarter,
        DATEDIFF('quarter', c.cohort_quarter, DATE_TRUNC('quarter', o.order_date))
                                                        AS quarter_offset
    FROM MARTS.FCT_ORDERS o
    JOIN customer_first_quarter c USING (customer_id)
),
cohort_sizes AS (
    SELECT cohort_quarter, COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_first_quarter
    GROUP BY cohort_quarter
),
cohort_activity AS (
    SELECT
        cohort_quarter,
        quarter_offset,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM customer_activity
    GROUP BY cohort_quarter, quarter_offset
)
SELECT
    a.cohort_quarter,
    s.cohort_size,
    a.quarter_offset,
    a.active_customers,
    ROUND(a.active_customers::FLOAT / s.cohort_size * 100, 1) AS retention_pct
FROM cohort_activity a
JOIN cohort_sizes s USING (cohort_quarter)
WHERE a.quarter_offset <= 6
ORDER BY a.cohort_quarter, a.quarter_offset;
