-- ============================================================================
-- marts/dim_product.sql
-- Cleaned product dimension.
-- ============================================================================

CREATE OR REPLACE TABLE MARTS.DIM_PRODUCT AS
SELECT
    product_id,
    product_name,
    list_price,
    category_id,
    category_name,
    department_id,
    department_name,
    CASE
        WHEN list_price <  50  THEN 'Low'
        WHEN list_price < 200  THEN 'Mid'
        ELSE 'High'
    END AS price_band
FROM STAGING.STG_PRODUCTS
QUALIFY ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY list_price DESC) = 1;
-- QUALIFY is a Snowflake-specific way to deduplicate after window functions.
-- On Postgres, wrap in a subquery using ROW_NUMBER() ... WHERE rn = 1.

SELECT COUNT(*) AS rows, COUNT(DISTINCT product_id) AS distinct_products
FROM MARTS.DIM_PRODUCT;
