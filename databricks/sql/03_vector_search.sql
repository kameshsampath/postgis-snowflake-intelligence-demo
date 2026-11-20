-- Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
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
-- Vector Search: source Delta table for the maintenance-text index
-- =====================================================
-- Run via: databricks bundle run vector_search -t dev
--
-- Vector Search indexes cannot be created with SQL DDL — create the index
-- from this Delta table via the workspace UI (AI Search -> Create index ->
-- Delta Sync, source ${var.prefix}_streetlights.streetlights.maintenance_records_text,
-- primary key maintenance_id, embedding source column full_text with model
-- databricks-bge-large-en) or the REST/SDK API. The endpoint
-- ${var.prefix}_streetlights_vs is created by the bundle.
--
-- Query the index from SQL with:
--   SELECT * FROM vector_search(
--     index => '${var.prefix}_streetlights.streetlights.maintenance_vs_index',
--     query_text => 'exposed wires or sparking',
--     num_results => 5);
-- =====================================================

USE CATALOG ${var.prefix}_streetlights;
USE SCHEMA streetlights;

-- Delta table backing the vector index (refreshed from the Lakebase
-- foreign catalog; re-run this job to pick up new rows)
CREATE OR REPLACE TABLE maintenance_records_text AS
SELECT
    maintenance_id,
    street_light_id,
    maintenance_date,
    maintenance_type,
    description,
    cost,
    technician,
    neighborhood,
    full_text
FROM maintenance_records_clean;

-- =====================================================
-- Verification
-- =====================================================
-- SELECT COUNT(*) FROM maintenance_records_text;
-- SELECT maintenance_id, description FROM maintenance_records_text LIMIT 5;
