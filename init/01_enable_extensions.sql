-- Enable PostGIS extension explicitly (educational: show users how to install)
-- This script runs automatically when the PostgreSQL container starts

-- Create the streetlights schema for application tables
-- This keeps our tables separate from system/extension tables
CREATE SCHEMA IF NOT EXISTS streetlights;
COMMENT ON SCHEMA streetlights IS 'Schema for street lights management application tables';

-- Set search path to include our schema
SET search_path TO streetlights, public;

-- Enable PostGIS core extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable PgVector core extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable PostGIS topology (optional but useful for advanced spatial operations)
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verify installation and show version
SELECT PostGIS_Version() as postgis_version;

-- Show available spatial reference systems
SELECT count(*) as available_srids FROM spatial_ref_sys;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'PostGIS extensions enabled successfully!';
    RAISE NOTICE 'PostGIS Version: %', PostGIS_Version();
END $$;


