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
-- Databricks App support views (the app itself is deployed by the bundle
-- from databricks/app via resources.apps — run: databricks bundle run app -t dev
-- for these views)
-- =====================================================

USE CATALOG ${var.prefix}_STREETLIGHTS;
USE SCHEMA streetlights;

-- KPI dashboard view
CREATE OR REPLACE VIEW app_kpi_dashboard AS
SELECT
    (SELECT COUNT(*) FROM street_lights_clean)                                        AS total_lights,
    (SELECT COUNT(*) FROM street_lights_clean WHERE status = 'faulty')                 AS faulty_lights,
    (SELECT COUNT(*) FROM street_lights_clean WHERE status = 'operational')            AS operational_lights,
    (SELECT COUNT(*) FROM street_lights_clean WHERE status = 'maintenance_required')   AS maintenance_required,
    (SELECT COUNT(*) FROM maintenance_records_clean)                                   AS total_maintenance,
    (SELECT AVG(cost) FROM maintenance_records_clean WHERE cost IS NOT NULL)           AS avg_maintenance_cost,
    (SELECT SUM(energy_consumed_kwh) FROM energy_consumption_clean)                    AS total_energy_kwh,
    (SELECT COUNT(DISTINCT neighborhood) FROM street_lights_clean)                     AS total_neighborhoods,
    CURRENT_TIMESTAMP()                                                                AS last_updated;

-- Neighborhood map view
CREATE OR REPLACE VIEW app_neighborhood_map AS
SELECT
    neighborhood,
    COUNT(*)                          AS total_lights,
    SUM(CASE WHEN status = 'faulty' THEN 1 ELSE 0 END) AS faulty_lights,
    AVG(latitude)                     AS lat,
    AVG(longitude)                    AS lon
FROM street_lights_clean
GROUP BY neighborhood;

-- =====================================================
-- Verification
-- =====================================================
-- SELECT * FROM app_kpi_dashboard;
-- SELECT * FROM app_neighborhood_map LIMIT 10;
