{{
    config(
        materialized='view'
    )
}}

-- Deduplicates product info from the wide raw table.

SELECT DISTINCT
    PRODUCT_CARD_ID         AS product_id,
    PRODUCT_NAME            AS product_name,
    PRODUCT_PRICE           AS list_price,
    PRODUCT_STATUS          AS status_flag,
    CATEGORY_ID             AS category_id,
    CATEGORY_NAME           AS category_name,
    DEPARTMENT_ID           AS department_id,
    DEPARTMENT_NAME         AS department_name
FROM {{ source('raw', 'dataco_orders') }}
WHERE PRODUCT_CARD_ID IS NOT NULL
