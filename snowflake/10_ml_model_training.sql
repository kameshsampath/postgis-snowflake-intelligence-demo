-- Copyright 2025 Kamesh Sampath
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================
-- Phase 9: ML Model Training - Maintenance Forecasting
-- =====================================================
-- Trains FORECAST models to predict:
--   1. Bulb failures (most common issue)
--   2. All maintenance issues (total workload)

-- Prerequisites:
-- 1. Run 08_ml_training_view.sql first
-- 2. Snowflake ML Functions enabled on account
-- 3. Warehouse size MEDIUM recommended

USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;

-- =====================================================
-- PART A: BULB FAILURE FORECASTING
-- =====================================================

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
-- PART B: ALL ISSUES FORECASTING (Total Maintenance)
-- =====================================================

-- =====================================================
-- STEP 7: Create All Issues Training Table
-- =====================================================

CREATE OR REPLACE TABLE ML_ALL_ISSUES_FORECAST_TRAINING AS
SELECT 
    REQUEST_DATE AS ts,
    TOTAL_REQUESTS AS y
FROM ML_ALL_ISSUES_TIMESERIES
WHERE REQUEST_DATE IS NOT NULL
ORDER BY REQUEST_DATE;

-- Verify training data
SELECT 
    'All Issues Training Data' AS check_name,
    COUNT(*) AS total_records,
    MIN(ts) AS start_date,
    MAX(ts) AS end_date,
    SUM(y) AS total_requests,
    ROUND(AVG(y), 2) AS avg_daily_requests
FROM ML_ALL_ISSUES_FORECAST_TRAINING;

-- =====================================================
-- STEP 8: Train All Issues Forecast Model
-- =====================================================

CREATE OR REPLACE SNOWFLAKE.ML.FORECAST ALL_ISSUES_FORECASTER(
    INPUT_DATA => SYSTEM$REFERENCE('TABLE', 'ML_ALL_ISSUES_FORECAST_TRAINING'),
    TIMESTAMP_COLNAME => 'ts',
    TARGET_COLNAME => 'y'
);

-- Check training status
SHOW SNOWFLAKE.ML.FORECAST;

-- =====================================================
-- STEP 9: Generate 30-Day All Issues Forecast
-- =====================================================

CALL ALL_ISSUES_FORECASTER!FORECAST(
    FORECASTING_PERIODS => 30,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

CREATE OR REPLACE TABLE ALL_ISSUES_FORECAST_30D AS
SELECT 
    ts::DATE AS FORECAST_DATE,
    ROUND(forecast, 0) AS PREDICTED_REQUESTS,
    ROUND(lower_bound, 0) AS LOWER_BOUND,
    ROUND(upper_bound, 0) AS UPPER_BOUND,
    ROUND(forecast, 2) AS PREDICTED_REQUESTS_PRECISE,
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
-- STEP 10: Generate 90-Day All Issues Forecast
-- =====================================================

CALL ALL_ISSUES_FORECASTER!FORECAST(
    FORECASTING_PERIODS => 90,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

CREATE OR REPLACE TABLE ALL_ISSUES_FORECAST_90D AS
SELECT 
    ts::DATE AS FORECAST_DATE,
    ROUND(forecast, 0) AS PREDICTED_REQUESTS,
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
-- STEP 11: Create All Issues User-Friendly Views
-- =====================================================

-- Daily Maintenance Schedule - total workload planning
CREATE OR REPLACE VIEW MAINTENANCE_SCHEDULE AS
SELECT 
    FORECAST_DATE,
    PREDICTED_REQUESTS,
    LOWER_BOUND,
    UPPER_BOUND,
    SEASON,
    DAY_OF_WEEK,
    CASE 
        WHEN PREDICTED_REQUESTS >= 8 THEN 'HIGH'
        WHEN PREDICTED_REQUESTS >= 5 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS WORKLOAD_LEVEL,
    CASE 
        WHEN PREDICTED_REQUESTS >= 8 THEN 'Full crew + backup (4+ technicians)'
        WHEN PREDICTED_REQUESTS >= 5 THEN 'Full crew (3 technicians)'
        ELSE 'Standard crew (2 technicians)'
    END AS STAFFING_RECOMMENDATION,
    -- Estimate parts needed (based on issue type distribution)
    CEIL(PREDICTED_REQUESTS * 0.5 * 1.2) AS BULBS_TO_STOCK,      -- 50% are bulb failures
    CEIL(PREDICTED_REQUESTS * 0.2 * 1.2) AS WIRING_KITS_TO_STOCK, -- 20% are wiring
    CEIL(PREDICTED_REQUESTS * 0.1 * 1.2) AS POLES_TO_STOCK,       -- 10% are pole damage
    WEEKOFYEAR(FORECAST_DATE) AS WEEK_NUMBER,
    PREDICTION_RANGE AS UNCERTAINTY_RANGE
FROM ALL_ISSUES_FORECAST_30D
ORDER BY FORECAST_DATE;

-- Weekly Summary - all maintenance
CREATE OR REPLACE VIEW WEEKLY_MAINTENANCE_FORECAST AS
SELECT 
    WEEK_START,
    SUM(PREDICTED_REQUESTS) AS TOTAL_PREDICTED_REQUESTS,
    SUM(LOWER_BOUND) AS TOTAL_LOWER_BOUND,
    SUM(UPPER_BOUND) AS TOTAL_UPPER_BOUND,
    ROUND(AVG(PREDICTED_REQUESTS), 1) AS AVG_DAILY_REQUESTS,
    MAX(PREDICTED_REQUESTS) AS PEAK_DAY_REQUESTS,
    MIN(SEASON) AS PRIMARY_SEASON
FROM ALL_ISSUES_FORECAST_90D
GROUP BY WEEK_START
ORDER BY WEEK_START;

-- Combined Forecast Comparison View
CREATE OR REPLACE VIEW FORECAST_COMPARISON AS
SELECT 
    b.FORECAST_DATE,
    b.PREDICTED_FAILURES AS BULB_FAILURES,
    a.PREDICTED_REQUESTS AS ALL_ISSUES,
    a.PREDICTED_REQUESTS - b.PREDICTED_FAILURES AS OTHER_ISSUES,
    ROUND(b.PREDICTED_FAILURES * 100.0 / NULLIF(a.PREDICTED_REQUESTS, 0), 1) AS BULB_PERCENTAGE,
    b.SEASON,
    CASE 
        WHEN a.PREDICTED_REQUESTS >= 8 THEN 'HIGH'
        WHEN a.PREDICTED_REQUESTS >= 5 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS OVERALL_WORKLOAD
FROM BULB_FAILURE_FORECAST_30D b
JOIN ALL_ISSUES_FORECAST_30D a ON b.FORECAST_DATE = a.FORECAST_DATE
ORDER BY b.FORECAST_DATE;

-- =====================================================
-- VERIFICATION
-- =====================================================

-- Bulb Failure Forecast (30 days)
SELECT * FROM BULB_FAILURE_FORECAST_30D ORDER BY FORECAST_DATE LIMIT 10;

-- All Issues Forecast (30 days)
SELECT * FROM ALL_ISSUES_FORECAST_30D ORDER BY FORECAST_DATE LIMIT 10;

-- Forecast Comparison
SELECT * FROM FORECAST_COMPARISON ORDER BY FORECAST_DATE LIMIT 10;

SELECT 
    'Bulb Failure Forecast' AS model,
    (SELECT COUNT(*) FROM ML_BULB_FORECAST_TRAINING) AS training_days,
    (SELECT COUNT(*) FROM BULB_FAILURE_FORECAST_30D) AS forecast_30d_days,
    (SELECT SUM(PREDICTED_FAILURES) FROM BULB_FAILURE_FORECAST_30D) AS total_30d_predicted
UNION ALL
SELECT 
    'All Issues Forecast',
    (SELECT COUNT(*) FROM ML_ALL_ISSUES_FORECAST_TRAINING),
    (SELECT COUNT(*) FROM ALL_ISSUES_FORECAST_30D),
    (SELECT SUM(PREDICTED_REQUESTS) FROM ALL_ISSUES_FORECAST_30D);

-- =====================================================
-- CHECKLIST
-- =====================================================
-- [ ] BULB_FAILURE_FORECASTER model trained
-- [ ] ALL_ISSUES_FORECASTER model trained
-- [ ] BULB_FAILURE_FORECAST_30D table populated
-- [ ] BULB_FAILURE_FORECAST_90D table populated
-- [ ] ALL_ISSUES_FORECAST_30D table populated
-- [ ] ALL_ISSUES_FORECAST_90D table populated
-- [ ] BULB_REPLACEMENT_SCHEDULE view accessible
-- [ ] MAINTENANCE_SCHEDULE view accessible
-- [ ] WEEKLY_BULB_FORECAST view accessible
-- [ ] WEEKLY_MAINTENANCE_FORECAST view accessible
-- [ ] FORECAST_COMPARISON view accessible
-- [ ] Ready for 10_ml_queries.sql
-- =====================================================

SELECT 'ML Model Training Complete - Both Models' AS status, CURRENT_TIMESTAMP() AS trained_at;
