-- Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
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
-- Lakebase schema: PostGIS + streetlights tables (plain Postgres DDL)
-- =====================================================
-- Run this against your Lakebase database with psql, e.g.:
--   PGPASSWORD=<oauth-token> psql -h <endpoint-host> -p 5432 -U <role> -d streetlights -f sql/00_lakebase_schema.sql
-- Lakebase is a real PostgreSQL 17 database, so PostGIS works natively.
-- (The Snowflake path uses pg_lake/Iceberg via init/ instead; this file is
-- the Lakebase equivalent. Columns mirror scripts/generate_ddl.py TABLE_SCHEMAS.)
-- =====================================================

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS streetlights;

CREATE TABLE IF NOT EXISTS streetlights.street_lights (
    id INTEGER PRIMARY KEY,
    pole_id TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    neighborhood TEXT,
    install_date DATE,
    wattage INTEGER,
    light_type TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS streetlights.maintenance_records (
    id INTEGER PRIMARY KEY,
    light_id INTEGER NOT NULL,
    date DATE NOT NULL,
    type TEXT,
    description TEXT,
    cost NUMERIC(10,2),
    technician TEXT
);

CREATE TABLE IF NOT EXISTS streetlights.energy_consumption (
    id INTEGER PRIMARY KEY,
    light_id INTEGER NOT NULL,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    kwh NUMERIC(8,4),
    voltage NUMERIC(5,1),
    power_factor NUMERIC(4,3)
);

CREATE TABLE IF NOT EXISTS streetlights.light_sensors (
    id INTEGER PRIMARY KEY,
    light_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    lux NUMERIC(7,1),
    motion_detected BOOLEAN,
    temperature NUMERIC(4,1)
);

CREATE TABLE IF NOT EXISTS streetlights.weather_enrichment (
    date DATE PRIMARY KEY,
    season TEXT NOT NULL,
    temperature NUMERIC(5,1),
    humidity NUMERIC(5,1),
    wind_speed NUMERIC(5,1),
    precipitation NUMERIC(5,1)
);

CREATE TABLE IF NOT EXISTS streetlights.demographics (
    neighborhood TEXT PRIMARY KEY,
    population INTEGER,
    median_income INTEGER,
    commercial_pct NUMERIC(3,2)
);

CREATE TABLE IF NOT EXISTS streetlights.power_grid_zones (
    zone_id TEXT PRIMARY KEY,
    zone_name TEXT NOT NULL,
    capacity_kw INTEGER,
    current_load_kw INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
