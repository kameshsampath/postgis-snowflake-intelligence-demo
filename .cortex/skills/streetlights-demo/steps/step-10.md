---
name: streetlights-demo-step-10
description: Run end-to-end validation and demonstrate the complete pipeline
---

## Gate

```bash
uv run gate --step step-10 --prior-step step-9 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-10 --desc "Validating end-to-end demo" --action start
```

# Step 10: Validate & Demo

## What we'll do

Run the full end-to-end sanity gate to verify all components are operational, then demonstrate the Intelligence Agent with sample queries.

- Execute the sanity gate script (checks all 8 components)
- Display top 5 demo questions with routing explanation
- Show bonus combined queries for advanced testing

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 10"
- Question: "Ready to run end-to-end validation?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Validation

1. Run the end-to-end sanity gate:
   ```bash
   uv run python scripts/sanity_gate.py
   ```
2. Verify all checks pass:
   - Manifest exists and is valid
   - PG instance reachable
   - CLD healthy (all 7 tables visible)
   - Semantic View queryable
   - Cortex Search service ACTIVE
   - Agent responds to queries
   - Forecast model trained
   - SiS app accessible

### Forecast Demo

```sql
-- 30-day failure forecast
CALL {database}.{schema}.BULB_FAILURE_FORECASTER!FORECAST(
  FORECASTING_PERIODS => 30
);
```

## What we did

- ✅ All gates passed (manifest, PG, CLD, Semantic View, Search, Agent, Forecast, SiS)
- ✅ End-to-end sanity check passed

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

## Try these with Snowflake Intelligence

| # | Question | Routing | What it tests |
|---|----------|---------|---------------|
| 1 | "How many street lights are currently faulty?" | Analyst → SQL | Status aggregation |
| 2 | "Which neighborhoods have the highest energy consumption?" | Analyst → SQL | Cross-table join |
| 3 | "Find maintenance reports about exposed wires or sparking" | Search → text | Semantic similarity |
| 4 | "What is the average repair cost by maintenance type?" | Analyst → SQL | Grouped metrics |
| 5 | "Show me the top 5 neighborhoods by maintenance frequency" | Analyst → SQL | Rankings |

**Bonus — try these combined queries:**
- "Tell me about maintenance issues in the busiest neighborhood" (Agent routes to both tools)
- "What's the situation with faulty lights and their repair status?" (Combined routing)

The demo is fully operational. You now have:
- PostgreSQL with pg_lake Iceberg tables
- Native CLD sync to Snowflake (no CDC pipeline needed)
- Semantic View for structured analytics
- Cortex Search for text retrieval
- Intelligence Agent combining both (UI auto-renders charts)
- ML Forecast for predictive maintenance
- Multi-page Streamlit dashboard

All powered by a single `$streetlights-demo` skill workflow.

## Mark COMPLETE

```bash
uv run gate --step step-10 --action complete
```

## Next

Demo complete! All 10 steps finished successfully. The streetlights intelligence system is fully operational.
