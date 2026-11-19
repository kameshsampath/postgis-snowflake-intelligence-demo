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
-- Databricks Setup: Catalog + Schema + Lakebase Configuration
-- =====================================================
-- Prerequisites:
--   1. Databricks workspace with Unity Catalog enabled
--   2. Lakebase instance created and connected
--   3. Appropriate permissions for catalog creation
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
--   <% LAKEBASE_INSTANCE %> = your Lakebase instance name
-- =====================================================

-- Step 1: Create catalog for the demo
CREATE CATALOG IF NOT EXISTS <% PREFIX %>_STREETLIGHTS
  COMMENT 'PostGIS Data Intelligence Demo - Databricks Perspective'
  PROPERTIES ('purpose' = 'DEMO', 'attribution' = 'streetlights-demo');

-- Step 2: Create schema within catalog
CREATE SCHEMA IF NOT EXISTS <% PREFIX %>_STREETLIGHTS.streetlights
  COMMENT 'Streetlights demo schema for Lakebase data';

-- Set current catalog/schema for subsequent operations
USE CATALOG <% PREFIX %>_STREETLIGHTS;
USE SCHEMA streetlights;

-- Step 3: Create SQL Warehouse for query processing
-- Note: This needs to be created via Databricks UI or REST API
-- The SQL below assumes the warehouse already exists
-- CREATE SQL WAREHOUSE IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_WH
--   WITH (SIZE = '2X-Small', AUTO_STOP_MINS = 30)
--   COMMENT 'SQL warehouse for streetlights demo queries';

USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

-- Step 4: Configure Lakebase connection
-- Lakebase automatically syncs with Unity Catalog
-- Tables from the connected PostgreSQL database become available in UC

-- Step 5: Create curated views matching Snowflake Semantic View structure
-- These views provide the semantic layer for Genie

-- Street lights view with spatial and operational metadata
CREATE OR REPLACE VIEW street_lights_clean AS
SELECT 
    street_light_id,
    longitude,
    latitude,
    neighborhood,
    installation_date,
    bulb_type,
    wattage,
    status,
    height,
    pole_material,
    last_maintenance_date,
    installed_by,
    notes,
    power_grid_zone_id,
    -- Add computed field for map display
    ST_POINT(longitude, latitude) as location
FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights;

-- Maintenance records view for text search and analysis
CREATE OR REPLACE VIEW maintenance_records_clean AS
SELECT 
    maintenance_id,
    street_light_id,
    maintenance_date,
    maintenance_type,
    description,
    status,
    cost,
    technician_id,
    start_time,
    end_time,
    notes,
    severity,
    -- Combine text fields for vector search
    CONCAT(
        COALESCE(description, ''),
        CASE WHEN description IS NOT NULL AND notes IS NOT NULL THEN ' ' ELSE '' END,
        COALESCE(notes, '')
    ) as full_text,
    -- Extract neighborhood from street_light_id join
    sl.neighborhood
FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records
LEFT JOIN <% PREFIX %>_STREETLIGHTS.streetlights.street_lights sl 
    ON maintenance_records.street_light_id = sl.street_light_id;

-- Energy consumption view for forecasting
CREATE OR REPLACE VIEW energy_consumption_clean AS
SELECT 
    consumption_id,
    street_light_id,
    consumed_date,
    energy_consumed_kwh,
    cost,
    rate_type,
    neighborhood,
    -- Calculate daily average
    AVG(energy_consumed_kwh) OVER (
        PARTITION BY street_light_id 
        ORDER BY consumed_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as avg_7day_consumption
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption;

-- Weather enrichment view
CREATE OR REPLACE VIEW weather_enrichment_clean AS
SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.weather_enrichment;

-- Light sensors view
CREATE OR REPLACE VIEW light_sensors_clean AS
SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.light_sensors;

-- Demographics view
CREATE OR REPLACE VIEW demographics_clean AS
SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.demographics;

-- Power grid zones view
CREATE OR REPLACE VIEW power_grid_zones_clean AS
SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.power_grid_zones;

-- Step 6: Grant permissions to users
-- In production, you would grant appropriate permissions based on your security requirements
-- Example: Grant SELECT on all views to users group
-- GRANT SELECT ON ALL VIEWS IN SCHEMA <% PREFIX %>_STREETLIGHTS.streetlights TO `users`;

-- =====================================================
-- Verification queries (run these to confirm setup)
-- =====================================================

-- SELECT COUNT(*) as table_count FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights;
-- SELECT COUNT(*) as maintenance_count FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records;
-- SELECT COUNT(*) as consumption_count FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption;

-- Check that views are accessible
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean LIMIT 10;
-- SELECT * FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean LIMIT 10;
