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

-- Reset PostgreSQL Database - Complete Fresh Start
-- Drops and recreates the entire streetlights schema
--
-- Usage:
--   psql -h localhost -U snowflake_admin -d postgres -f init/reset_database.sql
--
-- After running this script:
--   1. Regenerate data: uv run generate-all-data
--   2. Reload data: psql -h localhost -U snowflake_admin -d postgres -f data/load_data.sql
--   3. In Snowflake: DROP SCHEMA IF EXISTS "streetlights" CASCADE;
--   4. Restart Openflow processors to sync fresh data

\echo ''
\echo '========================================================='
\echo 'Resetting PostgreSQL Database - Complete Fresh Start'
\echo '========================================================='
\echo ''

-- Step 1: Drop publication (must be done before dropping schema)
\echo 'Step 1: Dropping publication...'
DROP PUBLICATION IF EXISTS streetlights_publication;

-- Step 2: Drop replication slot (if exists)
\echo 'Step 2: Dropping replication slot (if exists)...'
SELECT pg_drop_replication_slot('snowflake_cdc_slot') 
FROM pg_replication_slots 
WHERE slot_name = 'snowflake_cdc_slot';

-- Step 3: Drop the entire schema
\echo 'Step 3: Dropping streetlights schema...'
DROP SCHEMA IF EXISTS streetlights CASCADE;

\echo ''
\echo '========================================================='
\echo 'Recreating Database Schema'
\echo '========================================================='
\echo ''

-- Step 4: Run all initialization scripts
\echo 'Step 4: Running initialization scripts...'
\echo ''

-- 4a: Enable extensions
\echo '  4a. Enabling extensions...'
\i init/01_enable_extensions.sql

-- 4b: Configure WAL
\echo ''
\echo '  4b. Configuring WAL...'
\i init/02_enable_wal.sql

-- 4c: Create base tables
\echo ''
\echo '  4c. Creating base tables...'
\i init/03_create_base_tables.sql

-- 4d: Create enrichment tables
\echo ''
\echo '  4d. Creating enrichment tables...'
\i init/04_create_enrichment_tables.sql

-- 4e: Create enriched views
\echo ''
\echo '  4e. Creating enriched views...'
\i init/05_create_enriched_views.sql

-- 4f: Create indexes
\echo ''
\echo '  4f. Creating indexes...'
\i init/06_create_indexes.sql

-- 4g: Create publication
\echo ''
\echo '  4g. Creating publication...'
\i init/07_create_publication.sql

\echo ''
\echo '========================================================='
\echo 'Database Reset Complete!'
\echo '========================================================='
\echo ''
\echo 'Fresh schema created with:'
\echo '  - All tables (empty)'
\echo '  - All enriched views'
\echo '  - All indexes'
\echo '  - Publication for CDC'
\echo ''
\echo 'Next Steps:'
\echo ''
\echo '  1. Regenerate data:'
\echo '     uv run generate-all-data'
\echo ''
\echo '  2. Reload data into PostgreSQL:'
\echo '     psql -h localhost -U postgres -d postgres -f data/load_data.sql'
\echo ''
\echo '  3. In Snowflake (reset CDC target):'
\echo '     DROP SCHEMA IF EXISTS "streetlights" CASCADE;'
\echo ''
\echo '  4. Restart Openflow processors to sync fresh data'
\echo ''
\echo '  5. After CDC sync completes, run ML training:'
\echo '     snowflake/08_ml_training_view.sql'
\echo '     snowflake/09_ml_model_training.sql'
\echo ''
\echo '========================================================='
\echo ''
