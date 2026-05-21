---
name: streetlights-demo-step-6
description: Create Cortex Search service on maintenance records
---

# Step 6: Create Cortex Search Service

## What we'll do

Create a Cortex Search service that indexes maintenance record descriptions for semantic text search. This enables queries like "find safety hazards" or "flickering light issues."

- Deploy Cortex Search DDL on the maintenance_records table
- Wait for indexing to complete (service becomes ACTIVE)
- Test semantic search capability

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 6"
- Question: "Ready to create the Cortex Search service on maintenance records?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- CLD database exists with tables visible (Step 4 complete)
- Snowflake warehouse exists (from `snowflake/01_setup.sql`)

### Steps

1. Read manifest for database/warehouse names
2. Execute Cortex Search DDL:
   ```bash
   snow sql -f snowflake/03_cortex_search.sql
   ```
3. Wait for service to become ACTIVE (may take 1-2 minutes)

### Key Details

- Creates a Cortex Search service on maintenance record descriptions
- Enables semantic text search (e.g., "find safety hazards", "flickering lights")
- Service indexes the `description` column from `maintenance_records`

### Verification

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

## What we did

- ✅ Cortex Search service created and indexed
- ✅ Service status: ACTIVE
- ✅ Semantic search verified with test query
- ✅ Gate check: `check_cortex_search_ready` passed
