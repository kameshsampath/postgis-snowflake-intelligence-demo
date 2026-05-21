---
name: streetlights-demo-step-8
description: Train ML Forecast model on energy consumption data
---

# Step 8: Train ML Forecast

## Prerequisites

- CLD database exists with energy_consumption table (Step 4 complete)
- Warehouse exists (from `snowflake/01_setup.sql`)

## Steps

1. Read manifest for database/warehouse names
2. Execute ML Forecast DDL:
   ```bash
   snow sql -f snowflake/05_ml_forecast.sql
   ```
3. Wait for model training to complete (may take 2-5 minutes)

## Key Details

- Trains a FORECAST model on energy consumption time-series data
- Predicts future energy usage patterns per street light or zone
- Useful for budget planning and proactive maintenance scheduling

## Verification

- Run `gate.py check_forecast_model_ready`
- Verify model exists:
  ```sql
  SHOW SNOWFLAKE.ML.FORECAST MODELS IN SCHEMA {database}.{schema};
  ```
- Test a forecast query:
  ```sql
  CALL {database}.{schema}.BULB_FAILURE_FORECASTER!FORECAST(
    FORECASTING_PERIODS => 30
  );
  ```
