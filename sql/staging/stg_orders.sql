-- ============================================================================
-- staging/stg_orders.sql
-- Cleans the raw orders feed: casts dates, normalizes statuses, derives flags.
-- One row per order_item (the grain of the raw file).
-- ============================================================================

CREATE OR REPLACE VIEW STAGING.STG_ORDERS AS
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
    TRY_TO_DATE(TRY_TO_TIMESTAMP(ORDER_DATE, 'MM/DD/YYYY HH24:MI'))
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
    -- NOTE: These two flags use DIFFERENT logic and will disagree on some rows.
    -- is_late_flag   → derived from the DELIVERY_STATUS string in the raw data.
    --                  Use this for memo/dashboard numbers; it matches the DataCo
    --                  dataset's own classification and is what the analysis queries
    --                  (03_shipping_mode_performance.sql, etc.) are built on.
    -- is_on_time_flag → derived from the day arithmetic (actual vs scheduled).
    --                  Use this for time-math-based analysis only.
    -- Do NOT mix the two flags in the same query or you will get contradictory rates.
    CASE WHEN DELIVERY_STATUS = 'Late delivery' THEN 1 ELSE 0 END
                                                        AS is_late_flag,
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

FROM RAW.DATACO_ORDERS
WHERE ORDER_DATE IS NOT NULL
  AND TRY_TO_TIMESTAMP(ORDER_DATE, 'MM/DD/YYYY HH24:MI') IS NOT NULL;

-- Sanity checks
SELECT
    COUNT(*)                AS row_count,
    COUNT(DISTINCT order_id) AS distinct_orders,
    MIN(order_date)         AS first_order,
    MAX(order_date)         AS last_order,
    SUM(is_late_flag)       AS late_orders,
    ROUND(AVG(is_late_flag) * 100, 1) AS pct_late
FROM STAGING.STG_ORDERS;
