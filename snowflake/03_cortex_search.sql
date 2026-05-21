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
-- Cortex Search Service: Maintenance Records
-- =====================================================
-- Enables semantic search over maintenance request descriptions.
-- Users can ask natural language questions like:
--   "Find flickering light issues near downtown"
--   "Show me storm damage reports from last month"
--
-- Variables to replace:
--   ${PREFIX} = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

USE WAREHOUSE ${PREFIX}_STREETLIGHTS_WH;

CREATE OR REPLACE CORTEX SEARCH SERVICE ${PREFIX}_STREETLIGHTS_CLD."streetlights".maintenance_search
  ON description
  ATTRIBUTES light_id, maintenance_type, maintenance_date, neighborhood_name, request_status
  WAREHOUSE = ${PREFIX}_STREETLIGHTS_WH
  TARGET_LAG = '1 hour'
  COMMENT = 'Semantic search over street light maintenance request descriptions'
AS (
  SELECT
    m."request_id" AS request_id,
    m."light_id" AS light_id,
    m."reported_at" AS maintenance_date,
    m."resolved_at" AS resolved_at,
    m."issue_type" AS maintenance_type,
    m."description" AS description,
    l."status" AS light_status,
    l."wattage" AS wattage,
    l."latitude" AS latitude,
    l."longitude" AS longitude,
    n."name" AS neighborhood_name,
    CASE
      WHEN m."resolved_at" IS NULL THEN 'OPEN'
      ELSE 'CLOSED'
    END AS request_status
  FROM ${PREFIX}_STREETLIGHTS_CLD."streetlights"."maintenance_requests" m
  LEFT JOIN ${PREFIX}_STREETLIGHTS_CLD."streetlights"."street_lights" l
    ON m."light_id" = l."light_id"
  LEFT JOIN ${PREFIX}_STREETLIGHTS_CLD."streetlights"."neighborhoods" n
    ON l."neighborhood_id" = n."neighborhood_id"
);

-- Verify service was created
SHOW CORTEX SEARCH SERVICES IN SCHEMA ${PREFIX}_STREETLIGHTS_CLD."streetlights";
