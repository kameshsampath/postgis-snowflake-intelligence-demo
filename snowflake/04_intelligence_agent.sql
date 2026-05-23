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
--   - data_to_chart (visualization generation)
--
-- This enables natural language queries across both structured
-- analytics and free-text maintenance descriptions, with automatic
-- routing and chart generation.
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

CREATE OR REPLACE AGENT <% PREFIX %>_STREETLIGHTS.PUBLIC.streetlights_agent
  COMMENT = 'Intelligence agent for streetlight infrastructure: analytics + maintenance search'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto

  orchestration:
    budget:
      seconds: 30
      tokens: 16000

  instructions:
    response: |
      Respond in clear, concise markdown. Use tables for tabular data.
      Prioritize visualizations (charts, graphs) over raw tables when possible.
      Include units (kWh, count, hours, etc.) in all numeric outputs.
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
      - When query results include latitude and longitude columns, construct a Google Maps URL:
        https://www.google.com/maps/search/?api=1&query=LAT,LONG
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
    - tool_spec:
        type: "data_to_chart"
        name: "data_to_chart"
        description: "Generates visualizations (bar charts, line charts, pie charts) from query results."

  tool_resources:
    StreetlightsAnalyst:
      semantic_view: "<% PREFIX %>_STREETLIGHTS.PUBLIC.STREETLIGHTS_SEMANTIC_VIEW"
    MaintenanceSearch:
      name: "<% PREFIX %>_STREETLIGHTS.PUBLIC.MAINTENANCE_SEARCH"
      max_results: "5"
      title_column: "MAINTENANCE_TYPE"
      id_column: "RECORD_ID"
  $$;
