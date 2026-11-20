-- Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
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
-- Forecasting with ai_forecast()  (Databricks equivalent of ML FORECAST)
-- =====================================================
-- Run via: databricks bundle run forecast -t dev
-- ai_forecast() requires a SERVERLESS SQL warehouse — the bundle creates
-- ${var.prefix}_STREETLIGHTS_WH with enable_serverless_compute: true.
-- Docs: https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_forecast
-- =====================================================

USE CATALOG ${var.prefix}_STREETLIGHTS;
USE SCHEMA streetlights;

-- Daily total energy series (training data for the forecast)
CREATE OR REPLACE TABLE energy_consumption_daily AS
SELECT
    consumed_date AS date,
    SUM(energy_consumed_kwh) AS total_kwh
FROM energy_consumption_clean
GROUP BY consumed_date;

-- 30-day forecast of total daily energy consumption
-- Output columns: date, total_kwh_forecast, total_kwh_upper, total_kwh_lower
CREATE OR REPLACE TABLE energy_forecast AS
SELECT * FROM ai_forecast(
    observed  => TABLE(energy_consumption_daily),
    horizon   => DATEADD(day, 30, (SELECT MAX(date) FROM energy_consumption_daily)),
    time_col  => 'date',
    value_col => 'total_kwh',
    frequency => 'day'
);

-- Per-neighborhood forecast (grouped)
CREATE OR REPLACE TABLE energy_forecast_by_neighborhood AS
SELECT * FROM ai_forecast(
    observed  => TABLE(
        SELECT consumed_date AS date, neighborhood, SUM(energy_consumed_kwh) AS kwh
        FROM energy_consumption_clean
        GROUP BY consumed_date, neighborhood
    ),
    horizon   => DATEADD(day, 30, (SELECT MAX(consumed_date) FROM energy_consumption_clean)),
    time_col  => 'date',
    value_col => 'kwh',
    group_col => 'neighborhood',
    frequency => 'day'
);

-- =====================================================
-- Verification
-- =====================================================
-- SELECT * FROM energy_forecast ORDER BY date LIMIT 10;
-- SELECT * FROM energy_forecast_by_neighborhood ORDER BY date LIMIT 10;
