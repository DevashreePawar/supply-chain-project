-- ============================================================================
-- 00_load_data.sql
-- Creates the raw schema and loads DataCo CSV.
-- Works on Snowflake. Postgres notes inline.
-- ============================================================================

-- ----- SNOWFLAKE VERSION -----------------------------------------------------

CREATE DATABASE IF NOT EXISTS SUPPLY_CHAIN;
USE DATABASE SUPPLY_CHAIN;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS MARTS;

USE SCHEMA RAW;

-- Raw landing table. Column names match the DataCo CSV exactly (with spaces
-- replaced by underscores, since most SQL engines don't love spaces).
CREATE OR REPLACE TABLE DATACO_ORDERS (
    TYPE                              VARCHAR,
    DAYS_FOR_SHIPPING_REAL            INTEGER,
    DAYS_FOR_SHIPMENT_SCHEDULED       INTEGER,
    BENEFIT_PER_ORDER                 FLOAT,
    SALES_PER_CUSTOMER                FLOAT,
    DELIVERY_STATUS                   VARCHAR,
    LATE_DELIVERY_RISK                INTEGER,
    CATEGORY_ID                       INTEGER,
    CATEGORY_NAME                     VARCHAR,
    CUSTOMER_CITY                     VARCHAR,
    CUSTOMER_COUNTRY                  VARCHAR,
    CUSTOMER_EMAIL                    VARCHAR,
    CUSTOMER_FNAME                    VARCHAR,
    CUSTOMER_ID                       INTEGER,
    CUSTOMER_LNAME                    VARCHAR,
    CUSTOMER_PASSWORD                 VARCHAR,
    CUSTOMER_SEGMENT                  VARCHAR,
    CUSTOMER_STATE                    VARCHAR,
    CUSTOMER_STREET                   VARCHAR,
    CUSTOMER_ZIPCODE                  VARCHAR,
    DEPARTMENT_ID                     INTEGER,
    DEPARTMENT_NAME                   VARCHAR,
    LATITUDE                          FLOAT,
    LONGITUDE                         FLOAT,
    MARKET                            VARCHAR,
    ORDER_CITY                        VARCHAR,
    ORDER_COUNTRY                     VARCHAR,
    ORDER_CUSTOMER_ID                 INTEGER,
    ORDER_DATE                        VARCHAR,   -- cast to TIMESTAMP in staging
    ORDER_ID                          INTEGER,
    ORDER_ITEM_CARDPROD_ID            INTEGER,
    ORDER_ITEM_DISCOUNT               FLOAT,
    ORDER_ITEM_DISCOUNT_RATE          FLOAT,
    ORDER_ITEM_ID                     INTEGER,
    ORDER_ITEM_PRODUCT_PRICE          FLOAT,
    ORDER_ITEM_PROFIT_RATIO           FLOAT,
    ORDER_ITEM_QUANTITY               INTEGER,
    SALES                             FLOAT,
    ORDER_ITEM_TOTAL                  FLOAT,
    ORDER_PROFIT_PER_ORDER            FLOAT,
    ORDER_REGION                      VARCHAR,
    ORDER_STATE                       VARCHAR,
    ORDER_STATUS                      VARCHAR,
    ORDER_ZIPCODE                     VARCHAR,
    PRODUCT_CARD_ID                   INTEGER,
    PRODUCT_CATEGORY_ID               INTEGER,
    PRODUCT_DESCRIPTION               VARCHAR,
    PRODUCT_IMAGE                     VARCHAR,
    PRODUCT_NAME                      VARCHAR,
    PRODUCT_PRICE                     FLOAT,
    PRODUCT_STATUS                    INTEGER,
    SHIPPING_DATE                     VARCHAR,   -- cast to TIMESTAMP in staging
    SHIPPING_MODE                     VARCHAR
);

-- Load steps (run in Snowflake UI):
--   1. Right-click DATACO_ORDERS table → "Load Data"
--   2. Select your CSV from data/DataCoSupplyChainDataset.csv
--   3. Use a CSV file format with:
--        - Field delimiter: comma
--        - Skip header: 1
--        - Field enclosed by: double quotes
--        - Encoding: latin1 (the file has non-utf8 characters)
--   4. Click Load.

-- Quick sanity check
SELECT COUNT(*) AS row_count FROM DATACO_ORDERS;
-- Expected: ~180,519 rows

SELECT MIN(ORDER_DATE) AS earliest, MAX(ORDER_DATE) AS latest
FROM DATACO_ORDERS;
-- Expected date range: 2015-01-01 to 2018-01-31 (approximately)


-- ----- POSTGRES VERSION (if you skip Snowflake) -----------------------------
-- Replace the CREATE DATABASE / USE DATABASE / CREATE SCHEMA syntax with:
--
--   CREATE DATABASE supply_chain;
--   \c supply_chain
--   CREATE SCHEMA raw;
--   CREATE SCHEMA staging;
--   CREATE SCHEMA marts;
--
-- Then use the same CREATE TABLE above (Postgres accepts identical syntax).
-- Load with: \COPY raw.dataco_orders FROM 'data/DataCoSupplyChainDataset.csv'
--           WITH (FORMAT csv, HEADER true, ENCODING 'latin1');
