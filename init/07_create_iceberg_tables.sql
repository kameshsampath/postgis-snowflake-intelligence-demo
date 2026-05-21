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

-- Create ALL tables as Iceberg for pg_lake → Snowflake CLD flow
-- These Iceberg tables are the actual storage layer; data inserted here
-- is automatically visible in Snowflake via Catalog-Linked Database (CLD).
--
-- Note: This script DROPS and recreates tables as Iceberg.
-- Run AFTER 03_create_base_tables.sql and 04_create_enrichment_tables.sql
-- have validated the schema design (those create heap tables for local dev).
-- In production pg_lake flow, only this script is needed.

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

-- =====================================================
-- Drop heap tables if they exist (we're replacing with Iceberg)
-- =====================================================
DROP TABLE IF EXISTS streetlights.power_grid_zones CASCADE;
DROP TABLE IF EXISTS streetlights.demographics CASCADE;
DROP TABLE IF EXISTS streetlights.weather_enrichment CASCADE;
DROP TABLE IF EXISTS streetlights.maintenance_requests CASCADE;
DROP TABLE IF EXISTS streetlights.suppliers CASCADE;
DROP TABLE IF EXISTS streetlights.street_lights CASCADE;
DROP TABLE IF EXISTS streetlights.neighborhoods CASCADE;

-- =====================================================
-- Table 1: neighborhoods
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.neighborhoods (
    neighborhood_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    boundary_coords JSONB NOT NULL,
    population INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) USING iceberg;

COMMENT ON TABLE streetlights.neighborhoods IS 'City neighborhoods with geographic boundaries (Iceberg)';

-- =====================================================
-- Table 2: street_lights
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.street_lights (
    light_id TEXT PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL,
    wattage INTEGER,
    installation_date DATE,
    last_maintenance TIMESTAMP,
    neighborhood_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) USING iceberg;

COMMENT ON TABLE streetlights.street_lights IS 'Street lights with lat/lng coordinates and operational status (Iceberg)';

-- =====================================================
-- Table 3: maintenance_requests
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.maintenance_requests (
    request_id TEXT PRIMARY KEY,
    light_id TEXT NOT NULL,
    reported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    issue_type TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) USING iceberg;

COMMENT ON TABLE streetlights.maintenance_requests IS 'Maintenance request history for street lights (Iceberg)';

-- =====================================================
-- Table 4: suppliers
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.suppliers (
    supplier_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    contact_phone TEXT,
    service_radius_km INTEGER,
    avg_response_hours INTEGER,
    specialization TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) USING iceberg;

COMMENT ON TABLE streetlights.suppliers IS 'Light equipment suppliers with service coverage areas (Iceberg)';

-- =====================================================
-- Table 5: weather_enrichment
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.weather_enrichment (
    light_id TEXT NOT NULL,
    season TEXT NOT NULL,
    avg_temperature_c NUMERIC(5,2),
    rainfall_mm NUMERIC(6,2),
    failure_risk_score NUMERIC(3,2),
    predicted_failure_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (light_id, season)
) USING iceberg;

COMMENT ON TABLE streetlights.weather_enrichment IS 'Seasonal weather patterns per light for predictive maintenance (Iceberg)';

-- =====================================================
-- Table 6: demographics
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.demographics (
    neighborhood_id TEXT PRIMARY KEY,
    population_density INTEGER,
    urban_classification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) USING iceberg;

COMMENT ON TABLE streetlights.demographics IS 'Neighborhood demographics for resource allocation (Iceberg)';

-- =====================================================
-- Table 7: power_grid_zones
-- =====================================================
CREATE TABLE IF NOT EXISTS streetlights.power_grid_zones (
    light_id TEXT PRIMARY KEY,
    grid_zone TEXT NOT NULL,
    avg_load_percent NUMERIC(5,2),
    outage_history_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) USING iceberg;

COMMENT ON TABLE streetlights.power_grid_zones IS 'Power grid data for each light (Iceberg)';

-- =====================================================
-- Verification
-- =====================================================
DO $$
DECLARE
    tbl_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tbl_count
    FROM information_schema.tables
    WHERE table_schema = 'streetlights'
      AND table_type = 'BASE TABLE';

    RAISE NOTICE 'Iceberg tables created successfully!';
    RAISE NOTICE '  Total tables in streetlights schema: %', tbl_count;
    RAISE NOTICE '  Tables:';
    RAISE NOTICE '    1. neighborhoods';
    RAISE NOTICE '    2. street_lights';
    RAISE NOTICE '    3. maintenance_requests';
    RAISE NOTICE '    4. suppliers';
    RAISE NOTICE '    5. weather_enrichment';
    RAISE NOTICE '    6. demographics';
    RAISE NOTICE '    7. power_grid_zones';
    RAISE NOTICE '';
    RAISE NOTICE 'All tables use ICEBERG storage engine.';
    RAISE NOTICE 'Data will be visible in Snowflake via CLD after pg_lake sync.';
END $$;
