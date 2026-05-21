---
name: streetlights-demo-step-10
description: Run end-to-end validation and demonstrate the complete pipeline
---

# Step 10: Validate & Demo

## Prerequisites

- All previous steps (1-9) complete

## Validation

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

## Demo Queries

Try these natural language questions with the Intelligence Agent:

| Question | Expected Source |
|----------|---------------|
| "How many street lights are faulty?" | Semantic View |
| "Which neighborhoods have the most maintenance issues?" | Semantic View |
| "Find reports about exposed wires or sparking" | Cortex Search |
| "What's the average energy consumption by zone?" | Semantic View |
| "Show me urgent safety hazards" | Cortex Search |

## Forecast Demo

```sql
-- 30-day failure forecast
CALL {database}.{schema}.BULB_FAILURE_FORECASTER!FORECAST(
  FORECASTING_PERIODS => 30
);
```

## Celebration

The demo is fully operational. You now have:
- PostgreSQL with pg_lake Iceberg tables
- Native CLD sync to Snowflake (no CDC pipeline needed)
- Semantic View for structured analytics
- Cortex Search for text retrieval
- Intelligence Agent combining both
- ML Forecast for predictive maintenance
- Multi-page Streamlit dashboard

All powered by a single `$streetlights-demo` skill workflow.
