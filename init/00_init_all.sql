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

-- Master initialization script for Snowflake Postgres database
-- This script orchestrates all initialization steps in the correct order
--
-- Usage:
--   psql -U postgres -d postgres -f init/00_init_all.sql
--
-- Note: Uses the default 'postgres' database to keep the demo simple
--

\echo ''
\echo '========================================================='
\echo 'Starting PostgreSQL Database Initialization (pg_lake)'
\echo '========================================================='
\echo ''

-- Step 1: Enable required extensions (pg_lake) and create schema
\echo 'Step 1: Enabling extensions (pg_lake) and creating schema...'
\i init/01_enable_extensions.sql

-- Step 2: Create Iceberg tables (all 7 tables)
\echo ''
\echo 'Step 2: Creating Iceberg tables...'
\i init/02_create_iceberg_tables.sql

-- Final completion message
\echo ''
\echo '========================================================='
\echo 'Database Initialization Complete!'
\echo '========================================================='
\echo ''
\echo 'Snowflake Postgres database is ready for use with pg_lake.'
\echo ''
\echo 'Tables created (all Iceberg storage):'
\echo '  1. streetlights.neighborhoods'
\echo '  2. streetlights.street_lights'
\echo '  3. streetlights.maintenance_requests'
\echo '  4. streetlights.suppliers'
\echo '  5. streetlights.weather_enrichment'
\echo '  6. streetlights.demographics'
\echo '  7. streetlights.power_grid_zones'
\echo ''
\echo 'Next Steps:'
\echo '  1. Generate sample data: uv run generate --city "Portland"'
\echo '  2. Load data: psql -U postgres -d postgres -f data/load_data.sql'
\echo '  3. Create CLD in Snowflake (see snowflake/01_setup.sql)'
\echo ''
\echo '========================================================='
\echo ''
