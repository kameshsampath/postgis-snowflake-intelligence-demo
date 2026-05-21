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
DROP SEMANTIC VIEW IF EXISTS {database}.{schema}.STREETLIGHTS_SEMANTIC;
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

## Execution Notes

- Confirm with the user before EACH step
- Show what will be dropped before executing
- If any step fails, continue with remaining steps (resources may already be gone)
- Route to `$snowflake-postgres` for PG instance and CLD cleanup
