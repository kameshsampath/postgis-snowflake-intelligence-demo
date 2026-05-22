---
name: streetlights-demo-step-8
description: Train ML Forecast model on energy consumption data
---

## Gate

```bash
uv run gate --step step-8 --prior-step step-7 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-8 --desc "Training ML Forecast model" --action start
```

# Step 8: Train ML Forecast

## Why this matters

**Predictive analytics on live Iceberg data** — The FORECAST model trains directly on CLD tables that reflect the latest Iceberg state from Postgres. When new energy consumption data lands in PG, it flows through the CLD automatically — the model always trains on fresh data without manual refresh.

**Proactive maintenance** — Instead of waiting for bulbs to fail, the forecast predicts future failure patterns from energy consumption anomalies. A light consuming significantly more or less energy than predicted is a leading indicator of failure — enabling maintenance scheduling *before* the outage.

**IDD connection** — The ML model declaration is [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14) at the analytics layer: a single DDL statement encodes the entire training pipeline (data selection, time-series configuration, model parameters). Snowflake handles the ML engineering underneath.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

---

**STOP** — Use `ask_user_question` to confirm:
- Header: "Step 8"
- Question: "Ready to proceed with ML Forecast training? (trains on energy data, takes 2-5 minutes)"
- Options: ["Yes, proceed", "Skip this step"]

---

## What we'll do

Train a FORECAST model on energy consumption time-series data to predict future bulb failures. This enables proactive maintenance scheduling.

- Deploy ML Forecast DDL on energy consumption data
- Wait for model training (~2-5 minutes)
- Verify the model produces predictions

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

Show the execution plan to the user:
```bash
uv run gate --step step-8 --action dry-run
```
Present the output, then ask user to proceed.

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

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

## Mark COMPLETE

```bash
uv run gate --step step-8 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 9: Deploy SiS App?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 9` for later resumption.
