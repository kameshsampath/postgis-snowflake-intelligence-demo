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

-- Master initialization script for PostgreSQL database
-- This script orchestrates all initialization steps in the correct order
--
-- Usage:
--   psql -U postgres -d postgres -f init/00_init_all.sql
--
-- Note: Uses the default 'postgres' database to keep the demo simple
--

\echo ''
\echo '========================================================='
\echo 'Starting PostgreSQL Database Initialization'
\echo '========================================================='
\echo ''

-- Step 1: Enable required PostgreSQL extensions
\echo 'Step 1: Enabling extensions (PostGIS, uuid-ossp)...'
\i init/01_enable_extensions.sql

-- Step 2: Configure Write-Ahead Logging (WAL) for CDC
\echo ''
\echo 'Step 2: Configuring WAL for Change Data Capture...'
\i init/02_enable_wal.sql

-- Step 3: Create base tables
\echo ''
\echo 'Step 3: Creating base tables...'
\i init/03_create_base_tables.sql

-- Step 4: Create enrichment tables
\echo ''
\echo 'Step 4: Creating enrichment tables...'
\i init/04_create_enrichment_tables.sql

-- Step 5: Create enriched views
\echo ''
\echo 'Step 5: Creating enriched views...'
\i init/05_create_enriched_views.sql

-- Step 6: Create indexes for performance
\echo ''
\echo 'Step 6: Creating indexes...'
\i init/06_create_indexes.sql

-- Step 7: Create publication for CDC (Snowflake Openflow)
\echo ''
\echo 'Step 7: Creating publication for CDC...'
\i init/07_create_publication.sql

-- Final completion message
\echo ''
\echo '========================================================='
\echo 'Database Initialization Complete!'
\echo '========================================================='
\echo ''
\echo 'PostgreSQL database is ready for use.'
\echo ''
\echo 'Next Steps:'
\echo '  1. Generate sample data: cd data && ./generate_all_data.sh'
\echo '  2. Load data: psql -U postgres -d postgres -f data/load_data.sql'
\echo '  3. Start Streamlit dashboard: http://localhost:8501'
\echo ''
\echo 'For CDC with Snowflake Openflow:'
\echo '  - PostgreSQL needs to be restarted for WAL settings to take effect'
\echo '  - Restart command: pg_ctl restart (or your database restart method)'
\echo '  - Snowflake CDC will automatically create replication slots'
\echo '  - Publication "streetlights_publication" is ready for use'
\echo ''
\echo '========================================================='
\echo ''

