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
-- Databricks ML Forecast Configuration
-- =====================================================
-- Prerequisites:
--   1. Databricks ML enabled on the workspace
--   2. Setup from 01_setup.sql completed (energy_consumption_clean view exists)
--   3. Appropriate permissions for ML model creation
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

-- Set current catalog/schema
USE CATALOG <% PREFIX %>_STREETLIGHTS;
USE SCHEMA streetlights;

-- =====================================================
-- Step 1: Prepare Data for Forecasting
-- =====================================================

-- Create a dedicated forecasting table with proper data structure
CREATE OR REPLACE TABLE energy_forecast_data AS
SELECT 
    street_light_id,
    consumed_date,
    energy_consumed_kwh,
    cost,
    neighborhood,
    rate_type,
    -- Extract time features for better forecasting
    DAYOFWEEK(consumed_date) as day_of_week,
    DAYOFMONTH(consumed_date) as day_of_month,
    MONTH(consumed_date) as month,
    YEAR(consumed_date) as year,
    QUARTER(consumed_date) as quarter,
    -- Lag features for time series
    LAG(energy_consumed_kwh) OVER (
        PARTITION BY street_light_id 
        ORDER BY consumed_date
    ) as energy_lag_1,
    LAG(energy_consumed_kwh, 7) OVER (
        PARTITION BY street_light_id 
        ORDER BY consumed_date
    ) as energy_lag_7,
    LAG(energy_consumed_kwh, 30) OVER (
        PARTITION BY street_light_id 
        ORDER BY consumed_date
    ) as energy_lag_30,
    -- Rolling averages
    AVG(energy_consumed_kwh) OVER (
        PARTITION BY street_light_id 
        ORDER BY consumed_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as avg_7day,
    AVG(energy_consumed_kwh) OVER (
        PARTITION BY street_light_id 
        ORDER BY consumed_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as avg_30day
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean
WHERE consumed_date IS NOT NULL
ORDER BY street_light_id, consumed_date;

-- Create aggregated time series for overall forecasting
CREATE OR REPLACE TABLE energy_forecast_aggregated AS
SELECT 
    consumed_date,
    SUM(energy_consumed_kwh) as total_energy_kwh,
    SUM(cost) as total_cost,
    AVG(energy_consumed_kwh) as avg_energy_per_light,
    COUNT(*) as active_lights,
    -- Time features
    DAYOFWEEK(consumed_date) as day_of_week,
    DAYOFMONTH(consumed_date) as day_of_month,
    MONTH(consumed_date) as month,
    YEAR(consumed_date) as year,
    QUARTER(consumed_date) as quarter,
    -- Temperature/weather data if available (join with weather_enrichment_clean)
    NULL as avg_temperature,
    NULL as precipitation
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean
GROUP BY consumed_date
ORDER BY consumed_date;

-- =====================================================
-- Step 2: Create ML Forecast Model using AI_FORECAST
-- =====================================================

-- Databricks provides AI_FORECAST() function for automated time series forecasting
-- This creates a model that can predict future energy consumption

-- Create forecast model for individual street lights (aggregate by light)
CREATE OR REPLACE MODEL <% PREFIX %>_STREETLIGHTS_FORECAST
  INPUT_DATA => (
    SELECT 
        street_light_id,
        consumed_date as ds,
        energy_consumed_kwh as y
    FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_data
    WHERE energy_consumed_kwh IS NOT NULL
    ORDER BY street_light_id, consumed_date
  )
  FUNCTION ai_forecast
  OPTIONS (
    time_column = 'ds',
    value_column = 'y',
    id_column = 'street_light_id',
    horizon = 30, -- Forecast 30 days ahead
    confidence = 0.9, -- 90% confidence interval
    seasonality = 'auto', -- Auto-detect seasonality
    frequency = 'D', -- Daily data
    model_type = 'auto' -- Auto-select best model
  )
  COMMENT 'ML Forecast model for individual street light energy consumption'
  CATALOG <% PREFIX %>_STREETLIGHTS
  SCHEMA streetlights;

-- Create forecast model for aggregated energy consumption
CREATE OR REPLACE MODEL <% PREFIX %>_STREETLIGHTS_FORECAST_TOTAL
  INPUT_DATA => (
    SELECT 
        consumed_date as ds,
        total_energy_kwh as y
    FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_aggregated
    WHERE total_energy_kwh IS NOT NULL
    ORDER BY consumed_date
  )
  FUNCTION ai_forecast
  OPTIONS (
    time_column = 'ds',
    value_column = 'y',
    horizon = 90, -- Forecast 90 days ahead for aggregated
    confidence = 0.95, -- 95% confidence interval
    seasonality = 'auto',
    frequency = 'D',
    model_type = 'auto'
  )
  COMMENT 'ML Forecast model for total system energy consumption'
  CATALOG <% PREFIX %>_STREETLIGHTS
  SCHEMA streetlights;

-- =====================================================
-- Step 3: Generate Forecast Predictions
-- =====================================================

-- Generate forecasts for all street lights
CREATE OR REPLACE TABLE energy_forecast_predictions AS
SELECT 
    street_light_id,
    ds as forecast_date,
    y as predicted_energy_kwh,
    lo as confidence_low,
    hi as confidence_high,
    (hi - lo) / 2 as confidence_interval,
    CURRENT_TIMESTAMP() as prediction_timestamp,
   neighborhood
FROM ML.PREDICTIONS(
    MODEL <% PREFIX %>_STREETLIGHTS_FORECAST
    DATA => (
        SELECT 
            street_light_id,
            DATEADD(day, seq, MAX(consumed_date)) as ds
        FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_data
        CROSS JOIN (
            SELECT explode(sequence(1, 30)) as seq
        )
        GROUP BY street_light_id, seq
    )
);

-- Generate aggregated forecasts
CREATE OR REPLACE TABLE energy_forecast_predictions_total AS
SELECT 
    ds as forecast_date,
    y as predicted_total_energy_kwh,
    lo as confidence_low,
    hi as confidence_high,
    (hi - lo) / 2 as confidence_interval,
    CURRENT_TIMESTAMP() as prediction_timestamp
FROM ML.PREDICTIONS(
    MODEL <% PREFIX %>_STREETLIGHTS_FORECAST_TOTAL
    DATA => (
        SELECT 
            DATEADD(day, seq, MAX(consumed_date)) as ds
        FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_aggregated
        CROSS JOIN (
            SELECT explode(sequence(1, 90)) as seq
        )
        GROUP BY seq
    )
);

-- =====================================================
-- Step 4: Create Forecast Views for Easy Access
-- =====================================================

-- Daily forecast summary by neighborhood
CREATE OR REPLACE VIEW energy_forecast_daily AS
SELECT 
    forecast_date,
    neighborhood,
    AVG(predicted_energy_kwh) as avg_predicted_energy,
    SUM(predicted_energy_kwh) as total_predicted_energy,
    AVG(confidence_interval) as avg_confidence_interval,
    COUNT(*) as light_count
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions
GROUP BY forecast_date, neighborhood
ORDER BY forecast_date, total_predicted_energy DESC;

-- Neighborhood-level forecast summary
CREATE OR REPLACE VIEW energy_forecast_neighborhood AS
SELECT 
    neighborhood,
    forecast_date,
    avg_predicted_energy,
    total_predicted_energy,
    avg_confidence_interval,
    light_count,
    -- Calculate cost prediction (assuming average cost per kWh)
    total_predicted_energy * 0.15 as predicted_cost -- Approximate rate
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_daily
ORDER BY neighborhood, forecast_date;

-- =====================================================
-- Step 5: Configure Genie Forecast Tool
-- =====================================================

-- Connect the forecast model to Genie for natural language prediction queries

CREATE OR REPLACE GENIE TOOL <% PREFIX %>_STREETLIGHTS_FORECAST
  TYPE ML_FORECAST
  MODEL <% PREFIX %>_STREETLIGHTS_FORECAST_TOTAL
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  DESCRIPTION 'Time series forecasting tool for energy consumption prediction'
  INSTRUCTIONS $$
You are an energy forecasting expert with access to ML models.

**CAPABILITIES:**
- Predict future energy consumption for street lights
- Forecast costs based on consumption predictions
- Provide confidence intervals for predictions
- Handle time-based queries (days, weeks, months ahead)

**QUERY TYPES YOU CAN HANDLE:**
- "Predict energy consumption for the next 30 days"
- "What will be the energy usage tomorrow?"
- "Forecast energy costs for next month"
- "How much energy will we use in downtown next week?"
- "Show me the predicted energy trend for the next quarter"

**RESPONSE FORMAT:**
- Provide clear predictions with dates and values
- Include confidence intervals when available
- Show both energy (kWh) and cost predictions
- Provide visual-ready data tables
- Include insights about predicted trends

**CONTEXT:**
- Models are trained on historical energy consumption data
- Predictions are based on past patterns and seasonality
- Confidence intervals indicate prediction uncertainty
- All predictions are in kWh for energy, and local currency for cost
$$;

-- =====================================================
-- Step 6: Create Forecast Intent Examples
-- =====================================================

CREATE OR REPLACE GENIE INTENT EXAMPLE forecast_query
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  EXAMPLES (
    'Predict energy consumption for the next 30 days',
    'What is the forecasted energy usage for next month?',
    'Show me the energy consumption trend for Q3',
    'How much will we spend on energy next quarter?',
    'What are the predicted costs for street lighting in January?',
    'Forecast energy usage downtown for the next 7 days'
  )
  ROUTED_TO TOOL <% PREFIX %>_STREETLIGHTS_FORECAST;

-- =====================================================
-- Verification queries
-- =====================================================

-- Check that models are created
-- SHOW MODELS IN CATALOG <% PREFIX %>_STREETLIGHTS;

-- Describe models
-- DESCRIBE MODEL <% PREFIX %>_STREETLIGHTS_FORECAST;
-- DESCRIBE MODEL <% PREFIX %>_STREETLIGHTS_FORECAST_TOTAL;

-- Test predictions
-- SELECT * FROM ML.PREDICTIONS(
--   MODEL <% PREFIX %>_STREETLIGHTS_FORECAST
--   DATA => (
--     SELECT 
--         street_light_id,
--         DATEADD(day, 1, MAX(consumed_date)) as ds
--     FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_data
--     GROUP BY street_light_id
--   )
-- ) LIMIT 10;

-- Check prediction tables
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions LIMIT 10;
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions_total LIMIT 10;