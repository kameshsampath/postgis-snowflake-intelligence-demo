---
name: streetlights-demo-step-8
description: Train ML Forecast model on energy consumption data
---

# Step 8: Train ML Forecast

## What we'll do

Train a FORECAST model on energy consumption time-series data to predict future bulb failures. This enables proactive maintenance scheduling.

- Deploy ML Forecast DDL on energy consumption data
- Wait for model training (~2-5 minutes)
- Verify the model produces predictions

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 8"
- Question: "Ready to train the ML Forecast model? (training takes 2-5 minutes)"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- CLD database exists with energy_consumption table (Step 4 complete)
- Warehouse exists (from `snowflake/01_setup.sql`)

### Steps

1. Read manifest for database/warehouse names
2. Execute ML Forecast DDL:
   ```bash
   snow sql -f snowflake/05_ml_forecast.sql
   ```
3. Wait for model training to complete (may take 2-5 minutes)

### Key Details

- Trains a FORECAST model on energy consumption time-series data
- Predicts future energy usage patterns per street light or zone
- Useful for budget planning and proactive maintenance scheduling

### Verification

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

## What we did

- ✅ Forecast model trained on energy consumption data
- ✅ Model produces 30-day predictions
- ✅ Gate check: `check_forecast_model_ready` passed
