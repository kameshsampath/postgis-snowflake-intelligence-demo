-- =====================================================
-- Phase 11: Snowflake Cortex Analyst Setup
-- Semantic Model for Structured Analytics
-- =====================================================

-- Prerequisites:
-- 1. Phase 6 complete (CDC data flowing to Snowflake)
-- 2. Phase 7 complete (Cortex Search configured)
-- 3. streetlights_semantic_model.yaml file ready

-- This phase adds Cortex Analyst capabilities to complement
-- Cortex Search, enabling two types of AI-powered queries:
--   - Cortex Search: "Find maintenance requests like X" (semantic similarity)
--   - Cortex Analyst: "What's the average resolution time?" (SQL analytics)

-- =====================================================
-- STEP 1: Create Stage for Semantic Model
-- =====================================================

USE ROLE SYSADMIN;
USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;

-- Create an internal stage to store the semantic model YAML
CREATE STAGE IF NOT EXISTS SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for Cortex Analyst semantic model files';

-- =====================================================
-- STEP 2: Upload Semantic Model
-- =====================================================
-- Option A: Using Snow CLI
-- Run this from your terminal (not in Snowflake worksheet):
--
--   snow stage copy ./snowflake/streetlights_semantic_model.yaml '@streetlights_demo.analytics.semantic_models'
--
-- Option B: Using Snowsight UI
-- 1. Go to Data > Databases > STREETLIGHTS_DEMO > ANALYTICS > Stages > SEMANTIC_MODELS
-- 2. Click "+ Files" button
-- 3. Upload streetlights_semantic_model.yaml

-- Verify the file was uploaded
LIST @SEMANTIC_MODELS;

-- =====================================================
-- STEP 3: Verify Semantic Model Contents
-- =====================================================

-- Read the YAML file to verify it's correctly uploaded
SELECT $1 AS yaml_content
FROM @SEMANTIC_MODELS/streetlights_semantic_model.yaml
(FILE_FORMAT => (TYPE = 'CSV' FIELD_DELIMITER = NONE));

-- =====================================================
-- STEP 4: Wire to Snowflake Intelligence
-- =====================================================
-- 
-- After uploading the semantic model:
--
-- 1. Open Snowflake Intelligence (AI & ML > Snowflake Intelligence)
-- 2. Click "Add Data Sources"
-- 3. Select "Semantic Model"
-- 4. Navigate to: STREETLIGHTS_DEMO > ANALYTICS > SEMANTIC_MODELS
-- 5. Select: streetlights_semantic_model.yaml
-- 6. Click "Add"
--
-- You should now have BOTH data sources connected:
--   ✓ MAINTENANCE_SEARCH (Cortex Search) - for semantic search
--   ✓ streetlights_semantic_model.yaml (Cortex Analyst) - for analytics

-- =====================================================
-- STEP 5: Test Queries for Cortex Analyst
-- =====================================================
-- These are the types of questions Cortex Analyst handles well.
-- Use these in Snowflake Intelligence chat after wiring the semantic model.

-- INFRASTRUCTURE OVERVIEW
-- "How many street lights do we have by status?"
-- "Show me how many lights are in each neighborhood"
-- "What is the total power consumption by neighborhood?"

-- MAINTENANCE ANALYTICS
-- "How many maintenance requests are currently open?"
-- "What are the most common maintenance issues?"
-- "What is the average resolution time for each issue type?"
-- "Which neighborhoods have the most maintenance issues?"

-- WEATHER & RISK ANALYSIS
-- "Which lights have the highest failure risk?"
-- "What is the average failure risk by season?"
-- "Show me lights predicted to fail this month"

-- POWER GRID ANALYSIS
-- "Which power grid zones have the most outages?"
-- "What's the average grid load by zone?"

-- SUPPLIER ANALYSIS
-- "What are the average response times by supplier?"
-- "How many suppliers do we have for each specialization?"

-- CDC MONITORING
-- "Show me records modified today via CDC"
-- "What tables have the most recent changes?"

-- =====================================================
-- COMBINED CORTEX SEARCH + ANALYST DEMO FLOW
-- =====================================================
-- Show the power of using BOTH capabilities together:
--
-- 1. START WITH SEARCH (Cortex Search)
--    Question: "Find flickering light issues in Koramangala"
--    → Returns relevant maintenance requests by semantic similarity
--
-- 2. PIVOT TO ANALYTICS (Cortex Analyst)  
--    Question: "What's the average resolution time for bulb failures?"
--    → Returns aggregated statistics via SQL
--
-- 3. DRILL DOWN WITH SEARCH
--    Question: "Show me similar issues to storm damage"
--    → Finds related maintenance records
--
-- 4. GET INSIGHTS WITH ANALYST
--    Question: "Which neighborhoods have the most maintenance issues?"
--    → Returns ranked neighborhood data
--
-- 5. PREDICTIVE ANALYSIS
--    Question: "Which lights are predicted to fail during monsoon?"
--    → Uses weather enrichment data

-- =====================================================
-- PHASE 11 SUCCESS CHECKLIST
-- =====================================================
-- Run these to verify Phase 11 is complete:
--
-- [ ] SEMANTIC_MODELS stage created
-- [ ] streetlights_semantic_model.yaml uploaded
-- [ ] File visible in LIST @SEMANTIC_MODELS
-- [ ] Semantic model wired to Snowflake Intelligence
-- [ ] Can ask analytical questions in chat
-- [ ] Both Search and Analyst working together
--
-- Combined capabilities available:
--   Cortex Search → Semantic similarity queries
--   Cortex Analyst → Structured SQL analytics
-- =====================================================

