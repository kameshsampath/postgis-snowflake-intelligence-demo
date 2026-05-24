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
-- Intelligence Agent: Streetlights
-- =====================================================
-- Creates a Cortex Agent that combines:
--   - Cortex Analyst (Semantic View for structured SQL analytics)
--   - Cortex Search (unstructured text retrieval on maintenance records)
--
-- This enables natural language queries across both structured
-- analytics and free-text maintenance descriptions, with automatic
-- routing for combined multi-source answers.
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
--   <% CURRENCY_SYMBOL %> = local currency symbol (e.g., $, ₹, £)
-- =====================================================

USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

CREATE OR REPLACE AGENT <% PREFIX %>_STREETLIGHTS.PUBLIC.streetlights_agent
  COMMENT = 'Intelligence agent for streetlight infrastructure: analytics + maintenance search'
  FROM SPECIFICATION
  $$
  orchestration:
    budget:
      seconds: 30
      tokens: 16000

  instructions:
    response: |
      Respond in clear, concise markdown. Use tables for tabular data.
      Prioritize visualizations (charts, graphs) over raw tables when possible.
      Include units (kWh, count, hours, etc.) in all numeric outputs.
      Use <% CURRENCY_SYMBOL %> as the currency symbol for all cost and monetary values.
    orchestration: |
      ## ROUTING RULES
      Use MaintenanceSearch (Cortex Search) for:
      - Finding issues by description: "flickering", "sparking", "exposed wires"
      - Safety hazards, dangerous situations, urgent repairs
      - Semantic similarity: "find issues similar to...", "show me complaints about..."
      - Free-text content in maintenance descriptions

      Use StreetlightsAnalyst (Cortex Analyst) for:
      - Counts and aggregations: "how many", "total", "average"
      - Rankings: "which neighborhoods have the most..."
      - Status breakdowns: "lights by status", "active vs inactive"
      - Time-based analytics: resolution times, energy trends
      - Joins across tables: energy + demographics, lights + sensors

      ## OUTPUT GUIDELINES
      - Prioritize graphics (charts, plots) over raw tables when data permits
      - For geographic results, show neighborhood names (not raw coordinates)
      - When results are numeric comparisons, use bar or pie charts
      - For time-series data, use line charts

      ## LOCATION & MAP HANDLING
      - When the user asks about light locations, always include the LATITUDE and LONGITUDE columns in the query.
        Construct an OpenStreetMap URL using those values:
        https://www.openstreetmap.org/?mlat=LATITUDE&mlon=LONGITUDE&zoom=16
      - Display Logic:
        * Use the neighborhood name or pole_id as the hyperlink anchor text
        * If no name available, use "Show on Map" as fallback
        * Never display raw coordinate numbers to the user — always wrap in a map link
    sample_questions:
      - question: "How many street lights are currently faulty?"
      - question: "Which neighborhoods have the highest energy consumption?"
      - question: "Find maintenance reports about exposed wires or sparking"
      - question: "What is the average repair cost by maintenance type?"
      - question: "Show me the top 5 neighborhoods by maintenance frequency"

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "StreetlightsAnalyst"
        description: "Converts natural language to SQL for streetlight analytics. Use for counts, averages, trends, comparisons, rankings, and any structured data question about lights, energy, sensors, demographics, or power grid zones."
    - tool_spec:
        type: "cortex_search"
        name: "MaintenanceSearch"
        description: "Searches maintenance record descriptions using semantic search. Use for finding specific incidents, safety hazards, repair reports, or any free-text query about maintenance history and issue descriptions."

  tool_resources:
    StreetlightsAnalyst:
      semantic_view: "<% PREFIX %>_STREETLIGHTS.PUBLIC.STREETLIGHTS_SEMANTIC_VIEW"
    MaintenanceSearch:
      name: "<% PREFIX %>_STREETLIGHTS.PUBLIC.MAINTENANCE_SEARCH"
      max_results: "5"
      title_column: "MAINTENANCE_TYPE"
      id_column: "RECORD_ID"
  $$;

-- =====================================================
-- Grant Access
-- =====================================================
-- Required for non-ACCOUNTADMIN roles to open and query
-- the agent in Snowflake Intelligence.
-- CLD access (database / schema / tables) was granted in Step 4.
--
-- Additional variables:
--   <% ROLE %> = role to grant access to (e.g., KAMESH_DEMOS)
-- =====================================================

USE ROLE ACCOUNTADMIN;

-- Agent access
GRANT USAGE ON AGENT <% PREFIX %>_STREETLIGHTS.PUBLIC.STREETLIGHTS_AGENT TO ROLE <% ROLE %>;

-- Database and schema access
GRANT USAGE ON DATABASE <% PREFIX %>_STREETLIGHTS TO ROLE <% ROLE %>;
GRANT USAGE ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;

-- Tool resources access
GRANT SELECT ON SEMANTIC VIEW <% PREFIX %>_STREETLIGHTS.PUBLIC.STREETLIGHTS_SEMANTIC_VIEW TO ROLE <% ROLE %>;
GRANT USAGE ON CORTEX SEARCH SERVICE <% PREFIX %>_STREETLIGHTS.PUBLIC.MAINTENANCE_SEARCH TO ROLE <% ROLE %>;

-- Warehouse for query execution
GRANT USAGE ON WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH TO ROLE <% ROLE %>;

-- =====================================================
-- Register with Snowflake Intelligence
-- =====================================================
-- Required for the agent to appear in the Snowflake Intelligence UI.
-- Accounts with SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT show only
-- explicitly registered agents — without this, the UI falls back
-- to the default/main agent.
-- Note: CREATE OR REPLACE above drops and recreates the agent,
-- so this ADD must run after every deployment.
-- =====================================================

ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT <% PREFIX %>_STREETLIGHTS.PUBLIC.STREETLIGHTS_AGENT;
