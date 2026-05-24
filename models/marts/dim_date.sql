{{
    config(
        materialized='table'
    )
}}

-- Date dimension covering 2014-12-29 through ~2019 (1,500 days).
-- Uses Snowflake's GENERATOR for the date spine.

WITH date_spine AS (
    SELECT DATEADD(day, SEQ4(), '2014-12-29'::DATE) AS d
    FROM TABLE(GENERATOR(ROWCOUNT => 1500))
)
SELECT
    d                                                   AS date_day,
    EXTRACT(year FROM d)                                AS year,
    EXTRACT(quarter FROM d)                             AS quarter,
    EXTRACT(month FROM d)                               AS month,
    TO_CHAR(d, 'YYYY-MM')                               AS year_month,
    EXTRACT(week FROM d)                                AS week_of_year,
    DATE_TRUNC('week', d)                               AS week_start,
    DATE_TRUNC('month', d)                              AS month_start,
    EXTRACT(dayofweek FROM d)                           AS day_of_week_num,
    TO_CHAR(d, 'Dy')                                    AS day_of_week_name,
    CASE WHEN EXTRACT(dayofweek FROM d) IN (0, 6) THEN 1 ELSE 0 END
                                                        AS is_weekend
FROM date_spine
