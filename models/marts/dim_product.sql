{{
    config(
        materialized='table'
    )
}}

-- Product dimension. Deduplicates rows in staging using ROW_NUMBER + QUALIFY
-- (Snowflake-specific). Adds a price band derived attribute.

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
FROM {{ ref('stg_products') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY list_price DESC) = 1
