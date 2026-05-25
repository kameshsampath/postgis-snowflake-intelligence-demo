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
-- Snowflake Setup: Warehouse + Main Database + Grants
-- =====================================================
-- Prerequisites:
--   1. Snowflake Postgres instance created with managed storage
--   2. pg_lake extension enabled and Iceberg tables populated
--   3. Account params: ENABLE_SNOWFLAKE_POSTGRES, ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
--   <% ROLE %>   = your working role that should own the objects (e.g., KAMESH_DEMOS)
-- =====================================================

-- Step 1: Create warehouse for analytics workloads (run as admin role)
CREATE WAREHOUSE IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  COMMENT = 'Streetlights demo analytics warehouse';

USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

-- Step 2: Create main analytics database
-- All Snowflake demo objects (Semantic View, Cortex Search, Agent) live here.
CREATE DATABASE IF NOT EXISTS <% PREFIX %>_STREETLIGHTS
  COMMENT = 'Streetlights demo analytics database';

CREATE SCHEMA IF NOT EXISTS <% PREFIX %>_STREETLIGHTS.PUBLIC;

-- Step 3: Grant access to working role
-- Run these as ACCOUNTADMIN (or the role used to create the warehouse/database).
-- This ensures the working role can create all Snowflake objects in step 5–7.
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH TO ROLE <% ROLE %>;
GRANT USAGE ON DATABASE <% PREFIX %>_STREETLIGHTS TO ROLE <% ROLE %>;
GRANT USAGE ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
GRANT CREATE SEMANTIC VIEW ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
GRANT CREATE AGENT ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
GRANT CREATE STREAMLIT ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
USE ROLE <% ROLE %>;

-- =====================================================
-- Step 4 (post-CLD): CLD Table Access Grants
-- =====================================================
-- Run AFTER step-4 creates the CLD database.
-- Bulk GRANT ON ALL TABLES IN SCHEMA silently no-ops for CLD Iceberg tables —
-- each table must be granted individually.
-- =====================================================
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE <% PREFIX %>_STREETLIGHTS_CLD TO ROLE <% ROLE %>;
GRANT USAGE ON SCHEMA <% PREFIX %>_STREETLIGHTS_CLD."streetlights" TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."street_lights"        TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."maintenance_records"  TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."energy_consumption"   TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."light_sensors"        TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."weather_enrichment"   TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."demographics"         TO ROLE <% ROLE %>;
GRANT SELECT ON TABLE <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."power_grid_zones"     TO ROLE <% ROLE %>;
USE ROLE <% ROLE %>;

