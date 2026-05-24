{{
    config(
        materialized='table'
    )
}}

-- Customer dimension with first-order date and cohort attributes.

WITH first_orders AS (
    SELECT
        customer_id,
        MIN(order_date)                       AS first_order_date,
        DATE_TRUNC('month', MIN(order_date))  AS cohort_month,
        DATE_TRUNC('quarter', MIN(order_date)) AS cohort_quarter
    FROM {{ ref('stg_orders') }}
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
FROM {{ ref('stg_customers') }} c
LEFT JOIN first_orders f USING (customer_id)
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY first_order_date) = 1
