---
name: streetlights-demo-step-4
description: Create Catalog Integration and CLD database
---

# Step 4: Catalog Integration + CLD

**BILLABLE ACTION** — Confirm with user before proceeding.

## Pre-flight

- Run `gate.py check_pg_managed_storage` — CLD ONLY works with managed storage

## Steps

Route to `$snowflake-postgres` pg_lake to:

1. Create catalog integration for the PG instance:
   ```sql
   CREATE CATALOG INTEGRATION {prefix}_streetlights_catalog_int
     CATALOG_SOURCE = SNOWFLAKE_POSTGRES
     POSTGRES_INSTANCE_NAME = '{pg_instance}'
     ENABLED = TRUE;
   ```

2. Create CLD database: `{cld_database}` with `CATALOG_SOURCE = SNOWFLAKE_POSTGRES`:
   ```sql
   CREATE DATABASE {cld_database}
     CATALOG = '{prefix}_streetlights_catalog_int'
     LINKED_CATALOG = TRUE;
   ```

## CLD Propagation

After CLD creation, tables take ~30 seconds to appear.
- Wait 30s, then verify: `SHOW TABLES IN DATABASE {cld_database}`
- If tables not visible after 3 retries (30s each): STOP and report issue

## Verification

- Run `gate.py check_cld_healthy`
- Show table list from CLD to user
- Confirm all 7 tables are visible
