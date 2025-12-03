-- =====================================================
-- Phase 8: ML Training Data - Bulb Failure Forecasting
-- =====================================================
-- Prepares time-series data for predicting future bulb failures

-- Prerequisites:
-- 1. Phase 6 complete (CDC data in Snowflake)
-- 2. Phase 7 complete (Analytics schema exists)
-- 3. Sufficient historical maintenance data (at least 30 days)

-- IMPORTANT: CDC tables from PostgreSQL use quoted lowercase identifiers

USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;

-- =====================================================
-- STEP 1: Daily Bulb Failure Time Series
-- =====================================================
-- Aggregates bulb failures by day for forecasting model

CREATE OR REPLACE VIEW ML_BULB_FAILURE_TIMESERIES AS
WITH daily_bulb_failures AS (
    SELECT 
        DATE_TRUNC('day', mr."reported_at")::DATE AS FAILURE_DATE,
        COUNT(*) AS BULB_FAILURE_COUNT,
        COUNT(DISTINCT mr."light_id") AS UNIQUE_LIGHTS_AFFECTED
    FROM STREETLIGHTS_DEMO."streetlights"."maintenance_requests" mr
    WHERE mr."issue_type" = 'bulb_failure'
      AND mr."reported_at" IS NOT NULL
    GROUP BY DATE_TRUNC('day', mr."reported_at")::DATE
),
date_spine AS (
    -- Generate complete date range to fill gaps (no missing days)
    SELECT DATEADD('day', SEQ4(), 
        (SELECT MIN(FAILURE_DATE) FROM daily_bulb_failures)
    )::DATE AS CALENDAR_DATE
    FROM TABLE(GENERATOR(ROWCOUNT => 400))
    WHERE CALENDAR_DATE <= (SELECT MAX(FAILURE_DATE) FROM daily_bulb_failures)
)
SELECT 
    ds.CALENDAR_DATE AS FAILURE_DATE,
    COALESCE(dbf.BULB_FAILURE_COUNT, 0) AS BULB_FAILURE_COUNT,
    COALESCE(dbf.UNIQUE_LIGHTS_AFFECTED, 0) AS UNIQUE_LIGHTS_AFFECTED,
    
    -- Temporal features
    DAYOFWEEK(ds.CALENDAR_DATE) AS DAY_OF_WEEK,
    DAYOFMONTH(ds.CALENDAR_DATE) AS DAY_OF_MONTH,
    MONTH(ds.CALENDAR_DATE) AS MONTH,
    QUARTER(ds.CALENDAR_DATE) AS QUARTER,
    
    -- Season indicator (Bengaluru climate)
    CASE 
        WHEN MONTH(ds.CALENDAR_DATE) BETWEEN 6 AND 9 THEN 'monsoon'
        WHEN MONTH(ds.CALENDAR_DATE) BETWEEN 3 AND 5 THEN 'summer'
        ELSE 'winter'
    END AS SEASON,
    
    -- Weekend flag
    CASE WHEN DAYOFWEEK(ds.CALENDAR_DATE) IN (0, 6) THEN 1 ELSE 0 END AS IS_WEEKEND
    
FROM date_spine ds
LEFT JOIN daily_bulb_failures dbf ON ds.CALENDAR_DATE = dbf.FAILURE_DATE
ORDER BY ds.CALENDAR_DATE;

-- =====================================================
-- STEP 2: Weekly Aggregated Bulb Failures
-- =====================================================
-- Smoother time series for more stable forecasting

CREATE OR REPLACE VIEW ML_BULB_FAILURE_WEEKLY AS
SELECT 
    DATE_TRUNC('week', FAILURE_DATE)::DATE AS WEEK_START,
    SUM(BULB_FAILURE_COUNT) AS WEEKLY_FAILURES,
    SUM(UNIQUE_LIGHTS_AFFECTED) AS WEEKLY_LIGHTS_AFFECTED,
    AVG(BULB_FAILURE_COUNT) AS AVG_DAILY_FAILURES,
    MAX(BULB_FAILURE_COUNT) AS MAX_DAILY_FAILURES,
    MIN(SEASON) AS SEASON
FROM ML_BULB_FAILURE_TIMESERIES
GROUP BY DATE_TRUNC('week', FAILURE_DATE)::DATE
ORDER BY WEEK_START;

-- =====================================================
-- STEP 3: Bulb Failure with Rolling Statistics
-- =====================================================
-- Adds trend indicators for analysis

CREATE OR REPLACE VIEW ML_BULB_FAILURE_ENRICHED AS
SELECT 
    FAILURE_DATE,
    BULB_FAILURE_COUNT,
    UNIQUE_LIGHTS_AFFECTED,
    DAY_OF_WEEK,
    MONTH,
    SEASON,
    IS_WEEKEND,
    
    -- Rolling averages (trend indicators)
    AVG(BULB_FAILURE_COUNT) OVER (
        ORDER BY FAILURE_DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS ROLLING_7D_AVG,
    
    AVG(BULB_FAILURE_COUNT) OVER (
        ORDER BY FAILURE_DATE ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS ROLLING_14D_AVG,
    
    AVG(BULB_FAILURE_COUNT) OVER (
        ORDER BY FAILURE_DATE ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS ROLLING_30D_AVG,
    
    -- Standard deviation for volatility
    STDDEV(BULB_FAILURE_COUNT) OVER (
        ORDER BY FAILURE_DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS ROLLING_7D_STDDEV,
    
    -- Cumulative sum
    SUM(BULB_FAILURE_COUNT) OVER (ORDER BY FAILURE_DATE) AS CUMULATIVE_FAILURES,
    
    -- Lag features
    LAG(BULB_FAILURE_COUNT, 1) OVER (ORDER BY FAILURE_DATE) AS FAILURES_1D_AGO,
    LAG(BULB_FAILURE_COUNT, 7) OVER (ORDER BY FAILURE_DATE) AS FAILURES_7D_AGO,
    LAG(BULB_FAILURE_COUNT, 14) OVER (ORDER BY FAILURE_DATE) AS FAILURES_14D_AGO
    
FROM ML_BULB_FAILURE_TIMESERIES
ORDER BY FAILURE_DATE;

-- =====================================================
-- STEP 4: Feature Statistics
-- =====================================================

CREATE OR REPLACE VIEW ML_FEATURE_STATS AS
SELECT 
    'BULB_FAILURE_DAILY' AS FEATURE,
    MIN(BULB_FAILURE_COUNT) AS MIN_VAL,
    MAX(BULB_FAILURE_COUNT) AS MAX_VAL,
    ROUND(AVG(BULB_FAILURE_COUNT), 2) AS AVG_VAL,
    ROUND(STDDEV(BULB_FAILURE_COUNT), 2) AS STDDEV_VAL,
    COUNT(*) AS SAMPLE_COUNT
FROM ML_BULB_FAILURE_TIMESERIES
UNION ALL
SELECT 
    'WEEKLY_BULB_FAILURES',
    MIN(WEEKLY_FAILURES),
    MAX(WEEKLY_FAILURES),
    ROUND(AVG(WEEKLY_FAILURES), 2),
    ROUND(STDDEV(WEEKLY_FAILURES), 2),
    COUNT(*)
FROM ML_BULB_FAILURE_WEEKLY;

-- =====================================================
-- VERIFICATION
-- =====================================================

SELECT 'Bulb Failure Time Series' AS dataset, 
       COUNT(*) AS total_days,
       SUM(BULB_FAILURE_COUNT) AS total_failures,
       MIN(FAILURE_DATE) AS start_date,
       MAX(FAILURE_DATE) AS end_date
FROM ML_BULB_FAILURE_TIMESERIES;

SELECT 'Weekly Bulb Failures' AS dataset,
       COUNT(*) AS total_weeks,
       SUM(WEEKLY_FAILURES) AS total_failures,
       ROUND(AVG(WEEKLY_FAILURES), 2) AS avg_weekly_failures
FROM ML_BULB_FAILURE_WEEKLY;

-- Seasonal distribution
SELECT SEASON, COUNT(*) AS days, SUM(BULB_FAILURE_COUNT) AS total_failures,
       ROUND(AVG(BULB_FAILURE_COUNT), 2) AS avg_daily_failures
FROM ML_BULB_FAILURE_TIMESERIES
GROUP BY SEASON ORDER BY avg_daily_failures DESC;

SELECT * FROM ML_FEATURE_STATS;

-- =====================================================
-- CHECKLIST
-- =====================================================
-- [ ] ML_BULB_FAILURE_TIMESERIES view created
-- [ ] At least 30 days of history
-- [ ] Seasonal patterns visible
-- [ ] Ready for 09_ml_model_training.sql
-- =====================================================
