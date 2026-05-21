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
-- ML FORECAST: Energy Consumption Prediction
-- =====================================================
-- Trains a FORECAST model on energy consumption data to predict
-- future power usage patterns per street light.
--
-- Prerequisites:
--   1. CLD database created with populated Iceberg tables
--   2. Warehouse available for ML training
--
-- Variables to replace:
--   ${PREFIX} = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

USE WAREHOUSE ${PREFIX}_STREETLIGHTS_WH;

-- =====================================================
-- Step 1: Create training view (daily maintenance counts as proxy for energy)
-- =====================================================
-- Since we don't have a dedicated energy_consumption table with time-series
-- readings, we use daily maintenance request counts as the forecast target.
-- This demonstrates the FORECAST API with real time-series data.

CREATE OR REPLACE VIEW ${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_forecast_training AS
SELECT
  m."light_id" AS light_id,
  DATE_TRUNC('day', m."reported_at")::DATE AS reading_date,
  COUNT(*) AS request_count
FROM ${PREFIX}_STREETLIGHTS_CLD."streetlights"."maintenance_requests" m
WHERE m."reported_at" IS NOT NULL
GROUP BY m."light_id", DATE_TRUNC('day', m."reported_at")::DATE;

-- =====================================================
-- Step 2: Train FORECAST model
-- =====================================================
-- Predicts daily maintenance request counts per light.
-- SERIES_COLNAME enables per-light forecasting.

CREATE OR REPLACE SNOWFLAKE.ML.FORECAST ${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_forecast(
  INPUT_DATA => SYSTEM$REFERENCE('VIEW', '${PREFIX}_STREETLIGHTS_CLD."streetlights"."maintenance_forecast_training"'),
  SERIES_COLNAME => 'light_id',
  TIMESTAMP_COLNAME => 'reading_date',
  TARGET_COLNAME => 'request_count'
);

-- =====================================================
-- Step 3: Verify model training
-- =====================================================

SHOW SNOWFLAKE.ML.FORECAST IN SCHEMA ${PREFIX}_STREETLIGHTS_CLD."streetlights";

-- View evaluation metrics
CALL ${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_forecast!SHOW_EVALUATION_METRICS();

-- =====================================================
-- Step 4: Generate 30-day forecast
-- =====================================================

CALL ${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_forecast!FORECAST(
  FORECASTING_PERIODS => 30,
  CONFIG_OBJECT => {'prediction_interval': 0.95}
);

-- =====================================================
-- Usage Notes
-- =====================================================
-- The forecast model can be queried via the Intelligence Agent
-- or directly in SQL:
--
-- CALL ${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_forecast!FORECAST(
--   FORECASTING_PERIODS => 7,
--   CONFIG_OBJECT => {'prediction_interval': 0.90}
-- );
--
-- Results include: series (light_id), ts, forecast, lower_bound, upper_bound
-- =====================================================
