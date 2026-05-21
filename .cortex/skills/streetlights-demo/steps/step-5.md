---
name: streetlights-demo-step-5
description: Create Semantic View over CLD tables
---

# Step 5: Create Semantic View

## Prerequisites

- CLD database exists and tables are visible (Step 4 complete)

## Steps

1. Read manifest for database/warehouse names
2. Execute Semantic View DDL:
   ```bash
   snow sql -f snowflake/02_semantic_view.sql
   ```
3. Verify the Semantic View was created successfully

## Key Details

- The Semantic View references CLD tables with **quoted lowercase identifiers**
  (e.g., `"streetlights"."street_lights"`) because CLD preserves PostgreSQL casing
- Geography columns use `ST_MAKEPOINT(longitude, latitude)` for spatial reconstruction
- Dimensions, measures, and filters are defined for natural language querying

## Verification

- Run `gate.py check_semantic_view_exists`
- Show the Semantic View definition to user
- Test a simple query against the view
