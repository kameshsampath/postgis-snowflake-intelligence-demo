-- =====================================================
-- Phase 9: ML Model Training - Bulb Failure Forecasting
-- =====================================================
-- Trains a FORECAST model to predict future bulb failures

-- Prerequisites:
-- 1. Run 08_ml_training_view.sql first
-- 2. Snowflake ML Functions enabled on account
-- 3. Warehouse size MEDIUM recommended

USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;

-- =====================================================
-- STEP 1: Create Training Table
-- =====================================================
-- FORECAST requires a table, not a view

CREATE OR REPLACE TABLE ML_BULB_FORECAST_TRAINING AS
SELECT 
    FAILURE_DATE AS ts,  -- Snowflake FORECAST expects 'ts' for timestamp
    BULB_FAILURE_COUNT AS y  -- Snowflake FORECAST expects 'y' for target
FROM ML_BULB_FAILURE_TIMESERIES
WHERE FAILURE_DATE IS NOT NULL
ORDER BY FAILURE_DATE;

-- Verify training data
SELECT 
    'Forecast Training Data' AS check_name,
    COUNT(*) AS total_records,
    MIN(ts) AS start_date,
    MAX(ts) AS end_date,
    SUM(y) AS total_failures,
    ROUND(AVG(y), 2) AS avg_daily_failures
FROM ML_BULB_FORECAST_TRAINING;

-- =====================================================
-- STEP 2: Train Forecast Model
-- =====================================================
-- Training takes 1-3 minutes

CREATE OR REPLACE SNOWFLAKE.ML.FORECAST BULB_FAILURE_FORECASTER(
    INPUT_DATA => SYSTEM$REFERENCE('TABLE', 'ML_BULB_FORECAST_TRAINING'),
    TIMESTAMP_COLNAME => 'ts',
    TARGET_COLNAME => 'y'
);

-- Check training status
SHOW SNOWFLAKE.ML.FORECAST;

-- =====================================================
-- STEP 3: View Model Information
-- =====================================================

CALL BULB_FAILURE_FORECASTER!SHOW_EVALUATION_METRICS();
CALL BULB_FAILURE_FORECASTER!SHOW_TRAINING_LOGS();

-- =====================================================
-- STEP 4: Generate 30-Day Forecast
-- =====================================================

CALL BULB_FAILURE_FORECASTER!FORECAST(
    FORECASTING_PERIODS => 30,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

CREATE OR REPLACE TABLE BULB_FAILURE_FORECAST_30D AS
SELECT 
    ts::DATE AS FORECAST_DATE,
    ROUND(forecast, 0) AS PREDICTED_FAILURES,
    ROUND(lower_bound, 0) AS LOWER_BOUND,
    ROUND(upper_bound, 0) AS UPPER_BOUND,
    ROUND(forecast, 2) AS PREDICTED_FAILURES_PRECISE,
    DAYOFWEEK(ts) AS DAY_OF_WEEK,
    CASE 
        WHEN MONTH(ts) BETWEEN 6 AND 9 THEN 'monsoon'
        WHEN MONTH(ts) BETWEEN 3 AND 5 THEN 'summer'
        ELSE 'winter'
    END AS SEASON,
    ROUND(upper_bound - lower_bound, 0) AS PREDICTION_RANGE
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY ts;

-- =====================================================
-- STEP 5: Generate 90-Day Extended Forecast
-- =====================================================

CALL BULB_FAILURE_FORECASTER!FORECAST(
    FORECASTING_PERIODS => 90,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

CREATE OR REPLACE TABLE BULB_FAILURE_FORECAST_90D AS
SELECT 
    ts::DATE AS FORECAST_DATE,
    ROUND(forecast, 0) AS PREDICTED_FAILURES,
    ROUND(lower_bound, 0) AS LOWER_BOUND,
    ROUND(upper_bound, 0) AS UPPER_BOUND,
    DATE_TRUNC('week', ts)::DATE AS WEEK_START,
    DATE_TRUNC('month', ts)::DATE AS MONTH_START,
    CASE 
        WHEN MONTH(ts) BETWEEN 6 AND 9 THEN 'monsoon'
        WHEN MONTH(ts) BETWEEN 3 AND 5 THEN 'summer'
        ELSE 'winter'
    END AS SEASON
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY ts;

-- =====================================================
-- STEP 6: Create User-Friendly Views
-- =====================================================

-- Bulb Replacement Schedule - actionable maintenance planning
CREATE OR REPLACE VIEW BULB_REPLACEMENT_SCHEDULE AS
SELECT 
    FORECAST_DATE,
    PREDICTED_FAILURES,
    LOWER_BOUND,
    UPPER_BOUND,
    SEASON,
    DAY_OF_WEEK,
    CASE 
        WHEN PREDICTED_FAILURES >= 5 THEN 'HIGH'
        WHEN PREDICTED_FAILURES >= 3 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS PRIORITY,
    CASE 
        WHEN PREDICTED_FAILURES >= 5 THEN 'Full crew (3+ technicians)'
        WHEN PREDICTED_FAILURES >= 3 THEN 'Standard crew (2 technicians)'
        ELSE 'Minimal crew (1 technician)'
    END AS STAFFING_RECOMMENDATION,
    CEIL(UPPER_BOUND * 1.2) AS BULBS_TO_STOCK,
    WEEKOFYEAR(FORECAST_DATE) AS WEEK_NUMBER,
    PREDICTION_RANGE AS UNCERTAINTY_RANGE
FROM BULB_FAILURE_FORECAST_30D
ORDER BY FORECAST_DATE;

-- Weekly Summary - inventory and budget planning
CREATE OR REPLACE VIEW WEEKLY_BULB_FORECAST AS
SELECT 
    WEEK_START,
    SUM(PREDICTED_FAILURES) AS TOTAL_PREDICTED_FAILURES,
    SUM(LOWER_BOUND) AS TOTAL_LOWER_BOUND,
    SUM(UPPER_BOUND) AS TOTAL_UPPER_BOUND,
    ROUND(AVG(PREDICTED_FAILURES), 1) AS AVG_DAILY_FAILURES,
    MAX(PREDICTED_FAILURES) AS PEAK_DAY_FAILURES,
    MIN(SEASON) AS PRIMARY_SEASON
FROM BULB_FAILURE_FORECAST_90D
GROUP BY WEEK_START
ORDER BY WEEK_START;

-- =====================================================
-- VERIFICATION
-- =====================================================

SELECT * FROM BULB_FAILURE_FORECAST_30D ORDER BY FORECAST_DATE LIMIT 10;

SELECT 
    'Forecast Summary' AS status,
    (SELECT COUNT(*) FROM ML_BULB_FORECAST_TRAINING) AS training_days,
    (SELECT COUNT(*) FROM BULB_FAILURE_FORECAST_30D) AS forecast_30d_days,
    (SELECT COUNT(*) FROM BULB_FAILURE_FORECAST_90D) AS forecast_90d_days,
    (SELECT SUM(PREDICTED_FAILURES) FROM BULB_FAILURE_FORECAST_30D) AS total_30d_failures;

-- =====================================================
-- CHECKLIST
-- =====================================================
-- [ ] BULB_FAILURE_FORECASTER model trained
-- [ ] BULB_FAILURE_FORECAST_30D table populated
-- [ ] BULB_FAILURE_FORECAST_90D table populated
-- [ ] BULB_REPLACEMENT_SCHEDULE view accessible
-- [ ] WEEKLY_BULB_FORECAST view accessible
-- [ ] Ready for 10_ml_queries.sql
-- =====================================================

SELECT 'ML Model Training Complete' AS status, CURRENT_TIMESTAMP() AS trained_at;
