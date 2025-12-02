-- =====================================================
-- Phase 7: Snowflake Cortex Search Setup
-- Semantic Search for Maintenance Requests
-- =====================================================

-- Prerequisites:
-- 1. Phase 6 complete (CDC data flowing to Snowflake)
-- 2. STREETLIGHTS_DEMO database exists with all tables
-- 3. Account has Cortex Search enabled

-- IMPORTANT: CDC tables from PostgreSQL use quoted lowercase identifiers:
--   Schema: "streetlights"
--   Tables: "street_lights", "neighborhoods", etc.
--   Columns: "light_id", "status", etc.

-- NOTE: After setup, use Snowflake Intelligence for all queries.
-- See SNOWFLAKE_INTELLIGENCE_QUESTIONS.md for 40+ sample questions.

-- =====================================================
-- STEP 1: Create Analytics Schema
-- =====================================================
-- This schema will hold our Cortex Search service and ML models

USE ROLE SYSADMIN;  -- Or your role with CREATE SCHEMA privilege
USE DATABASE STREETLIGHTS_DEMO;

CREATE SCHEMA IF NOT EXISTS ANALYTICS
  COMMENT = 'Analytics schema for Cortex Search and ML models';

USE SCHEMA ANALYTICS;

-- =====================================================
-- STEP 2: Create Searchable Maintenance View
-- =====================================================
-- Cortex Search needs a text column to search on.
-- We create a view that synthesizes rich descriptions from maintenance data.
-- Note: CDC columns are lowercase quoted, output columns are uppercase

CREATE OR REPLACE VIEW MAINTENANCE_SEARCHABLE AS
SELECT 
    mr."request_id" AS REQUEST_ID,
    mr."light_id" AS LIGHT_ID,
    mr."reported_at" AS REPORTED_AT,
    mr."resolved_at" AS RESOLVED_AT,
    mr."issue_type" AS ISSUE_TYPE,
    
    -- Synthesize a searchable description from available data
    CONCAT(
        'Maintenance request for street light ', mr."light_id", '. ',
        'Issue type: ', COALESCE(mr."issue_type", 'unknown'), '. ',
        'Location: ', COALESCE(n."name", 'Unknown neighborhood'), '. ',
        'Light status: ', COALESCE(sl."status", 'unknown'), '. ',
        'Light wattage: ', COALESCE(CAST(sl."wattage" AS VARCHAR), 'unknown'), 'W. ',
        'Reported on: ', TO_VARCHAR(mr."reported_at", 'YYYY-MM-DD HH24:MI'), '. ',
        CASE 
            WHEN mr."resolved_at" IS NOT NULL 
            THEN CONCAT('Resolved on: ', TO_VARCHAR(mr."resolved_at", 'YYYY-MM-DD HH24:MI'), '.')
            ELSE 'Status: Open/Pending resolution.'
        END
    ) AS SEARCH_DESCRIPTION,
    
    -- Additional context for search results
    sl."status" AS LIGHT_STATUS,
    sl."wattage" AS WATTAGE,
    n."name" AS NEIGHBORHOOD_NAME,
    n."population" AS NEIGHBORHOOD_POPULATION,
    ST_X(TRY_TO_GEOGRAPHY(sl."location")) AS LONGITUDE,
    ST_Y(TRY_TO_GEOGRAPHY(sl."location")) AS LATITUDE,
    
    -- Resolution metrics
    CASE 
        WHEN mr."resolved_at" IS NOT NULL 
        THEN DATEDIFF('hour', mr."reported_at", mr."resolved_at")
        ELSE NULL 
    END AS RESOLUTION_HOURS,
    
    CASE 
        WHEN mr."resolved_at" IS NULL THEN 'OPEN'
        ELSE 'CLOSED'
    END AS REQUEST_STATUS

FROM STREETLIGHTS_DEMO."streetlights"."maintenance_requests" mr
LEFT JOIN STREETLIGHTS_DEMO."streetlights"."street_lights" sl ON mr."light_id" = sl."light_id"
LEFT JOIN STREETLIGHTS_DEMO."streetlights"."neighborhoods" n ON sl."neighborhood_id" = n."neighborhood_id";

-- Verify the view was created
SELECT * FROM MAINTENANCE_SEARCHABLE LIMIT 5;

-- =====================================================
-- STEP 3: Create Cortex Search Service
-- =====================================================
-- The search service enables semantic search via Snowflake Intelligence

CREATE OR REPLACE CORTEX SEARCH SERVICE MAINTENANCE_SEARCH
  ON SEARCH_DESCRIPTION
  ATTRIBUTES REQUEST_ID, LIGHT_ID, ISSUE_TYPE, NEIGHBORHOOD_NAME, REQUEST_STATUS
  WAREHOUSE = COMPUTE_WH  -- Change to your warehouse name
  TARGET_LAG = '1 hour'   -- How fresh the search index should be
  COMMENT = 'Semantic search for street light maintenance requests'
AS (
  SELECT 
    REQUEST_ID,
    LIGHT_ID,
    ISSUE_TYPE,
    NEIGHBORHOOD_NAME,
    REQUEST_STATUS,
    SEARCH_DESCRIPTION,
    REPORTED_AT,
    RESOLVED_AT,
    LIGHT_STATUS,
    WATTAGE,
    LONGITUDE,
    LATITUDE,
    RESOLUTION_HOURS
  FROM ANALYTICS.MAINTENANCE_SEARCHABLE
);

-- =====================================================
-- STEP 4: Verify Cortex Search Service
-- =====================================================

-- Check service status
SHOW CORTEX SEARCH SERVICES;

-- Describe the service
DESCRIBE CORTEX SEARCH SERVICE MAINTENANCE_SEARCH;

-- Expected output: MAINTENANCE_SEARCH service should be listed

-- =====================================================
-- PHASE 7 SUCCESS CHECKLIST
-- =====================================================
-- Run these to verify Phase 7 is complete:
--
-- [ ] Analytics schema created
-- [ ] MAINTENANCE_SEARCHABLE view created with rich descriptions
-- [ ] MAINTENANCE_SEARCH Cortex Search service created
-- [ ] Service appears in SHOW CORTEX SEARCH SERVICES
-- [ ] Wire service to Snowflake Intelligence for queries
--
-- For sample questions to use with Snowflake Intelligence,
-- see: SNOWFLAKE_INTELLIGENCE_QUESTIONS.md
-- =====================================================

