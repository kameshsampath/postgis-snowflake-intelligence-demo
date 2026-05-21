---
name: streetlights-demo-step-3
description: Create Iceberg tables and load synthetic data
---

# Step 3: Create Schema + Load Data

## Prerequisites

- PG instance exists and is reachable (Step 2 complete)
- CSV data files exist in `data/` (Step 1 complete)

## Sequence (order matters!)

1. Enable extensions (`init/01_enable_extensions.sql`)
2. Create schema (`CREATE SCHEMA IF NOT EXISTS streetlights`)
3. Create Iceberg tables (`init/07_create_iceberg_tables.sql`)
4. Load data from CSVs: `\copy` for each of the 7 tables

## Execution

```bash
psql -h {pg_host} -U {pg_user} -d streetlights -f init/01_enable_extensions.sql
psql -h {pg_host} -U {pg_user} -d streetlights -f init/07_create_iceberg_tables.sql

# Load each CSV:
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.street_lights FROM 'data/street_lights.csv' CSV HEADER"
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.maintenance_records FROM 'data/maintenance_records.csv' CSV HEADER"
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.energy_consumption FROM 'data/energy_consumption.csv' CSV HEADER"
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.light_sensors FROM 'data/light_sensors.csv' CSV HEADER"
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.weather_enrichment FROM 'data/weather_enrichment.csv' CSV HEADER"
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.demographics FROM 'data/demographics.csv' CSV HEADER"
psql -h {pg_host} -U {pg_user} -d streetlights \
  -c "\copy streetlights.power_grid_zones FROM 'data/power_grid_zones.csv' CSV HEADER"
```

## Verification

- Query row counts for all 7 tables
- Show summary table to user:

| Table | Expected Rows |
|-------|--------------|
| street_lights | ~500 |
| maintenance_records | ~150 |
| energy_consumption | ~12000 |
| light_sensors | ~2500 |
| weather_enrichment | ~1500 |
| demographics | ~20 |
| power_grid_zones | ~10 |
