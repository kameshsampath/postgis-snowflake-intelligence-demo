---
name: streetlights-demo-step-3
description: Create Iceberg tables and load synthetic data
---

## Gate

```bash
uv run gate --step step-3 --prior-step step-2 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-3 --desc "Creating schema and loading data" --action start
```

# Step 3: Create Schema + Load Data

## Why this matters

**`USING iceberg`** — When we create tables with `USING iceberg`, Postgres stores data in Apache Iceberg format (Parquet data files + Iceberg metadata). The data lives on managed object storage — not local PG disk.

**Zero-copy read from Snowflake** — Because the data is already in Iceberg format on shared storage, Snowflake can read it directly. No ETL pipeline, no data movement, no sync jobs. Just shared Iceberg metadata pointing at the same Parquet files.

**IDD connection** — This skill file is the *intent*; CoCo (the AI agent) *executes* it. The `generate --city` command compresses 7 table definitions + synthetic data into a single invocation — an [Intent Compression Ratio](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9) of ~7:1. The skill file itself is [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14).

---

**STOP** — Use `ask_user_question` to confirm:
- Header: "Step 3"
- Question: "Ready to proceed with table creation? (Iceberg tables on PG managed storage)"
- Options: ["Yes, proceed", "Skip this step"]

---

## What we'll do

Create the `streetlights` schema with Iceberg tables on the Postgres instance and load all 7 CSV files. This gives pg_lake the data it will sync to Snowflake via CLD.

- Enable PostGIS and pg_lake extensions
- Create Iceberg tables in the `streetlights` schema
- Load all CSV data via `\copy`

## Dry-Run

Show the execution plan to the user:
```bash
uv run gate --step step-3 --action dry-run
```
Present the output, then ask user to proceed.

## Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 3"
- Question: "Ready to create Iceberg tables and load data into Postgres?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- PG instance exists and is reachable (Step 2 complete)
- CSV data files exist in `data/` (Step 1 complete)

### Network Pre-check

Before connecting via psql, verify network access:
- Run `uv run gate --step step-3 --prior-step step-2 --action check` (internally verifies PG reachability)
- If **IP MISMATCH**: show current IP vs allowed IPs, ask to update network policy
  (user may have switched networks since Step 2)
- If user approves: route to `$snowflake-postgres` to update the policy, then retry

### Sequence (order matters!)

> ⚠️ **CASCADE required** — `pg_lake` depends on 5+ other extensions (PostGIS, pgcrypto, etc.). The extension SQL uses `CREATE EXTENSION ... CASCADE` to auto-install dependencies.

> ⚠️ **No PRIMARY KEY** — Iceberg tables are *foreign tables* under the hood. PostgreSQL foreign tables do not support constraints (`PRIMARY KEY`, `UNIQUE`, `NOT NULL`). The DDL uses bare column definitions only.

> ⚠️ **`table_type = 'FOREIGN'`** — When verifying tables, query `information_schema.tables` with `WHERE table_type = 'FOREIGN'` (not `'BASE TABLE'`).

1. Enable extensions (`init/01_enable_extensions.sql`)
2. Create schema (`CREATE SCHEMA IF NOT EXISTS streetlights`)
3. Create Iceberg tables (`init/02_create_iceberg_tables.sql`)
4. Load data from CSVs: `\copy` for each of the 7 tables

```bash
psql "service=$PGSERVICE" -f init/01_enable_extensions.sql
psql "service=$PGSERVICE" -f init/02_create_iceberg_tables.sql

# Load each CSV:
psql "service=$PGSERVICE" \
  -c "\copy streetlights.street_lights FROM 'data/street_lights.csv' CSV HEADER"
psql "service=$PGSERVICE" \
  -c "\copy streetlights.maintenance_records FROM 'data/maintenance_records.csv' CSV HEADER"
psql "service=$PGSERVICE" \
  -c "\copy streetlights.energy_consumption FROM 'data/energy_consumption.csv' CSV HEADER"
psql "service=$PGSERVICE" \
  -c "\copy streetlights.light_sensors FROM 'data/light_sensors.csv' CSV HEADER"
psql "service=$PGSERVICE" \
  -c "\copy streetlights.weather_enrichment FROM 'data/weather_enrichment.csv' CSV HEADER"
psql "service=$PGSERVICE" \
  -c "\copy streetlights.demographics FROM 'data/demographics.csv' CSV HEADER"
psql "service=$PGSERVICE" \
  -c "\copy streetlights.power_grid_zones FROM 'data/power_grid_zones.csv' CSV HEADER"
```

### Verification

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

## What we did

- ✅ Extensions enabled (PostGIS, pg_lake)
- ✅ Iceberg tables created in `streetlights` schema
- ✅ All 7 CSV files loaded successfully
- ✅ Row counts verified

## Mark COMPLETE

```bash
uv run gate --step step-3 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 4: Catalog Integration + CLD?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 4` for later resumption.
