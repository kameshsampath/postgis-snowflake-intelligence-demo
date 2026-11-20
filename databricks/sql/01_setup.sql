-- Copyright 2025 Kamesh Sampath <kamesh.sampath@gmail.com>
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
-- Databricks setup: curated views over the Lakebase catalog
-- =====================================================
-- Run via the asset bundle job (databricks bundle run setup -t dev).
-- Bundle variables (${var.prefix}) are interpolated by DAB at deploy/run time.
--
-- Prerequisites:
--   1. Lakebase project + branch + endpoint (compute) created, database
--      "streetlights" populated via sql/00_lakebase_schema.sql + \copy loads
--   2. The Lakebase database registered in Unity Catalog as a foreign catalog:
--        databricks postgres create-catalog ${var.prefix}_STREETLIGHTS_PG \
--          --json '{"spec": {"postgres_database": "streetlights",
--                            "branch": "projects/<project>/branches/main"}}'
--      (see docs/databricks-guide.md for the full walkthrough)
--   3. The bundle's own catalog/schema/warehouse already created by
--      `databricks bundle deploy` (resources in databricks.yml)
-- =====================================================

USE CATALOG ${var.prefix}_STREETLIGHTS;
USE SCHEMA streetlights;

-- =====================================================
-- Curated views (the Genie "semantic layer")
-- Source tables live in the Lakebase-registered foreign catalog
-- ${var.prefix}_STREETLIGHTS_PG.streetlights.* (plain Postgres columns).
-- =====================================================

CREATE OR REPLACE VIEW street_lights_clean AS
SELECT
    id            AS street_light_id,
    pole_id,
    latitude,
    longitude,
    neighborhood,
    install_date  AS installation_date,
    wattage,
    light_type    AS bulb_type,
    status,
    ST_POINT(longitude, latitude) AS location
FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.street_lights;

CREATE OR REPLACE VIEW maintenance_records_clean AS
SELECT
    m.id          AS maintenance_id,
    m.light_id    AS street_light_id,
    m.date        AS maintenance_date,
    m.type        AS maintenance_type,
    m.description,
    m.cost,
    m.technician,
    sl.neighborhood,
    CONCAT_WS(' ', COALESCE(m.description, ''), COALESCE(m.type, ''),
              COALESCE(sl.neighborhood, '')) AS full_text
FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.maintenance_records m
LEFT JOIN ${var.prefix}_STREETLIGHTS_PG.streetlights.street_lights sl
    ON m.light_id = sl.id;

CREATE OR REPLACE VIEW energy_consumption_clean AS
SELECT
    e.id          AS consumption_id,
    e.light_id    AS street_light_id,
    e.date        AS consumed_date,
    e.hour,
    e.kwh         AS energy_consumed_kwh,
    e.voltage,
    e.power_factor,
    sl.neighborhood
FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.energy_consumption e
LEFT JOIN ${var.prefix}_STREETLIGHTS_PG.streetlights.street_lights sl
    ON e.light_id = sl.id;

CREATE OR REPLACE VIEW weather_enrichment_clean AS
SELECT * FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.weather_enrichment;

CREATE OR REPLACE VIEW light_sensors_clean AS
SELECT * FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.light_sensors;

CREATE OR REPLACE VIEW demographics_clean AS
SELECT * FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.demographics;

CREATE OR REPLACE VIEW power_grid_zones_clean AS
SELECT * FROM ${var.prefix}_STREETLIGHTS_PG.streetlights.power_grid_zones;

-- =====================================================
-- Verification
-- =====================================================
-- SELECT COUNT(*) FROM street_lights_clean;
-- SELECT COUNT(*) FROM maintenance_records_clean;
-- SELECT COUNT(*) FROM energy_consumption_clean;
