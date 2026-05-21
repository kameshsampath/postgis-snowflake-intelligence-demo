---
name: streetlights-demo-step-7
description: Create Intelligence Agent with Semantic View and Cortex Search
---

# Step 7: Create Intelligence Agent

## What we'll do

Create the Cortex Intelligence Agent that combines Semantic View (structured analytics) with Cortex Search (text retrieval) and chart generation into a single natural language interface.

- Deploy Agent DDL with full FROM SPECIFICATION (orchestration rules, tools, sample questions)
- Verify the agent routes queries correctly
- Test both structured and unstructured queries

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 7"
- Question: "Ready to create the Intelligence Agent?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- Semantic View exists (Step 5 complete)
- Cortex Search service is ACTIVE (Step 6 complete)

### Steps

1. Read manifest for database/warehouse names
2. Execute Agent DDL:
   ```bash
   snow sql -f snowflake/04_intelligence_agent.sql
   ```
3. Verify agent responds to a test query

### Key Details

- The Intelligence Agent combines THREE tools:
  - **StreetlightsAnalyst** (Cortex Analyst) — for structured SQL queries (counts, aggregations, rankings)
  - **MaintenanceSearch** (Cortex Search) — for unstructured text retrieval (descriptions, issues)
  - **data_to_chart** — for generating visualizations from query results
- Orchestration instructions control routing between tools
- Map links are auto-generated when results include lat/lng columns

### Verification

- Run `gate.py check_agent_accessible`
- Test with a structured query:
  ```
  "How many street lights are currently faulty?"
  ```
- Test with a text search query:
  ```
  "Find maintenance records about exposed wires"
  ```
- Verify routing: structured → Analyst, text → Search

## What we did

- ✅ Intelligence Agent created with FROM SPECIFICATION
- ✅ Orchestration routing rules configured (Analyst vs Search)
- ✅ Map link generation enabled for lat/lng results
- ✅ Gate check: `check_agent_accessible` passed
