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

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 8: Train ML Forecast

## Why this matters

**Predictive analytics on live Iceberg data** — The FORECAST model trains directly on CLD tables that reflect the latest Iceberg state from Postgres. When new energy consumption data lands in PG, it flows through the CLD automatically — the model always trains on fresh data without manual refresh.

**Proactive maintenance** — Instead of waiting for bulbs to fail, the forecast predicts future failure patterns from energy consumption anomalies. A light consuming significantly more or less energy than predicted is a leading indicator of failure — enabling maintenance scheduling *before* the outage.

**IDD connection** — The ML model declaration is [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14) at the analytics layer: a single DDL statement encodes the entire training pipeline (data selection, time-series configuration, model parameters). Snowflake handles the ML engineering underneath.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

## What we'll do

Submit ML Forecast training as a background job. The warehouse temporarily resizes to MEDIUM for
training and auto-resizes back to XSMALL when done.

> **In `$streetlights-demo app`**: this step runs as the **Forecast worker** in Team `streetlights-app-phase`, in parallel with the Deploy worker (step 9). Both are spawned by the Synthesizer agent; step 10 runs after both complete.

- Apply schema grants (including `CREATE DYNAMIC TABLE`) and resize warehouse to MEDIUM
- Create `energy_daily_vw` view joining CLD tables (lat/lng/neighborhood/status for location-aware prediction)
- Materialize as `energy_daily_tbl` **Dynamic Table** (TARGET_LAG=1 hour — auto-refreshes when new Iceberg data arrives in PG)
- Train `energy_forecast` FORECAST model on `energy_daily_tbl`
- Mark step-8 COMPLETE after training finishes

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> ⚠️ **MANDATORY**: Plan mode is already active. Run the dry-run command and present the output to the user.

Show the execution plan to the user:
```bash
uv run gate --step step-8 --action dry-run
```
Present the output, then ask user to proceed.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a plan summary of what the step will execute. Proceed to Execution only after the user confirms.

## Execution

### Prerequisites

- CLD database exists with `energy_consumption` and `street_lights` tables (Step 4 complete)
- Warehouse `{warehouse}` exists (Step 4 complete)

### Steps

1. Read manifest for `prefix`, `role`, `connection`, `warehouse`.

2. **Run training synchronously** (wait for completion):
   ```bash
   snow sql -f snowflake/05_ml_forecast.sql \
     -D "PREFIX={manifest.demo.prefix.upper()}" \
     -D "ROLE={manifest.snowflake.role}" \
     -c {manifest.snowflake.connection} \
     --enable-templating STANDARD --format json
   ```
   When called from `$streetlights-demo app`, this runs as a background Forecast worker — the
   worker itself is a separate agent, so the SQL can block until training completes.

3. **Inform the user** (present verbatim):

   > Training complete. `energy_daily_tbl` Dynamic Table created (TARGET_LAG=1 hour).
   > The warehouse has auto-resized back to XSMALL.
   > Marking step-8 COMPLETE.

### Key Details

- `energy_daily_vw` joins CLD `energy_consumption` + `street_lights` for lat/lng/neighborhood/status
- `ANY_VALUE()` is safe: location columns are constant per `light_id` across dates
- `energy_daily_tbl` is a Dynamic Table (TARGET_LAG=1 hour) — refreshes automatically when PG Iceberg data changes
- Warehouse resize is embedded in the SQL: MEDIUM before training, XSMALL after
- `SYSTEM$REFERENCE('TABLE',...)` is used so the ML service can cross the CLD boundary

## What we did

- ✅ Grants applied: `CREATE VIEW` + `CREATE DYNAMIC TABLE` + `CREATE SNOWFLAKE.ML.FORECAST` on schema
- ✅ Warehouse resized to MEDIUM for training
- ✅ `energy_daily_vw` created with `series_id`, `ds`, `daily_kwh`, `latitude`, `longitude`, `neighborhood`, `status`
- ✅ `energy_daily_tbl` Dynamic Table created (TARGET_LAG=1 hour — auto-refreshes from Iceberg)
- ✅ `energy_forecast` training complete
- ✅ Warehouse auto-resized back to XSMALL

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 8` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~5 — (2 SQL grants + 1 WH resize + 1 view DDL + 1 forecast DDL without this skill) |
| **Step ICR** | **5** (5 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Mark COMPLETE

```bash
uv run gate --step step-8 --action complete
```

## Next

When invoked standalone (`$streetlights-demo step 8`):

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Training complete. Continue to Step 9: Deploy SiS App?"
- Options: ["Yes, proceed to Step 9", "Stop here"]

If "Stop here": show `$streetlights-demo step 9` for later resumption.

> **Note**: When invoked as the Forecast worker from `$streetlights-demo app`, the Synthesizer
> handles convergence — do not ask the user this question in the worker context.
