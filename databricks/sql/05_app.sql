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
-- Databricks App (Streamlit) Configuration
-- =====================================================
-- Prerequisites:
--   1. Databricks Apps (Streamlit) enabled on the workspace
--   2. Setup from 01_setup.sql completed
--   3. Genie space from 02_genie_space.sql configured
--   4. Vector Search from 03_vector_search.sql configured
--   5. Forecast models from 04_forecast.sql created
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

-- =====================================================
-- Step 1: Create Databricks App Configuration
-- =====================================================

-- Note: Databricks Apps are primarily configured via UI or REST API
-- The SQL below provides the equivalent configuration that would be created via UI
-- and the necessary support objects in Unity Catalog

-- Set current catalog/schema
USE CATALOG <% PREFIX %>_STREETLIGHTS;
USE SCHEMA streetlights;

-- =====================================================
-- Step 2: Create App Database Schema
-- =====================================================

-- Create schema for app-specific objects
CREATE SCHEMA IF NOT EXISTS streetlights_app
  COMMENT 'Schema for Databricks App objects and queries';

USE SCHEMA streetlights_app;

-- =====================================================
-- Step 3: Create App-optimized Views
-- =====================================================

-- KPI dashboard view
CREATE OR REPLACE VIEW app_kpi_dashboard AS
SELECT 
    -- Infrastructure KPIs
    (SELECT COUNT(*) FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean) as total_lights,
    (SELECT COUNT(*) FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean WHERE status = 'Faulty') as faulty_lights,
    (SELECT COUNT(*) FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean WHERE status = 'Active') as active_lights,
    
    -- Maintenance KPIs
    (SELECT COUNT(*) FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean WHERE status = 'Completed') as completed_maintenance,
    (SELECT COUNT(*) FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean WHERE status = 'Pending') as pending_maintenance,
    (SELECT AVG(cost) FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean WHERE cost IS NOT NULL) as avg_maintenance_cost,
    
    -- Energy KPIs
    (SELECT SUM(energy_consumed_kwh) FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean) as total_energy_kwh,
    (SELECT SUM(cost) FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean) as total_energy_cost,
    (SELECT AVG(energy_consumed_kwh) FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean) as avg_daily_energy_kwh,
    
    -- Forecast KPIs
    (SELECT SUM(predicted_energy_kwh) FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions WHERE forecast_date = CURRENT_DATE()) as predicted_today_energy,
    
    -- Neighborhood insights
    (SELECT COUNT(DISTINCT neighborhood) FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean) as total_neighborhoods,
    
    CURRENT_TIMESTAMP() as last_updated;

-- Neighborhood summary view for map visualizations
CREATE OR REPLACE VIEW app_neighborhood_summary AS
SELECT 
    IfNull(sl.neighborhood, 'Unknown') as neighborhood,
    COUNT(DISTINCT sl.street_light_id) as total_lights,
    COUNT(DISTINCT CASE WHEN sl.status = 'Faulty' THEN sl.street_light_id END) as faulty_lights,
    COUNT(DISTINCT CASE WHEN sl.status = 'Active' THEN sl.street_light_id END) as active_lights,
    AVG(sl.wattage) as avg_wattage,
    
    -- Energy data
    COALESCE(SUM(ec.energy_consumed_kwh), 0) as total_energy_kwh,
    COALESCE(AVG(ec.energy_consumed_kwh), 0) as avg_energy_kwh,
    COALESCE(SUM(ec.cost), 0) as total_energy_cost,
    
    -- Maintenance data
    COUNT(DISTINCT mr.maintenance_id) as total_maintenance_count,
    AVG(CASE WHEN mr.cost IS NOT NULL THEN mr.cost ELSE 0 END) as avg_maintenance_cost,
    COUNT(DISTINCT CASE WHEN mr.status = 'Pending' THEN mr.maintenance_id END) as pending_maintenance,
    
    -- Geographic center for map display
    AVG(sl.latitude) as center_lat,
    AVG(sl.longitude) as center_lng,
    
    CURRENT_TIMESTAMP() as last_updated
FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean sl
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean ec 
    ON sl.street_light_id = ec.street_light_id 
    AND ec.consumed_date >= DATEADD(day, -30, CURRENT_DATE())
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean mr 
    ON sl.street_light_id = mr.street_light_id 
    AND mr.maintenance_date >= DATEADD(day, -90, CURRENT_DATE())
GROUP BY sl.neighborhood
ORDER BY total_lights DESC;

-- Street light detail view for individual light inspection
CREATE OR REPLACE VIEW app_streetlight_detail AS
SELECT 
    sl.*,
    -- Latest maintenance info
    mr.maintenance_date as last_maintenance_date,
    mr.description as last_maintenance_description,
    mr.cost as last_maintenance_cost,
    mr.status as last_maintenance_status,
    mr.severity as last_maintenance_severity,
    
    -- Latest energy consumption
    ec.consumed_date as latest_consumption_date,
    ec.energy_consumed_kwh as latest_consumption_kwh,
    ec.cost as latest_consumption_cost,
    
    -- Forecast for next 30 days
    COALESCE(fp.predicted_energy_kwh, 0) as forecast_energy_kwh,
    COALESCE(fp.confidence_low, 0) as forecast_low_kwh,
    COALESCE(fp.confidence_high, 0) as forecast_high_kwh,
    
    -- GeoJSON for map display
    ST_AsGeoJSON(ST_Point(sl.longitude, sl.latitude)) as geojson,
    
    CURRENT_TIMESTAMP() as last_updated
FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean sl
LEFT JOIN (
    SELECT street_light_id, MAX(maintenance_date) as max_date
    FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean
    GROUP BY street_light_id
) latest_mr ON sl.street_light_id = latest_mr.street_light_id
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean mr 
    ON latest_mr.street_light_id = mr.street_light_id AND latest_mr.max_date = mr.maintenance_date

LEFT JOIN (
    SELECT street_light_id, MAX(consumed_date) as max_date
    FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean
    GROUP BY street_light_id
) latest_ec ON sl.street_light_id = latest_ec.street_light_id
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean ec 
    ON latest_ec.street_light_id = ec.street_light_id AND latest_ec.max_date = ec.consumed_date

LEFT JOIN (
    SELECT street_light_id, MIN(forecast_date) as forecast_date
    FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions
    GROUP BY street_light_id
) latest_fp ON sl.street_light_id = latest_fp.street_light_id
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions fp 
    ON latest_fp.street_light_id = fp.street_light_id AND latest_fp.forecast_date = fp.forecast_date

ORDER BY sl.street_light_id;

-- Maintenance records view for faulty lights analysis
CREATE OR REPLACE VIEW app_faulty_lights AS
SELECT 
    sl.street_light_id,
    sl.neighborhood,
    sl.status,
    sl.longitude,
    sl.latitude,
    sl.bulb_type,
    sl.wattage,
    sl.installation_date,
    sl.last_maintenance_date as installed_last_maintenance,
    
    mr.maintenance_id,
    mr.maintenance_date,
    mr.maintenance_type,
    mr.description,
    mr.status as maintenance_status,
    mr.cost,
    mr.severity,
    mr.notes,
    
    -- Days since last maintenance
    DATEDIFF(day, COALESCE(mr.maintenance_date, sl.installation_date), CURRENT_DATE()) as days_since_work,
    
    -- Map link
    CONCAT('https://www.google.com/maps/search/?api=1&query=', sl.latitude, ',', sl.longitude) as map_link,
    
    CURRENT_TIMESTAMP() as last_updated
FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean sl
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean mr 
    ON sl.street_light_id = mr.street_light_id
WHERE sl.status = 'Faulty'
ORDER BY mr.maintenance_date DESC NULLS LAST, sl.street_light_id;

-- Energy analytics view for consumption analysis
CREATE OR REPLACE VIEW app_energy_analytics AS
SELECT 
    ec.consumed_date,
    ec.street_light_id,
    ec.energy_consumed_kwh,
    ec.cost,
    ec.rate_type,
    sl.neighborhood,
    sl.bulb_type,
    sl.wattage,
    sl.status as light_status,
    
    -- 7-day moving average
    AVG(ec.energy_consumed_kwh) OVER (
        PARTITION BY ec.street_light_id 
        ORDER BY ec.consumed_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as energy_7day_avg,
    
    -- Forecast comparison
    COALESCE(fp.predicted_energy_kwh, 0) as forecast_energy_kwh,
    COALESCE(fp.confidence_low, 0) as forecast_low_kwh,
    COALESCE(fp.confidence_high, 0) as forecast_high_kwh,
    
    -- Percentage difference from forecast
    CASE 
        WHEN fp.predicted_energy_kwh > 0 AND ec.energy_consumed_kwh > 0
        THEN ROUND(((ec.energy_consumed_kwh - fp.predicted_energy_kwh) / fp.predicted_energy_kwh) * 100, 2)
        ELSE NULL 
    END as pct_diff_from_forecast,
    
    -- Day of week and month for grouping
    DAYOFWEEK(ec.consumed_date) as day_of_week,
    DAYNAME(ec.consumed_date) as day_name,
    MONTH(ec.consumed_date) as month,
    MONTHNAME(ec.consumed_date) as month_name,
    
    CURRENT_TIMESTAMP() as last_updated
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean ec
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean sl 
    ON ec.street_light_id = sl.street_light_id
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_predictions fp 
    ON ec.street_light_id = fp.street_light_id AND ec.consumed_date = fp.forecast_date
ORDER BY ec.consumed_date DESC, ec.street_light_id;

-- Forecast visualization view
CREATE OR REPLACE VIEW app_forecast_visualization AS
SELECT 
    forecast_date,
    neighborhood,
    avg_predicted_energy,
    total_predicted_energy,
    avg_confidence_interval,
    light_count,
    predicted_cost,
    
    -- Calculate trend indicators
    LAG(avg_predicted_energy) OVER (PARTITION BY neighborhood ORDER BY forecast_date) as prev_avg_energy,
    ROUND(
        CASE 
            WHEN LAG(avg_predicted_energy) OVER (PARTITION BY neighborhood ORDER BY forecast_date) > 0
            THEN ((avg_predicted_energy - LAG(avg_predicted_energy) OVER (PARTITION BY neighborhood ORDER BY forecast_date)) / 
                   LAG(avg_predicted_energy) OVER (PARTITION BY neighborhood ORDER BY forecast_date)) * 100
            ELSE NULL 
        END, 2
    ) as pct_change_from_prev_day,
    
    -- Weekday/weekend flag
    CASE WHEN DAYOFWEEK(forecast_date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END as day_type,
    
    -- Month for grouping
    MONTHNAME(forecast_date) as month_name,
    
    CURRENT_TIMESTAMP() as last_updated
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_forecast_daily
ORDER BY forecast_date, total_predicted_energy DESC;

-- =====================================================
-- Step 4: Create App Permissions
-- =====================================================

-- Grant SELECT on all app views to appropriate users
-- In production, adjust permissions based on your security requirements

-- GRANT USAGE ON SCHEMA <% PREFIX %>_STREETLIGHTS.streetlights_app TO `users`;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA <% PREFIX %>_STREETLIGHTS.streetlights_app TO `users`;

-- =====================================================
-- Step 5: Configure Databricks App Metadata
-- =====================================================

-- Note: Databricks App configuration is typically done via UI or REST API
-- The following commands represent the equivalent SQL operations

-- Register the app in the workspace
-- CREATE DATABRICKS APP IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_APP
--   TYPE STREAMLIT
--   CATALOG <% PREFIX %>_STREETLIGHTS
--   SCHEMA streetlights_app
--   DESCRIPTION 'Streetlights Intelligence Dashboard - Databricks Perspective'
--   tags ('demo', 'streetlights', 'intelligence', 'databricks');

-- =====================================================
-- Step 6: Create Sample Streamlit App File
-- =====================================================

-- This would be saved as a .py file in the workspace
-- See the databricks.yml file for the app file configuration

-- The streamlit app would include:
-- 1. KPI dashboard page
-- 2. Infrastructure map visualization
-- 3. Faulty lights inspector
-- 4. Energy analytics and forecasting
-- 5. Maintenance history and trends

-- =====================================================
-- Step 7: Deploy and Configure App
-- =====================================================

-- Deploy the app via Databricks CLI:
-- databricks bundle deploy -t dev

-- Or via UI: Workspace → Apps → Create App → Streamlit

-- thimpApp configuration would include:
-- - App name: <% PREFIX %>_STREETLIGHTS_APP
-- - Entry point: The streamlit Python file
-- - Cluster: Shared or dedicated cluster
-- - Permissions: Who can view/edit the app

-- =====================================================
-- Verification queries
-- =====================================================

-- Check that all app views exist and are accessible
-- SHOW VIEWS IN <% PREFIX %>_STREETLIGHTS.streetlights_app;

-- Test KPI dashboard
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights_app.app_kpi_dashboard;

-- Test neighborhood summary
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights_app.app_neighborhood_summary LIMIT 5;

-- Test faulty lights view
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights_app.app_faulty_lights LIMIT 10;

-- Test energy analytics
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights_app.app_energy_analytics LIMIT 10;

-- Test forecast visualization
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights_app.app_forecast_visualization LIMIT 10;