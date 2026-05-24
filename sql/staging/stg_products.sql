-- ============================================================================
-- staging/stg_products.sql
-- Deduplicates product info from the wide raw table.
-- ============================================================================

CREATE OR REPLACE VIEW STAGING.STG_PRODUCTS AS
SELECT DISTINCT
    PRODUCT_CARD_ID         AS product_id,
    PRODUCT_NAME            AS product_name,
    PRODUCT_PRICE           AS list_price,
    PRODUCT_STATUS          AS status_flag,
    CATEGORY_ID             AS category_id,
    CATEGORY_NAME           AS category_name,
    DEPARTMENT_ID           AS department_id,
    DEPARTMENT_NAME         AS department_name
FROM RAW.DATACO_ORDERS
WHERE PRODUCT_CARD_ID IS NOT NULL;

-- Sanity check
SELECT COUNT(*) AS distinct_products,
       COUNT(DISTINCT category_id) AS categories,
       COUNT(DISTINCT department_id) AS departments
FROM STAGING.STG_PRODUCTS;
