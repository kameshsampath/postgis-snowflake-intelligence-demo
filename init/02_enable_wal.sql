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

-- Configure Write-Ahead Logging (WAL) for CDC (Change Data Capture)
-- This prepares the database for Apache NiFi CDC in future phases

-- Set WAL level to logical (required for logical replication/CDC)
ALTER SYSTEM SET wal_level = 'logical';

-- Set maximum number of replication slots
ALTER SYSTEM SET max_replication_slots = 10;

-- Set maximum number of WAL sender processes
ALTER SYSTEM SET max_wal_senders = 10;

-- Note: These settings require PostgreSQL restart to take effect
-- Restart using your database management method (e.g., pg_ctl restart, service restart, etc.)

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'WAL configuration updated for CDC support';
    RAISE NOTICE 'Settings will take effect after PostgreSQL restart';
    RAISE NOTICE 'Use your database restart method (e.g., pg_ctl restart)';
END $$;


-- Grant replication privileges to snowflake_admin user
ALTER USER snowflake_admin WITH REPLICATION;
