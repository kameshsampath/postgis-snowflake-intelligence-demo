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
-- Snowflake Openflow Quick Reference
-- PostgreSQL CDC Configuration
-- =====================================================

-- https://www.snowflake.com/en/developers/guides/getting-started-with-openflow-spcs/

-- =====================================================
-- PART 1: Snowflake Prerequisites (Run These First)
-- =====================================================

-- https://www.snowflake.com/en/developers/guides/getting-started-with-openflow-spcs/

-- If result is 'DISABLED', run:
-- CALL SYSTEM$ENABLE_BEHAVIOR_CHANGE_BUNDLE('2025_06');

-- Step 4: Create destination database (optional - Openflow can create automatically)
-- !jinja

USE ROLE KAMESH_DEMOS;

CREATE DATABASE IF NOT EXISTS STREETLIGHTS_DEMO
  COMMENT = 'Street lights data from PostgreSQL CDC via Openflow';

-- =====================================================
-- PART 2: Openflow UI Setup
-- =====================================================
-- https://www.snowflake.com/en/developers/guides/getting-started-with-openflow-postgresql-cdc/

-- =====================================================
-- IMPORTANT: CDC Table Naming Convention
-- =====================================================
-- PostgreSQL CDC creates tables with QUOTED LOWERCASE identifiers:
--   Schema: "streetlights" (not PUBLIC)
--   Tables: "street_lights", "neighborhoods", etc.
--   Columns: "light_id", "status", etc.
--
-- Always use quoted lowercase when referencing CDC tables!
-- =====================================================

-- =====================================================
-- PART 3: Verification Queries
-- =====================================================

-- After Openflow pipeline is running, verify with these queries:

USE DATABASE STREETLIGHTS_DEMO;

-- Check tables were created (schema is "streetlights" from PostgreSQL)
SHOW TABLES IN SCHEMA "streetlights";

-- Expected tables:
-- - street_lights
-- - neighborhoods  
-- - maintenance_requests
-- - suppliers
-- - weather_enrichment
-- - demographics_enrichment
-- - power_grid_enrichment

-- =====================================================
-- STEP 5: Verify Data Loaded
-- =====================================================

-- Check row counts (using quoted lowercase identifiers)
SELECT 'street_lights' as table_name, COUNT(*) as row_count FROM "streetlights"."street_lights"
UNION ALL
SELECT 'neighborhoods', COUNT(*) FROM "streetlights"."neighborhoods"
UNION ALL
SELECT 'maintenance_requests', COUNT(*) FROM "streetlights"."maintenance_requests"
UNION ALL
SELECT 'suppliers', COUNT(*) FROM "streetlights"."suppliers"
UNION ALL
SELECT 'weather_enrichment', COUNT(*) FROM "streetlights"."weather_enrichment"
UNION ALL
SELECT 'demographics_enrichment', COUNT(*) FROM "streetlights"."demographics_enrichment"
UNION ALL
SELECT 'power_grid_enrichment', COUNT(*) FROM "streetlights"."power_grid_enrichment"
ORDER BY table_name;

-- =====================================================
-- STEP 6: Test Spatial Data
-- =====================================================
-- Verify geography columns exist
DESC TABLE "streetlights"."street_lights";
-- Look for: location GEOGRAPHY

DESC TABLE "streetlights"."neighborhoods";
-- Look for: boundary GEOGRAPHY

DESC TABLE "streetlights"."suppliers";
-- Look for: location GEOGRAPHY

-- Test spatial query (using quoted lowercase columns)
SELECT 
  "light_id",
  ST_X("location") as longitude,
  ST_Y("location") as latitude,
  "status",
  "neighborhood_id"
FROM "streetlights"."street_lights"
LIMIT 10;

-- Test distance calculation
SELECT 
  l1."light_id" as light_1,
  l2."light_id" as light_2,
  ST_DISTANCE(l1."location", l2."location") as distance_meters
FROM "streetlights"."street_lights" l1
CROSS JOIN "streetlights"."street_lights" l2
WHERE l1."light_id" = 'SL-0001'
  AND l2."light_id" != 'SL-0001'
ORDER BY distance_meters
LIMIT 5;

-- =====================================================
-- STEP 7: Test CDC (Optional)
-- =====================================================
-- After making changes in PostgreSQL, check here:

-- Example: Check if status update came through
SELECT "light_id", "status", "last_maintenance"
FROM "streetlights"."street_lights"
WHERE "light_id" = 'SL-0001';

-- =====================================================
-- USEFUL QUERIES
-- =====================================================

-- Enriched view: Lights with all context
SELECT 
  sl."light_id",
  sl."status",
  ST_X(sl."location") as longitude,
  ST_Y(sl."location") as latitude,
  n."name" as neighborhood_name,
  n."population",
  w."season",
  w."failure_risk_score",
  w."predicted_failure_date",
  d."population_density",
  d."urban_classification",
  p."grid_zone",
  p."avg_load_percent"
FROM "streetlights"."street_lights" sl
LEFT JOIN "streetlights"."neighborhoods" n ON sl."neighborhood_id" = n."neighborhood_id"
LEFT JOIN "streetlights"."weather_enrichment" w ON sl."light_id" = w."light_id" AND w."season" = 'monsoon'
LEFT JOIN "streetlights"."demographics_enrichment" d ON n."neighborhood_id" = d."neighborhood_id"
LEFT JOIN "streetlights"."power_grid_enrichment" p ON sl."light_id" = p."light_id"
LIMIT 10;

-- Faulty lights with nearest supplier
WITH faulty AS (
  SELECT "light_id", "location", "status", "neighborhood_id"
  FROM "streetlights"."street_lights"
  WHERE "status" = 'faulty'
),
nearest_supplier AS (
  SELECT 
    f."light_id",
    s."supplier_id",
    s."name" as supplier_name,
    s."contact_phone",
    ST_DISTANCE(f."location", s."location")/1000 as distance_km,
    ROW_NUMBER() OVER (PARTITION BY f."light_id" ORDER BY ST_DISTANCE(f."location", s."location")) as rn
  FROM faulty f
  CROSS JOIN "streetlights"."suppliers" s
)
SELECT 
  "light_id",
  supplier_name,
  "contact_phone",
  ROUND(distance_km, 2) as distance_km
FROM nearest_supplier
WHERE rn = 1
ORDER BY distance_km;

-- =====================================================
-- PHASE 6 SUCCESS CHECKLIST
-- =====================================================
-- Run these to verify Phase 6 is complete:
--
-- [ ] Connection created and active
-- [ ] Database STREETLIGHTS_DEMO exists
-- [ ] Schema "streetlights" exists (quoted lowercase)
-- [ ] 7 tables created
-- [ ] Row counts match PostgreSQL
-- [ ] Geography columns working
-- [ ] CDC test successful (update flows from PG to SF)
--
-- =====================================================

