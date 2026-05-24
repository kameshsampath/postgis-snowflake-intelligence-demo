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
- Question: "Ready to proceed with ML Forecast training? (fires in background, training takes 5-15 minutes on MEDIUM warehouse)"
- Options: ["Yes, proceed", "Skip this step"]

---

## What we'll do

Submit ML Forecast training as a background job, then proceed immediately to Step 9. The warehouse temporarily resizes to MEDIUM for training and auto-resizes back to XSMALL when done.

- Apply schema grants and resize warehouse to MEDIUM
- Fire the forecast training SQL in background (do not wait)
- The training view `energy_daily_vw` includes lat/lng/neighborhood/status for location-aware failure prediction
- Move to Step 9 immediately — the step-9 gate automatically verifies the model is ready before allowing deployment to proceed

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> ⚠️ **MANDATORY**: Call `enter_plan_mode` BEFORE running or presenting the dry-run output. Do NOT show dry-run content until plan mode is active. Call `exit_plan_mode` only after the user confirms. Then execute.

Show the execution plan to the user:
```bash
uv run gate --step step-8 --action dry-run
```
Present the output, then ask user to proceed.

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 8"
- Question: "Ready to submit ML Forecast training? (runs in background on MEDIUM warehouse)"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- CLD database exists with `energy_consumption` and `street_lights` tables (Step 4 complete)
- Warehouse `{warehouse}` exists (Step 4 complete)

### Steps

1. Read manifest for `prefix`, `role`, `connection`, `warehouse`.

2. **Fire training in background** (do NOT wait — return immediately):
   ```bash
   snow sql -f snowflake/05_ml_forecast.sql \
     -D "PREFIX={manifest.demo.prefix.upper()}" \
     -D "ROLE={manifest.snowflake.role}" \
     -c {manifest.snowflake.connection} \
     --enable-templating STANDARD --format json
   ```
   Run with `run_in_background=True`. If the command starts without an immediate error, proceed.

3. **Inform the user** (present verbatim):

   > Training submitted on `{warehouse}` (resized to MEDIUM).
   > The warehouse will auto-resize back to XSMALL when training completes.
   > Proceeding to Step 9 now — the step-9 gate will automatically verify
   > the model is ready and mark Step 8 complete before deployment proceeds.

   > ⚠️ **Do NOT call `uv run gate --step step-8 --action complete` manually.**
   > The gate auto-marks Step 8 COMPLETE via the step-9 prior-step backfill
   > mechanism when `SHOW SNOWFLAKE.ML.FORECAST` confirms the model exists.

### Key Details

- `energy_daily_vw` joins CLD `energy_consumption` + `street_lights` for lat/lng/neighborhood/status
- `ANY_VALUE()` is safe: location columns are constant per `light_id` across dates
- Warehouse resize is embedded in the SQL: MEDIUM before training, XSMALL after
- The gate's `--prior-step` backfill walks the chain and calls `_check_forecast()` automatically

### Gate auto-backfill flow

```
Step 9 gate (--prior-step step-8):
  → step-8 is IN_PROGRESS (not COMPLETE)
  → runs _check_forecast(): SHOW SNOWFLAKE.ML.FORECAST ...
  → model exists?  YES → auto-marks step-8 COMPLETE → step-9 PASS
  → model missing? NO  → BLOCK "still training" → retry in a few minutes
```

> **No manual verification needed in step-8.** The gate handles it.

## What we did

- ✅ Grants applied: `CREATE VIEW` + `CREATE SNOWFLAKE.ML.FORECAST` on schema (as ACCOUNTADMIN)
- ✅ Warehouse resized to MEDIUM for training
- ✅ `energy_daily_vw` created with `series_id`, `ds`, `daily_kwh`, `latitude`, `longitude`, `neighborhood`, `status`
- ✅ `energy_forecast` training submitted in background
- ⏳ Warehouse auto-resizes to XSMALL when training completes
- ⚠️ Step-9 gate auto-verifies and marks Step 8 COMPLETE when model is ready — no manual action needed

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 8` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~5 — (2 SQL grants + 1 WH resize + 1 view DDL + 1 forecast DDL without this skill) |
| **Step ICR** | **5** (5 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Training is running in background. Continue to Step 9: Deploy SiS App?"
- Options: ["Yes, proceed to Step 9", "Wait here until training finishes"]

If "Wait here": poll with `SHOW SNOWFLAKE.ML.FORECAST IN DATABASE {database}` every 2 minutes until the model appears, then proceed to Step 9.
If "Stop here": show `$streetlights-demo step 9` for later resumption.
