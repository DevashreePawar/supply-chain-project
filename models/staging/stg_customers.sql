{{
    config(
        materialized='view'
    )
}}

-- Deduplicates customer attributes. PII fields (email, password, street) are
-- deliberately excluded — we do not need them and excluding them is good
-- data hygiene.

SELECT DISTINCT
    CUSTOMER_ID         AS customer_id,
    CUSTOMER_SEGMENT    AS customer_segment,
    CUSTOMER_CITY       AS customer_city,
    CUSTOMER_STATE      AS customer_state,
    CUSTOMER_COUNTRY    AS customer_country,
    CUSTOMER_ZIPCODE    AS customer_zipcode
FROM {{ source('raw', 'dataco_orders') }}
WHERE CUSTOMER_ID IS NOT NULL
