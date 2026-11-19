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
-- Genie space support: verified-question views
-- =====================================================
-- The Genie space itself is created by the asset bundle
-- (resources.genie_spaces in databricks.yml, direct deployment engine).
-- There is no SQL DDL for Genie spaces — after `databricks bundle deploy`,
-- open the space in the workspace (AI/BI -> Genie) and:
--   1. Add catalog/schema: ${var.prefix}_STREETLIGHTS.streetlights
--   2. Add instructions, e.g.:
--        "You are a streetlights domain expert. Available curated views:
--         street_lights_clean, maintenance_records_clean, energy_consumption_clean,
--         weather_enrichment_clean, light_sensors_clean, demographics_clean,
--         power_grid_zones_clean. Join on street_light_id. Statuses are
--         operational | faulty | maintenance_required. When results include
--         latitude/longitude, also give a map link:
--         https://www.google.com/maps/search/?api=1&query={lat},{lon}"
--   3. Add the verified questions below (one per view) and mark their SQL
--      as verified answers.
-- Run via: databricks bundle run genie_views -t dev
-- =====================================================

USE CATALOG ${var.prefix}_STREETLIGHTS;
USE SCHEMA streetlights;

-- Verified question: "How many street lights are currently faulty?"
CREATE OR REPLACE VIEW v_q_faulty_count AS
SELECT COUNT(*) AS faulty_lights
FROM street_lights_clean
WHERE status = 'faulty';

-- Verified question: "Show me faulty lights in <neighborhood>"
CREATE OR REPLACE VIEW v_q_faulty_by_neighborhood AS
SELECT street_light_id, pole_id, neighborhood, status, latitude, longitude
FROM street_lights_clean
WHERE status = 'faulty';

-- Verified question: "Which neighborhoods have the highest energy consumption?"
CREATE OR REPLACE VIEW v_q_energy_by_neighborhood AS
SELECT neighborhood, SUM(energy_consumed_kwh) AS total_kwh, COUNT(DISTINCT street_light_id) AS lights
FROM energy_consumption_clean
GROUP BY neighborhood
ORDER BY total_kwh DESC;

-- Verified question: "What is the average repair cost by maintenance type?"
CREATE OR REPLACE VIEW v_q_cost_by_type AS
SELECT maintenance_type, AVG(cost) AS avg_cost, COUNT(*) AS n
FROM maintenance_records_clean
GROUP BY maintenance_type
ORDER BY avg_cost DESC;

-- Verified question: "Predict energy consumption for the next 30 days"
-- (answered from the energy_forecast table built by 04_forecast.sql)
CREATE OR REPLACE VIEW v_q_forecast_next_30d AS
SELECT * FROM energy_forecast
ORDER BY date;

-- =====================================================
-- Verification
-- =====================================================
-- SELECT * FROM v_q_faulty_count;
-- SELECT * FROM v_q_energy_by_neighborhood LIMIT 5;
