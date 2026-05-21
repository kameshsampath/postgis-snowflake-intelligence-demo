---
name: streetlights-demo-step-7
description: Create Intelligence Agent with Semantic View and Cortex Search
---

# Step 7: Create Intelligence Agent

## Prerequisites

- Semantic View exists (Step 5 complete)
- Cortex Search service is ACTIVE (Step 6 complete)

## Steps

1. Read manifest for database/warehouse names
2. Execute Agent DDL:
   ```bash
   snow sql -f snowflake/04_intelligence_agent.sql
   ```
3. Verify agent responds to a test query

## Key Details

- The Intelligence Agent combines TWO data sources:
  - **Semantic View** — for structured SQL queries (counts, aggregations, rankings)
  - **Cortex Search** — for unstructured text retrieval (descriptions, issues)
- This enables natural language questions that span both structured and unstructured data

## Verification

- Run `gate.py check_agent_accessible`
- Test with a sample question:
  ```
  "How many street lights are currently faulty?"
  ```
- Verify agent returns a coherent answer using the Semantic View
- Test text retrieval:
  ```
  "Find maintenance records about exposed wires"
  ```
- Verify agent uses Cortex Search for this type of query
