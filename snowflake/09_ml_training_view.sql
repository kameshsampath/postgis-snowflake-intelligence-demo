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
-- Phase 8: ML Training Data - Maintenance Forecasting
-- =====================================================
-- Prepares time-series data for predicting:
--   1. Bulb failures (most common issue type)
--   2. All maintenance issues (total workload)

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
-- STEP 4: Feature Statistics (Bulb Failures)
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
-- STEP 5: ALL ISSUES Time Series (Total Maintenance)
-- =====================================================
-- Aggregates ALL maintenance requests for total workload forecasting

CREATE OR REPLACE VIEW ML_ALL_ISSUES_TIMESERIES AS
WITH daily_all_issues AS (
    SELECT 
        DATE_TRUNC('day', mr."reported_at")::DATE AS REQUEST_DATE,
        COUNT(*) AS TOTAL_REQUESTS,
        COUNT(DISTINCT mr."light_id") AS UNIQUE_LIGHTS_AFFECTED,
        COUNT(CASE WHEN mr."issue_type" = 'bulb_failure' THEN 1 END) AS BULB_FAILURES,
        COUNT(CASE WHEN mr."issue_type" = 'wiring' THEN 1 END) AS WIRING_ISSUES,
        COUNT(CASE WHEN mr."issue_type" = 'pole_damage' THEN 1 END) AS POLE_DAMAGE,
        COUNT(CASE WHEN mr."issue_type" = 'power_supply' THEN 1 END) AS POWER_SUPPLY,
        COUNT(CASE WHEN mr."issue_type" = 'sensor_failure' THEN 1 END) AS SENSOR_FAILURES
    FROM STREETLIGHTS_DEMO."streetlights"."maintenance_requests" mr
    WHERE mr."reported_at" IS NOT NULL
    GROUP BY DATE_TRUNC('day', mr."reported_at")::DATE
),
date_spine AS (
    SELECT DATEADD('day', SEQ4(), 
        (SELECT MIN(REQUEST_DATE) FROM daily_all_issues)
    )::DATE AS CALENDAR_DATE
    FROM TABLE(GENERATOR(ROWCOUNT => 400))
    WHERE CALENDAR_DATE <= (SELECT MAX(REQUEST_DATE) FROM daily_all_issues)
)
SELECT 
    ds.CALENDAR_DATE AS REQUEST_DATE,
    COALESCE(dai.TOTAL_REQUESTS, 0) AS TOTAL_REQUESTS,
    COALESCE(dai.UNIQUE_LIGHTS_AFFECTED, 0) AS UNIQUE_LIGHTS_AFFECTED,
    COALESCE(dai.BULB_FAILURES, 0) AS BULB_FAILURES,
    COALESCE(dai.WIRING_ISSUES, 0) AS WIRING_ISSUES,
    COALESCE(dai.POLE_DAMAGE, 0) AS POLE_DAMAGE,
    COALESCE(dai.POWER_SUPPLY, 0) AS POWER_SUPPLY,
    COALESCE(dai.SENSOR_FAILURES, 0) AS SENSOR_FAILURES,
    
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
LEFT JOIN daily_all_issues dai ON ds.CALENDAR_DATE = dai.REQUEST_DATE
ORDER BY ds.CALENDAR_DATE;

-- =====================================================
-- STEP 6: Weekly Aggregated All Issues
-- =====================================================

CREATE OR REPLACE VIEW ML_ALL_ISSUES_WEEKLY AS
SELECT 
    DATE_TRUNC('week', REQUEST_DATE)::DATE AS WEEK_START,
    SUM(TOTAL_REQUESTS) AS WEEKLY_REQUESTS,
    SUM(UNIQUE_LIGHTS_AFFECTED) AS WEEKLY_LIGHTS_AFFECTED,
    SUM(BULB_FAILURES) AS WEEKLY_BULB_FAILURES,
    SUM(WIRING_ISSUES) AS WEEKLY_WIRING_ISSUES,
    SUM(POLE_DAMAGE) AS WEEKLY_POLE_DAMAGE,
    SUM(POWER_SUPPLY) AS WEEKLY_POWER_SUPPLY,
    SUM(SENSOR_FAILURES) AS WEEKLY_SENSOR_FAILURES,
    AVG(TOTAL_REQUESTS) AS AVG_DAILY_REQUESTS,
    MAX(TOTAL_REQUESTS) AS MAX_DAILY_REQUESTS,
    MIN(SEASON) AS SEASON
FROM ML_ALL_ISSUES_TIMESERIES
GROUP BY DATE_TRUNC('week', REQUEST_DATE)::DATE
ORDER BY WEEK_START;

-- =====================================================
-- STEP 7: Issue Type Distribution Summary
-- =====================================================

CREATE OR REPLACE VIEW ML_ISSUE_TYPE_DISTRIBUTION AS
SELECT 
    mr."issue_type" AS ISSUE_TYPE,
    COUNT(*) AS TOTAL_COUNT,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS PERCENTAGE,
    MIN(mr."reported_at")::DATE AS FIRST_REPORTED,
    MAX(mr."reported_at")::DATE AS LAST_REPORTED,
    COUNT(DISTINCT mr."light_id") AS UNIQUE_LIGHTS
FROM STREETLIGHTS_DEMO."streetlights"."maintenance_requests" mr
WHERE mr."reported_at" IS NOT NULL
GROUP BY mr."issue_type"
ORDER BY TOTAL_COUNT DESC;

-- =====================================================
-- STEP 8: Feature Statistics (All Issues)
-- =====================================================

CREATE OR REPLACE VIEW ML_ALL_ISSUES_STATS AS
SELECT 
    'ALL_ISSUES_DAILY' AS FEATURE,
    MIN(TOTAL_REQUESTS) AS MIN_VAL,
    MAX(TOTAL_REQUESTS) AS MAX_VAL,
    ROUND(AVG(TOTAL_REQUESTS), 2) AS AVG_VAL,
    ROUND(STDDEV(TOTAL_REQUESTS), 2) AS STDDEV_VAL,
    COUNT(*) AS SAMPLE_COUNT
FROM ML_ALL_ISSUES_TIMESERIES
UNION ALL
SELECT 
    'ALL_ISSUES_WEEKLY',
    MIN(WEEKLY_REQUESTS),
    MAX(WEEKLY_REQUESTS),
    ROUND(AVG(WEEKLY_REQUESTS), 2),
    ROUND(STDDEV(WEEKLY_REQUESTS), 2),
    COUNT(*)
FROM ML_ALL_ISSUES_WEEKLY;

-- =====================================================
-- VERIFICATION
-- =====================================================

-- Verifying Bulb Failure Time Series
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

-- Verifying All Issues Time Series
SELECT 'All Issues Time Series' AS dataset, 
       COUNT(*) AS total_days,
       SUM(TOTAL_REQUESTS) AS total_requests,
       MIN(REQUEST_DATE) AS start_date,
       MAX(REQUEST_DATE) AS end_date
FROM ML_ALL_ISSUES_TIMESERIES;

SELECT 'Weekly All Issues' AS dataset,
       COUNT(*) AS total_weeks,
       SUM(WEEKLY_REQUESTS) AS total_requests,
       ROUND(AVG(WEEKLY_REQUESTS), 2) AS avg_weekly_requests
FROM ML_ALL_ISSUES_WEEKLY;

-- Seasonal distribution (Bulb Failures)
-- Seasonal Distribution - Bulb Failures
SELECT SEASON, COUNT(*) AS days, SUM(BULB_FAILURE_COUNT) AS total_failures,
       ROUND(AVG(BULB_FAILURE_COUNT), 2) AS avg_daily_failures
FROM ML_BULB_FAILURE_TIMESERIES
GROUP BY SEASON ORDER BY avg_daily_failures DESC;

-- Seasonal distribution (All Issues)
-- Seasonal Distribution - All Issues
SELECT SEASON, COUNT(*) AS days, SUM(TOTAL_REQUESTS) AS total_requests,
       ROUND(AVG(TOTAL_REQUESTS), 2) AS avg_daily_requests
FROM ML_ALL_ISSUES_TIMESERIES
GROUP BY SEASON ORDER BY avg_daily_requests DESC;

-- Issue Type Distribution
-- Issue Type Distribution
SELECT * FROM ML_ISSUE_TYPE_DISTRIBUTION;

-- Feature Statistics
SELECT * FROM ML_FEATURE_STATS;
SELECT * FROM ML_ALL_ISSUES_STATS;

-- =====================================================
-- CHECKLIST
-- =====================================================
-- [ ] ML_BULB_FAILURE_TIMESERIES view created
-- [ ] ML_ALL_ISSUES_TIMESERIES view created
-- [ ] ML_ISSUE_TYPE_DISTRIBUTION view created
-- [ ] At least 30 days of history
-- [ ] Seasonal patterns visible
-- [ ] Ready for 09_ml_model_training.sql
-- =====================================================
