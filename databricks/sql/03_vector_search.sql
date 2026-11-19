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
-- Databricks Vector Search Configuration
-- =====================================================
-- Prerequisites:
--   1. Databricks Vector Search enabled on the workspace
--   2. Setup from 01_setup.sql completed
--   3. Appropriate permissions for Vector Search creation
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

-- Set current catalog/schema
USE CATALOG <% PREFIX %>_STREETLIGHTS;
USE SCHEMA streetlights;

-- =====================================================
-- Step 1: Create Vector Search Endpoint
-- =====================================================

-- Note: Vector Search endpoints are typically created via UI/REST API
-- The SQL below assumes the endpoint already exists or creates it if supported
-- If not supported via SQL, use the Databricks UI:
--   Workspace → Vector Search → Create Endpoint
--   Name: <% PREFIX %>_STREETLIGHTS_VS
--   Type: STANDARD

-- CREATE VECTOR SEARCH ENDPOINT IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_VS
--   ENDPOINT_TYPE = STANDARD;

-- =====================================================
-- Step 2: Create embedding model for maintenance text
-- =====================================================

-- Use Databricks BGE embedding model
-- This model is optimized for semantic similarity search
-- Dimension: 1024 for bge-large-en

-- =====================================================
-- Step 3: Create Vector Search Index on Maintenance Records
-- =====================================================

-- Create the vector index on the maintenance_records_clean view
-- This index will enable semantic search on maintenance descriptions and notes

CREATE VECTOR SEARCH INDEX IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_MAINTENANCE
  ON maintenance_records_clean (full_text)
  COLUMNS (* EXCLUDE (full_text))
  -- Use abc for indexing all columns except the text column itself
  -- The star notation is not universally supported, so we specify key columns
  COLUMNS (
    maintenance_id,
    street_light_id,
    maintenance_date,
    maintenance_type,
    description,
    status,
    cost,
    severity,
    neighborhood
  )
  EXCLUDE COLUMNS (full_text)
  USING VECTORIZER 
    databricks-bge-large-en
  USING INDEX_HINT (
    index_structure = HNSW,
    index_metric = COSINE
  )
  PRIMARY KEY (maintenance_id)
  COMMENT 'Vector Search index for semantic search on maintenance records'
  -- Set endpoint for this index
  WITH (
    endpoint = '<% PREFIX %>_STREETLIGHTS_VS'
  );

-- =====================================================
-- Step 4: Create Vector Search Index for Street Lights
-- =====================================================

-- Optional: Create a second index for street light notes and metadata
-- This can be useful for searching by location description, bulb types, etc.

CREATE VECTOR SEARCH INDEX IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_INFRA
  ON street_lights_clean (
    CONCAT(
      COALESCE(notes, ''),
      CASE WHEN notes IS NOT NULL AND bulb_type IS NOT NULL THEN ' ' ELSE '' END,
      COALESCE(bulb_type, ''),
      CASE WHEN (notes IS NOT NULL OR bulb_type IS NOT NULL) AND pole_material IS NOT NULL THEN ' ' ELSE '' END,
      COALESCE(pole_material, '')
    )
  )
  COLUMNS (
    street_light_id,
    neighborhood,
    status,
    latitude,
    longitude,
    bulb_type,
    wattage,
    height,
    pole_material,
    installation_date,
    last_maintenance_date
  )
  USING VECTORIZER 
    databricks-bge-large-en
  USING INDEX_HINT (
    index_structure = HNSW,
    index_metric = COSINE
  )
  PRIMARY KEY (street_light_id)
  COMMENT 'Vector Search index for street light infrastructure metadata'
  WITH (
    endpoint = '<% PREFIX %>_STREETLIGHTS_VS'
  );

-- =====================================================
-- Step 5: Configure Genie Text Search Tool
-- =====================================================

-- Create Vector Search tool for Genie
-- This connects the vector index to the Genie space

CREATE OR REPLACE GENIE TOOL <% PREFIX %>_STREETLIGHTS_SEARCH
  TYPE VECTOR_SEARCH
  VECTOR_SEARCH_INDEX <% PREFIX %>_STREETLIGHTS_MAINTENANCE
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  DESCRIPTION 'Semantic text search tool for maintenance record descriptions and notes'
  INSTRUCTIONS $$
You are a maintenance text search expert. 

**PRIMARY PURPOSE:**
- Search maintenance descriptions, notes, and observations
- Find specific maintenance issues or patterns
- Identify problems described in free text

**SEARCH STRATEGY:**
- Use semantic similarity to find relevant maintenance records
- Consider synonyms and related terms (e.g., "sparking" = "electrical" = "short circuit")
- Prioritize recent and high-severity issues
- Include neighborhood context when available

**COMMON SEARCH TYPES:**
- "exposed wires" → Find electrical safety issues
- "pole integrity" → Find structural damage reports
- "sparking" → Find fire/ignition hazards
- "flickering" → Find bulb/connection problems
- "water damage" → Find weather-related issues

**RESPONSE FORMAT:**
- Return the most relevant maintenance records
- Include maintenance_id, description, notes, severity, and neighborhood
- Sort by relevance score and recency
- Provide context about why each result matches
$$;

-- =====================================================
-- Step 6: Create Hybrid Search Configuration
-- =====================================================

-- Configure Genie to use both Analyst and Vector Search tools
-- This enables hybrid queries that use both structured and text search

CREATE OR REPLACE GENIE INTENT EXAMPLE hybrid_query
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  EXAMPLES (
    'Tell me about maintenance issues in Koramangala',
    'What maintenance has been done on faulty lights downtown?',
    'Show me high-severity electrical problems in the north zone',
    'Find all sparking incidents and their repair costs'
  )
  ROUTED_TO TOOLS <% PREFIX %>_STREETLIGHTS_ANALYST, <% PREFIX %>_STREETLIGHTS_SEARCH;

-- =====================================================
-- Step 7: Test Vector Search Index
-- =====================================================

-- These are sample queries to test the vector search functionality
-- Uncomment to test:

-- Test basic semantic search
-- SELECT * FROM VECTOR_SEARCH(
--   INDEX => '%<PREFIX>_STREETLIGHTS_MAINTENANCE',
--   QUERY_TEXT => 'exposed wires electrical safety'
-- ) ORDER BY score DESC LIMIT 10;

-- Test hybrid query (structured + vector)
-- WITH structured_results AS (
--   SELECT maintenance_id, description, neighborhood, maintenance_date
--   FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean
--   WHERE neighborhood = 'Koramangala'
-- ),
-- vector_results AS (
--   SELECT maintenance_id, score, full_text
--   FROM VECTOR_SEARCH(
--     INDEX => '%<PREFIX>_STREETLIGHTS_MAINTENANCE',
--     QUERY_TEXT => 'exposed wires'
--   )
-- )
-- SELECT sr.*, vr.score as semantic_score
-- FROM structured_results sr
-- JOIN vector_results vr ON sr.maintenance_id = vr.maintenance_id
-- ORDER BY semantic_score DESC LIMIT 10;

-- =====================================================
-- Verification queries
-- =====================================================

-- Show vector search endpoints
-- SHOW VECTOR SEARCH ENDPOINTS;

-- Show vector search indexes
-- SHOW VECTOR SEARCH INDEXES;

-- Describe specific index
-- DESCRIBE VECTOR SEARCH INDEX <% PREFIX %>_STREETLIGHTS_MAINTENANCE;

-- Check index status
-- SELECT * FROM SYSTEM.VECTOR_SEARCH.INDEXES 
-- WHERE name = '<% PREFIX %>_STREETLIGHTS_MAINTENANCE';
