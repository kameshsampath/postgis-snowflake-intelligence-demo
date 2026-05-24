---
name: streetlights-demo-cleanup
description: Remove all demo resources (reverse order)
---

# Cleanup: Remove Demo Resources

This will DESTROY all demo resources. Confirm each step with the user.

## Prerequisites

- `.streetlights-demo/manifest.toml` exists (to read resource names)

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

### 8. Drop PG Instance

**BILLABLE** — dropping the instance stops billing.

Route to `$snowflake-postgres` to drop:
```sql
DROP POSTGRES INSTANCE IF EXISTS {pg_instance};
```

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

- Confirm with the user before EACH step
- Show what will be dropped before executing
- If any step fails, continue with remaining steps (resources may already be gone)
- Route to `$snowflake-postgres` for PG instance and CLD cleanup
