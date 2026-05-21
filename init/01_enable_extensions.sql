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

-- Enable required extensions for Snowflake Postgres with pg_lake
-- pg_lake enables Iceberg table storage for seamless CLD integration

-- Create the streetlights schema for application tables
CREATE SCHEMA IF NOT EXISTS streetlights;
COMMENT ON SCHEMA streetlights IS 'Schema for street lights management application tables';

-- Set search path to include our schema
SET search_path TO streetlights, public;

-- Enable pg_lake extension (Iceberg table support for Snowflake CLD)
CREATE EXTENSION IF NOT EXISTS pg_lake;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Extensions enabled successfully!';
    RAISE NOTICE '  - pg_lake (Iceberg table storage)';
    RAISE NOTICE 'Schema "streetlights" created.';
END $$;
