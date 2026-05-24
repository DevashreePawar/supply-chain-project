-- ============================================================================
-- marts/dim_customer.sql
-- Customer dim with first-order date (for cohort analysis).
-- ============================================================================

CREATE OR REPLACE TABLE MARTS.DIM_CUSTOMER AS
WITH first_orders AS (
    SELECT
        customer_id,
        MIN(order_date)                     AS first_order_date,
        DATE_TRUNC('month', MIN(order_date)) AS cohort_month,
        DATE_TRUNC('quarter', MIN(order_date)) AS cohort_quarter
    FROM STAGING.STG_ORDERS
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    c.customer_segment,
    c.customer_city,
    c.customer_state,
    c.customer_country,
    f.first_order_date,
    f.cohort_month,
    f.cohort_quarter
FROM STAGING.STG_CUSTOMERS c
LEFT JOIN first_orders f USING (customer_id)
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY first_order_date) = 1;

SELECT COUNT(*) AS rows, COUNT(DISTINCT customer_id) AS distinct_customers
FROM MARTS.DIM_CUSTOMER;
