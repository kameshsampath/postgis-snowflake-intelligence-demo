---
name: streetlights-demo-step-6
description: Create Cortex Search service on maintenance records
---

# Step 6: Create Cortex Search Service

## Prerequisites

- CLD database exists with tables visible (Step 4 complete)
- Snowflake warehouse exists (from `snowflake/01_setup.sql`)

## Steps

1. Read manifest for database/warehouse names
2. Execute Cortex Search DDL:
   ```bash
   snow sql -f snowflake/03_cortex_search.sql
   ```
3. Wait for service to become ACTIVE (may take 1-2 minutes)

## Key Details

- Creates a Cortex Search service on maintenance record descriptions
- Enables semantic text search (e.g., "find safety hazards", "flickering lights")
- Service indexes the `description` column from `maintenance_records`

## Verification

- Run `gate.py check_cortex_search_ready`
- Service status must be `ACTIVE`
- Test a sample search query:
  ```sql
  SELECT * FROM TABLE(
    {database}.{schema}.MAINTENANCE_SEARCH(
      SEARCH_QUERY => 'safety hazard exposed wires'
    )
  ) LIMIT 5;
  ```
