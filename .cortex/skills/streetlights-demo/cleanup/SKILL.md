---
name: streetlights-demo-cleanup
description: Remove all demo resources (reverse order)
---

# Cleanup: Remove Demo Resources

This will DESTROY all demo resources.

## Prerequisites

- `.streetlights-demo/manifest.toml` exists (to read resource names)

## Plan Mode: Show What Will Be Dropped

Before executing anything, load the manifest and present the full cleanup plan in plan mode.

**STOP** — call `enter_plan_mode` and present this table (fill in values from manifest):

```
Resource                          | Value
----------------------------------|--------------------------------------------
Intelligence Agent                | {database}.PUBLIC.STREETLIGHTS_AGENT
Cortex Search Service             | {database}.PUBLIC.MAINTENANCE_SEARCH
Semantic View                     | {database}.PUBLIC.STREETLIGHTS_SEMANTIC_VIEW
CLD Database                      | {cld_database}
Catalog Integration               | {prefix}_streetlights_catalog_int
Postgres Instance (optional ⚠️)   | {pg_instance}  — ask separately, billable
Network Policy (if demo-created)  | {pg_network_policy}  — blank = pre-existing, skip
Warehouse                         | {warehouse}
Main Database                     | {database}
Local config                      | .streetlights-demo/
```

Steps that existed (SiS app, Forecast model) are dropped with `IF EXISTS` — safe to run even if not created.

Use `ask_user_question` to confirm:
- Header: "Cleanup"
- Question: "Review the plan above. Proceed with cleanup? (The Postgres instance drop will be confirmed separately.)"
- Options: ["Yes, clean up", "Cancel"]

If user cancels: stop. Do not execute anything.

If user confirms: call `exit_plan_mode`, then execute the steps below in order.

## Rollback Order (reverse of creation)

Execute in this exact order — each step depends on the previous:

### 0. Deregister from Snowflake Intelligence

Must run BEFORE Drop Agent — removes the agent from the Intelligence UI registry.

```sql
-- Note: syntax is DROP AGENT (not REMOVE AGENT)
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  DROP AGENT {database}.{schema}.STREETLIGHTS_AGENT;
```

### 1. Drop SiS App

```sql
DROP STREAMLIT IF EXISTS {database}.{schema}.STREETLIGHTS_APP;
```

### 2. Drop FORECAST Model

```sql
DROP SNOWFLAKE.ML.FORECAST IF EXISTS {database}.{schema}.BULB_FAILURE_FORECASTER;
```

### 3. Drop Intelligence Agent

```sql
DROP AGENT IF EXISTS {database}.{schema}.STREETLIGHTS_AGENT;
```

### 4. Drop Cortex Search Service

```sql
DROP CORTEX SEARCH SERVICE IF EXISTS {database}.{schema}.MAINTENANCE_SEARCH;
```

### 5. Drop Semantic View

```sql
DROP SEMANTIC VIEW IF EXISTS {database}.{schema}.STREETLIGHTS_SEMANTIC_VIEW;
```

### 6. Drop CLD Database

```sql
DROP DATABASE IF EXISTS {cld_database};
```

### 7. Drop Catalog Integration

```sql
DROP CATALOG INTEGRATION IF EXISTS {prefix}_streetlights_catalog_int;
```

### 8. Drop PG Instance (Optional — STOP and ask user first)

**⚠️ BILLABLE + DESTRUCTIVE** — Use `ask_user_question` before proceeding:
- Header: "Drop Postgres Instance"
- Question: "Drop the Postgres instance `{pg_instance}`? This stops billing but permanently deletes all Iceberg data on managed storage."
- Options: ["Yes, drop it", "No, keep it running"]

If user says **No**: skip this step and Steps 9–10 (warehouse and main database can still be dropped independently). Leave the PG instance, network policy, and managed Iceberg data intact.

If user says **Yes**, run in this order:

1. **Detach and drop demo network policy** (only if `pg_network_policy` is set in manifest — skip if blank, meaning a pre-existing policy was used):
   ```sql
   ALTER POSTGRES INSTANCE {pg_instance} UNSET NETWORK_POLICY;
   DROP NETWORK POLICY IF EXISTS {pg_network_policy};
   ```
   > **Never** drop a network policy that was not created by this demo. Check `pg_network_policy` in manifest — if blank, skip both statements.

2. **Drop the PG instance**:
   ```sql
   DROP POSTGRES INSTANCE IF EXISTS {pg_instance};
   ```

Route to `$snowflake-postgres` for the DROP POSTGRES INSTANCE operation.

### 9. Drop Warehouse

```sql
DROP WAREHOUSE IF EXISTS {warehouse};
```

### 10. Drop Database

```sql
DROP DATABASE IF EXISTS {database};
```

### 11. Remove Local Config

```bash
rm -rf .streetlights-demo/
```

### 12. Reset Gate State

Reset all step progress tracking (already handled by step 11 which removes `.streetlights-demo/`):
```bash
# The manifest removal in step 11 resets gate state automatically.
# If you want to reset only gate state without removing the full manifest:
uv run gate --step step-7 --action reset
uv run gate --step step-6 --action reset
uv run gate --step step-5 --action reset
uv run gate --step step-4 --action reset
uv run gate --step step-3 --action reset
uv run gate --step step-2 --action reset
uv run gate --step step-1 --action reset
uv run gate --step setup --action reset
```

### 13. Remove Generated CSV Data (optional)

**Optional** — only needed if you want a completely clean slate before re-running Step 1.
Keep the CSVs if you want to reload the same data without regenerating.

```bash
rm -rf data/
```

Files removed: `street_lights.csv`, `maintenance_records.csv`, `energy_consumption.csv`,
`light_sensors.csv`, `weather_enrichment.csv`, `demographics.csv`, `power_grid_zones.csv`

Also removes the generated Iceberg DDL:
```bash
rm -f init/02_create_iceberg_tables.sql
```

## Execution Notes

- Show the full cleanup plan in plan mode first — one confirmation covers steps 0–7 and 9–13
- The Postgres instance drop (step 8) has its own `ask_user_question` — billable + destructive
- If any step fails, continue with remaining steps (resources may already be gone)
- Route to `$snowflake-postgres` for PG instance and CLD cleanup
