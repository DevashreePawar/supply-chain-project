-- ============================================================================
-- staging/stg_customers.sql
-- Deduplicates customer attributes. PII fields (email, password, street) are
-- deliberately excluded — we do not need them and excluding them is good
-- data hygiene to demonstrate on the project.
-- ============================================================================

CREATE OR REPLACE VIEW STAGING.STG_CUSTOMERS AS
SELECT DISTINCT
    CUSTOMER_ID         AS customer_id,
    CUSTOMER_SEGMENT    AS customer_segment,
    CUSTOMER_CITY       AS customer_city,
    CUSTOMER_STATE      AS customer_state,
    CUSTOMER_COUNTRY    AS customer_country,
    CUSTOMER_ZIPCODE    AS customer_zipcode
FROM RAW.DATACO_ORDERS
WHERE CUSTOMER_ID IS NOT NULL;

-- Sanity check
SELECT COUNT(*) AS distinct_customers,
       COUNT(DISTINCT customer_segment) AS segments,
       COUNT(DISTINCT customer_state)   AS states
FROM STAGING.STG_CUSTOMERS;
