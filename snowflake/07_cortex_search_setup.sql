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
-- Uses CTEs for modularity, readability, and maintainability.
-- Note: CDC columns are lowercase quoted, output columns are uppercase

CREATE OR REPLACE VIEW MAINTENANCE_SEARCHABLE AS
WITH 
    -- CTE 1: Base maintenance requests with standardized column names
    maintenance_base AS (
        SELECT 
            "request_id" AS request_id,
            "light_id" AS light_id,
            "reported_at" AS reported_at,
            "resolved_at" AS resolved_at,
            "issue_type" AS issue_type
        FROM STREETLIGHTS_DEMO."streetlights"."maintenance_requests"
    ),
    
    -- CTE 2: Street light details with parsed geography
    light_details AS (
        SELECT 
            "light_id" AS light_id,
            "neighborhood_id" AS neighborhood_id,
            "status" AS status,
            "wattage" AS wattage,
            TRY_TO_GEOGRAPHY("location") AS geo_location,
            ST_X(TRY_TO_GEOGRAPHY("location")) AS longitude,
            ST_Y(TRY_TO_GEOGRAPHY("location")) AS latitude
        FROM STREETLIGHTS_DEMO."streetlights"."street_lights"
    ),
    
    -- CTE 3: Neighborhood details
    neighborhood_details AS (
        SELECT 
            "neighborhood_id" AS neighborhood_id,
            "name" AS name,
            "population" AS population
        FROM STREETLIGHTS_DEMO."streetlights"."neighborhoods"
    ),
    
    -- CTE 4: Join all data sources
    joined_data AS (
        SELECT 
            mb.request_id,
            mb.light_id,
            mb.reported_at,
            mb.resolved_at,
            mb.issue_type,
            ld.status AS light_status,
            ld.wattage,
            ld.geo_location,
            ld.longitude,
            ld.latitude,
            nd.name AS neighborhood_name,
            nd.population AS neighborhood_population
        FROM maintenance_base mb
        LEFT JOIN light_details ld ON mb.light_id = ld.light_id
        LEFT JOIN neighborhood_details nd ON ld.neighborhood_id = nd.neighborhood_id
    )

-- Final SELECT: Build computed columns from joined data
SELECT 
    request_id AS REQUEST_ID,
    light_id AS LIGHT_ID,
    reported_at AS REPORTED_AT,
    resolved_at AS RESOLVED_AT,
    issue_type AS ISSUE_TYPE,
    
    -- Synthesize a searchable description from available data
    CONCAT(
        'Maintenance request for street light ', light_id, '. ',
        'Issue type: ', COALESCE(issue_type, 'unknown'), '. ',
        'Location: ', COALESCE(neighborhood_name, 'Unknown neighborhood'), '. ',
        'Light status: ', COALESCE(light_status, 'unknown'), '. ',
        'Light wattage: ', COALESCE(CAST(wattage AS VARCHAR), 'unknown'), 'W. ',
        'Reported on: ', TO_VARCHAR(reported_at, 'YYYY-MM-DD HH24:MI'), '. ',
        CASE 
            WHEN resolved_at IS NOT NULL 
            THEN CONCAT('Resolved on: ', TO_VARCHAR(resolved_at, 'YYYY-MM-DD HH24:MI'), '.')
            ELSE 'Status: Open/Pending resolution.'
        END
    ) AS SEARCH_DESCRIPTION,
    
    -- Additional context for search results
    light_status AS LIGHT_STATUS,
    wattage AS WATTAGE,
    neighborhood_name AS NEIGHBORHOOD_NAME,
    neighborhood_population AS NEIGHBORHOOD_POPULATION,
    longitude AS LONGITUDE,
    latitude AS LATITUDE,
    
    -- Google Maps location URL
    CASE 
        WHEN geo_location IS NOT NULL 
        THEN CONCAT('https://www.google.com/maps?q=', latitude, ',', longitude)
        ELSE NULL 
    END AS GOOGLE_MAPS_URL,
    
    -- Resolution metrics
    CASE 
        WHEN resolved_at IS NOT NULL 
        THEN DATEDIFF('hour', reported_at, resolved_at)
        ELSE NULL 
    END AS RESOLUTION_HOURS,
    
    CASE 
        WHEN resolved_at IS NULL THEN 'OPEN'
        ELSE 'CLOSED'
    END AS REQUEST_STATUS

FROM joined_data;

-- Verify the view was created
SELECT * FROM MAINTENANCE_SEARCHABLE LIMIT 5;

-- =====================================================
-- STEP 3: Create Cortex Search Service
-- =====================================================
-- The search service enables semantic search via Snowflake Intelligence

CREATE OR REPLACE CORTEX SEARCH SERVICE MAINTENANCE_SEARCH
  ON SEARCH_DESCRIPTION
  ATTRIBUTES REQUEST_ID, LIGHT_ID, ISSUE_TYPE, NEIGHBORHOOD_NAME, REQUEST_STATUS
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 min' -- just for demo purposes, for production we would set to value that is more appropriate for the data and the business
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
    GOOGLE_MAPS_URL,
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

