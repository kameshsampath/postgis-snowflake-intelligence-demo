-- =====================================================
-- Phase 10: ML Queries - Bulb Failure Forecasting
-- =====================================================
-- Ready-to-use queries for forecasting results

-- Prerequisites: Run 09_ml_model_training.sql first

USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;

-- =====================================================
-- SECTION 1: DAILY FORECAST QUERIES
-- =====================================================

-- 1.1: Next 7 Days - Quick Planning View
SELECT 
    FORECAST_DATE,
    PREDICTED_FAILURES,
    LOWER_BOUND || ' - ' || UPPER_BOUND AS RANGE,
    PRIORITY,
    STAFFING_RECOMMENDATION,
    BULBS_TO_STOCK
FROM BULB_REPLACEMENT_SCHEDULE
WHERE FORECAST_DATE <= DATEADD('day', 7, CURRENT_DATE())
ORDER BY FORECAST_DATE;

-- 1.2: Today's Operations Briefing
SELECT 
    FORECAST_DATE AS TODAY,
    PREDICTED_FAILURES AS EXPECTED_FAILURES,
    STAFFING_RECOMMENDATION,
    BULBS_TO_STOCK AS BULBS_NEEDED,
    PRIORITY,
    CASE 
        WHEN SEASON = 'monsoon' THEN 'Monsoon season - expect weather delays'
        WHEN SEASON = 'summer' THEN 'Summer heat - schedule early morning/evening'
        ELSE 'Favorable conditions'
    END AS WEATHER_NOTE
FROM BULB_REPLACEMENT_SCHEDULE
WHERE FORECAST_DATE = CURRENT_DATE();

-- 1.3: High-Volume Days Alert
SELECT 
    FORECAST_DATE,
    PREDICTED_FAILURES,
    UPPER_BOUND AS WORST_CASE,
    SEASON,
    'Deploy ' || 
    CASE 
        WHEN PREDICTED_FAILURES >= 5 THEN '3+ crews'
        WHEN PREDICTED_FAILURES >= 3 THEN '2 crews'
        ELSE '1 crew'
    END || ', stock ' || CEIL(UPPER_BOUND * 1.5) || ' bulbs' AS ACTION_REQUIRED
FROM BULB_REPLACEMENT_SCHEDULE
WHERE PRIORITY IN ('HIGH', 'MEDIUM')
ORDER BY FORECAST_DATE;

-- =====================================================
-- SECTION 2: WEEKLY PLANNING QUERIES
-- =====================================================

-- 2.1: Weekly Inventory Planning with Cost Breakdown
SELECT 
    WEEK_START,
    TOTAL_PREDICTED_FAILURES AS PREDICTED_BULB_FAILURES,
    TOTAL_UPPER_BOUND AS WORST_CASE_ESTIMATE,
    CEIL(TOTAL_UPPER_BOUND * 1.2) AS BULBS_TO_ORDER,
    PRIMARY_SEASON,
    
    -- Cost breakdown (INR)
    CEIL(TOTAL_UPPER_BOUND * 1.2) * 1000 AS MATERIAL_COST_INR,      -- ₹1000 per LED bulb
    TOTAL_PREDICTED_FAILURES * 500 AS LABOR_COST_INR,               -- ₹500 per replacement job
    TOTAL_PREDICTED_FAILURES * 150 AS TRANSPORT_COST_INR,           -- ₹150 vehicle/travel per job
    
    -- Total weekly budget
    (CEIL(TOTAL_UPPER_BOUND * 1.2) * 1000) + 
    (TOTAL_PREDICTED_FAILURES * 500) + 
    (TOTAL_PREDICTED_FAILURES * 150) AS TOTAL_WEEKLY_BUDGET_INR
FROM WEEKLY_BULB_FORECAST
ORDER BY WEEK_START
LIMIT 12;

-- 2.2: Week-Ahead Crew Schedule
SELECT 
    FORECAST_DATE,
    CASE DAYOFWEEK(FORECAST_DATE)
        WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue'
        WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat'
    END AS DAY,
    PREDICTED_FAILURES,
    PRIORITY,
    CASE 
        WHEN PREDICTED_FAILURES >= 5 THEN 'Crew A + Crew B + Crew C'
        WHEN PREDICTED_FAILURES >= 3 THEN 'Crew A + Crew B'
        ELSE 'Crew A'
    END AS ASSIGNED_CREWS,
    PREDICTED_FAILURES * 1.5 AS ESTIMATED_WORK_HOURS
FROM BULB_REPLACEMENT_SCHEDULE
WHERE FORECAST_DATE BETWEEN CURRENT_DATE() AND DATEADD('day', 7, CURRENT_DATE())
ORDER BY FORECAST_DATE;

-- =====================================================
-- SECTION 3: MONTHLY & SEASONAL QUERIES
-- =====================================================

-- 3.1: Monthly Forecast Summary
SELECT 
    DATE_TRUNC('month', FORECAST_DATE)::DATE AS MONTH,
    SUM(PREDICTED_FAILURES) AS TOTAL_PREDICTED_FAILURES,
    ROUND(AVG(PREDICTED_FAILURES), 1) AS AVG_DAILY_FAILURES,
    MAX(PREDICTED_FAILURES) AS PEAK_DAY,
    CEIL(SUM(UPPER_BOUND) * 1.2) AS BULBS_TO_STOCK
FROM BULB_FAILURE_FORECAST_90D
GROUP BY DATE_TRUNC('month', FORECAST_DATE)
ORDER BY MONTH;

-- 3.2: Seasonal Risk Comparison
SELECT 
    SEASON,
    COUNT(*) AS FORECAST_DAYS,
    SUM(PREDICTED_FAILURES) AS TOTAL_FAILURES,
    ROUND(AVG(PREDICTED_FAILURES), 2) AS AVG_DAILY_FAILURES,
    MAX(PREDICTED_FAILURES) AS PEAK_DAY_FAILURES,
    CASE 
        WHEN AVG(PREDICTED_FAILURES) > 3 THEN 'HIGH RISK'
        WHEN AVG(PREDICTED_FAILURES) > 2 THEN 'MEDIUM RISK'
        ELSE 'LOW RISK'
    END AS SEASONAL_RISK
FROM BULB_FAILURE_FORECAST_90D
GROUP BY SEASON
ORDER BY AVG_DAILY_FAILURES DESC;

-- =====================================================
-- SECTION 4: BUDGET PLANNING
-- =====================================================

-- 4.1: Monthly Budget Forecast with Detailed Cost Breakdown
WITH forecast_costs AS (
    SELECT 
        DATE_TRUNC('month', FORECAST_DATE)::DATE AS MONTH,
        SUM(PREDICTED_FAILURES) AS PREDICTED_FAILURES,
        CEIL(SUM(UPPER_BOUND) * 1.2) AS BULBS_NEEDED
    FROM BULB_FAILURE_FORECAST_90D
    GROUP BY DATE_TRUNC('month', FORECAST_DATE)
)
SELECT 
    MONTH,
    PREDICTED_FAILURES AS JOBS,
    BULBS_NEEDED,
    
    -- Cost breakdown (INR)
    BULBS_NEEDED * 1000 AS MATERIAL_COST_INR,           -- ₹1000 per LED bulb
    PREDICTED_FAILURES * 500 AS LABOR_COST_INR,         -- ₹500 per technician job
    PREDICTED_FAILURES * 150 AS TRANSPORT_COST_INR,     -- ₹150 vehicle cost per job
    PREDICTED_FAILURES * 100 AS OVERHEAD_COST_INR,      -- ₹100 admin/tools per job
    
    -- Total monthly budget
    (BULBS_NEEDED * 1000) + 
    (PREDICTED_FAILURES * 500) + 
    (PREDICTED_FAILURES * 150) + 
    (PREDICTED_FAILURES * 100) AS TOTAL_MONTHLY_BUDGET_INR
FROM forecast_costs
ORDER BY MONTH;

-- =====================================================
-- SECTION 5: DASHBOARD METRICS
-- =====================================================

-- 5.1: Key Forecast Metrics (for dashboard cards)
SELECT 
    'FORECAST_NEXT_7_DAYS' AS metric,
    SUM(PREDICTED_FAILURES)::VARCHAR AS value,
    'Expected bulb failures in next 7 days' AS description
FROM BULB_REPLACEMENT_SCHEDULE
WHERE FORECAST_DATE <= DATEADD('day', 7, CURRENT_DATE())

UNION ALL

SELECT 'FORECAST_NEXT_30_DAYS', SUM(PREDICTED_FAILURES)::VARCHAR, 'Expected bulb failures in next 30 days'
FROM BULB_REPLACEMENT_SCHEDULE

UNION ALL

SELECT 'HIGH_PRIORITY_DAYS', COUNT(*)::VARCHAR, 'Days requiring extra staffing (next 30 days)'
FROM BULB_REPLACEMENT_SCHEDULE WHERE PRIORITY = 'HIGH'

UNION ALL

SELECT 'BULBS_TO_ORDER_30D', SUM(BULBS_TO_STOCK)::VARCHAR, 'Recommended bulb inventory for next 30 days'
FROM BULB_REPLACEMENT_SCHEDULE;

-- =====================================================
-- DEMO QUERIES (Copy-Paste Ready)
-- =====================================================

-- Demo 1: Quick forecast overview
SELECT FORECAST_DATE, PREDICTED_FAILURES, PRIORITY, STAFFING_RECOMMENDATION
FROM BULB_REPLACEMENT_SCHEDULE LIMIT 10;

-- Demo 2: Weekly summary
SELECT WEEK_START, TOTAL_PREDICTED_FAILURES, AVG_DAILY_FAILURES, PRIMARY_SEASON
FROM WEEKLY_BULB_FORECAST LIMIT 8;

-- Demo 3: Monthly budget forecast
SELECT DATE_TRUNC('month', FORECAST_DATE)::DATE AS month, 
       SUM(PREDICTED_FAILURES) AS failures,
       SUM(PREDICTED_FAILURES) * 1750 AS estimated_cost_inr  -- ₹1750 per job (bulb + labor + transport)
FROM BULB_FAILURE_FORECAST_90D GROUP BY 1 ORDER BY 1;

-- Demo 4: Seasonal comparison
SELECT SEASON, SUM(PREDICTED_FAILURES) AS total_failures, 
       ROUND(AVG(PREDICTED_FAILURES), 1) AS avg_daily
FROM BULB_FAILURE_FORECAST_90D GROUP BY SEASON ORDER BY total_failures DESC;

-- Demo 5: Today's plan
SELECT * FROM BULB_REPLACEMENT_SCHEDULE WHERE FORECAST_DATE = CURRENT_DATE();

-- =====================================================
-- QUERY INDEX
-- =====================================================
-- 
-- DAILY QUERIES:
--   1.1 Next 7 Days Quick View
--   1.2 Today's Operations Briefing
--   1.3 High-Volume Days Alert
--
-- WEEKLY QUERIES:
--   2.1 Weekly Inventory Planning
--   2.2 Week-Ahead Crew Schedule
--
-- MONTHLY/SEASONAL:
--   3.1 Monthly Forecast Summary
--   3.2 Seasonal Risk Comparison
--
-- BUDGET:
--   4.1 Monthly Budget Forecast
--
-- DASHBOARD:
--   5.1 Key Forecast Metrics
--
-- =====================================================
