-- Create PostgreSQL publication for Snowflake Openflow CDC
-- This publication makes all streetlights schema tables available for Change Data Capture

-- Create publication for all tables in the streetlights schema
CREATE PUBLICATION streetlights_publication FOR TABLES IN SCHEMA streetlights;

-- Verify publication
SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete 
FROM pg_publication 
WHERE pubname = 'streetlights_publication';

-- List tables in publication
SELECT schemaname, tablename 
FROM pg_publication_tables 
WHERE pubname = 'streetlights_publication'
ORDER BY tablename;
