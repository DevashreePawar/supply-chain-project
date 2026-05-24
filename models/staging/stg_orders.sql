{{
    config(
        materialized='view'
    )
}}

-- Cleans the raw orders feed: casts dates, normalizes statuses, derives flags.
-- Grain: one row per order_item.

SELECT
    ORDER_ITEM_ID                                       AS order_item_id,
    ORDER_ID                                            AS order_id,
    ORDER_CUSTOMER_ID                                   AS customer_id,
    PRODUCT_CARD_ID                                     AS product_id,
    CATEGORY_ID                                         AS category_id,
    DEPARTMENT_ID                                       AS department_id,

    -- Dates: the CSV stores them as strings like "1/1/2018 0:00"
    TRY_TO_TIMESTAMP(ORDER_DATE,   'MM/DD/YYYY HH24:MI') AS order_ts,
    TRY_TO_TIMESTAMP(SHIPPING_DATE,'MM/DD/YYYY HH24:MI') AS shipping_ts,
    CAST(TRY_TO_TIMESTAMP(ORDER_DATE, 'MM/DD/YYYY HH24:MI') AS DATE)
                                                        AS order_date,
    DATE_TRUNC('week',
        TRY_TO_TIMESTAMP(ORDER_DATE, 'MM/DD/YYYY HH24:MI'))
                                                        AS order_week,

    -- Shipping & delivery
    SHIPPING_MODE                                       AS shipping_mode,
    DAYS_FOR_SHIPPING_REAL                              AS shipping_days_actual,
    DAYS_FOR_SHIPMENT_SCHEDULED                         AS shipping_days_scheduled,
    DAYS_FOR_SHIPPING_REAL - DAYS_FOR_SHIPMENT_SCHEDULED AS shipping_delay_days,
    DELIVERY_STATUS                                     AS delivery_status,
    LATE_DELIVERY_RISK                                  AS late_delivery_risk_flag,

    -- Canonical late flag (uses the is_late() macro from macros/is_late.sql).
    -- This is the ONLY way new code should compute "is this order late?".
    {{ is_late('DELIVERY_STATUS') }}                    AS is_late_flag,

    -- Day-math version, kept for shipping-SLA analyses where the question
    -- is "did we ship within the scheduled window?" — NOT for "is late?".
    -- See macros/is_late.sql docstring for why these are separate flags.
    CASE WHEN DAYS_FOR_SHIPPING_REAL <= DAYS_FOR_SHIPMENT_SCHEDULED THEN 1
         ELSE 0 END                                     AS is_on_time_flag,

    -- Money
    ORDER_ITEM_QUANTITY                                 AS quantity,
    ORDER_ITEM_PRODUCT_PRICE                            AS unit_price,
    ORDER_ITEM_DISCOUNT                                 AS line_discount,
    ORDER_ITEM_DISCOUNT_RATE                            AS line_discount_rate,
    SALES                                               AS gross_sales,
    ORDER_ITEM_TOTAL                                    AS net_sales,
    BENEFIT_PER_ORDER                                   AS profit,
    ORDER_ITEM_PROFIT_RATIO                             AS profit_ratio,

    -- Status & geo
    ORDER_STATUS                                        AS order_status,
    ORDER_REGION                                        AS region,
    ORDER_COUNTRY                                       AS country,
    ORDER_STATE                                         AS state,
    ORDER_CITY                                          AS city,
    MARKET                                              AS market,
    CUSTOMER_SEGMENT                                    AS customer_segment

FROM {{ source('raw', 'dataco_orders') }}
WHERE ORDER_DATE IS NOT NULL
  AND TRY_TO_TIMESTAMP(ORDER_DATE, 'MM/DD/YYYY HH24:MI') IS NOT NULL
