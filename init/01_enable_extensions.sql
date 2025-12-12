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


