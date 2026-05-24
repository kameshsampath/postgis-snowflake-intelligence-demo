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
-- Snowflake Setup: Warehouse + CLD Database
-- =====================================================
-- Prerequisites:
--   1. Snowflake Postgres instance created with managed storage
--   2. pg_lake extension enabled and Iceberg tables populated
--   3. Account params: ENABLE_SNOWFLAKE_POSTGRES, ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
--   ${PG_INSTANCE} = your Snowflake Postgres instance name
-- =====================================================

-- Step 1: Create warehouse for analytics workloads
CREATE WAREHOUSE IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  COMMENT = 'Streetlights demo analytics warehouse';

USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

-- Step 2: Create Catalog-Linked Database from Snowflake Postgres pg_lake
-- This surfaces all Iceberg tables from the PG instance as read-only tables.
-- Tables appear under: <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."<table_name>"
--
-- NOTE: The actual CLD creation is handled by the $snowflake-postgres skill
-- in Step 4 of the demo workflow. The syntax below is for reference:
--
-- CREATE DATABASE <% PREFIX %>_STREETLIGHTS_CLD
--   CATALOG_SOURCE = SNOWFLAKE_POSTGRES
--   CATALOG_NAME = '${PG_INSTANCE}'
--   AUTO_REFRESH = TRUE;

-- Step 3: Verify CLD tables are visible (run after CLD creation)
-- SHOW TABLES IN SCHEMA <% PREFIX %>_STREETLIGHTS_CLD."streetlights";
--
-- Expected tables:
--   "street_lights"
--   "maintenance_records"
--   "energy_consumption"
--   "light_sensors"
--   "weather_enrichment"
--   "demographics"
--   "power_grid_zones"

-- Step 4: Verify row counts
-- SELECT 'street_lights' AS table_name, COUNT(*) AS row_count
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."street_lights"
-- UNION ALL
-- SELECT 'maintenance_records', COUNT(*)
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."maintenance_records"
-- UNION ALL
-- SELECT 'energy_consumption', COUNT(*)
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."energy_consumption"
-- UNION ALL
-- SELECT 'light_sensors', COUNT(*)
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."light_sensors"
-- UNION ALL
-- SELECT 'weather_enrichment', COUNT(*)
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."weather_enrichment"
-- UNION ALL
-- SELECT 'demographics', COUNT(*)
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."demographics"
-- UNION ALL
-- SELECT 'power_grid_zones', COUNT(*)
--   FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."power_grid_zones"
-- ORDER BY table_name;
