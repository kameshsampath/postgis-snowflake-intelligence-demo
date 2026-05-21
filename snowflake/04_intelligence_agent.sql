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
--   - Semantic View (structured SQL analytics)
--   - Cortex Search (unstructured text retrieval)
--
-- This enables natural language queries across both structured
-- analytics and free-text maintenance descriptions.
--
-- Variables to replace:
--   ${PREFIX} = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

USE WAREHOUSE ${PREFIX}_STREETLIGHTS_WH;

CREATE OR REPLACE CORTEX AGENT ${PREFIX}_STREETLIGHTS_CLD."streetlights".streetlights_agent
  SEMANTIC_VIEW = (${PREFIX}_STREETLIGHTS_CLD."streetlights".streetlights_semantic_view)
  CORTEX_SEARCH_SERVICES = (${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_search)
  COMMENT = 'Intelligence agent for streetlight infrastructure: analytics + maintenance search'
;

-- =====================================================
-- Verification: Test the agent with sample queries
-- =====================================================
-- After creation, test with these queries in Snowflake Intelligence:
--
-- Structured analytics (routed to Semantic View):
--   "How many street lights do we have by status?"
--   "What is the average resolution time for bulb failures?"
--   "Which neighborhoods have the most maintenance issues?"
--   "What is the total power consumption by neighborhood?"
--   "Which lights have the highest failure risk?"
--
-- Semantic search (routed to Cortex Search):
--   "Find flickering light issues"
--   "Show me storm damage reports"
--   "Any wiring problems near downtown?"
--   "Recent pole damage incidents"
--
-- Combined (agent decides routing):
--   "Tell me about maintenance issues in the busiest neighborhood"
--   "What's the situation with faulty lights and their repair status?"
-- =====================================================
