---
name: streetlights-demo-app
description: App phase orchestration — ML Forecast + SiS deploy + Validation (steps 8–10) via Team App
---

## Gate

```bash
uv run gate --step step-8 --prior-step step-7 --action check
```

If BLOCK: inform the user that the Infrastructure phase (setup + steps 1–7) must be complete
before starting the App phase. Run `$streetlights-demo step 7` first.
If PASS: continue below.

## Mark Steps IN_PROGRESS

```bash
uv run gate --step step-8 --desc "Training ML Forecast (App phase)" --action start
uv run gate --step step-9 --desc "Deploying SiS App (App phase)" --action start
```

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking both steps IN_PROGRESS.
> Do NOT spawn workers until plan mode is confirmed.

# App Phase: ML Forecast + Streamlit + Validation

## Why this matters

**Infrastructure phase is complete.** You have a live Intelligence Agent, a Semantic View for
structured analytics, and Cortex Search for text retrieval — all backed by Iceberg tables in
Snowflake Postgres.

The App phase adds the predictive and visual layers:

- **Step 8 — ML Forecast**: Train a time-series FORECAST model on energy consumption. The model
  uses `energy_daily_tbl`, a Dynamic Table that auto-refreshes when new Iceberg data arrives — so
  the forecast always reflects the latest readings without manual intervention.

- **Step 9 — SiS App**: Deploy the multi-page Streamlit in Snowflake application. It composes
  *all* prior infrastructure into one interface: maps, search, analytics, forecast, and agent chat.
  No external servers, no credentials to manage — the app runs inside your Snowflake account.

- **Step 10 — Validation**: Run the end-to-end sanity gate and compile the full IDD session
  summary with Infrastructure + App ICR metrics.

## What we'll do

The Forecast worker (step 8) and Deploy worker (step 9) run **in parallel** as Team
`streetlights-app-phase`. This Synthesizer agent (the lead) waits for both to complete, then
runs step 10 validation.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with the summary below. Proceed only after the user confirms.

**Plan summary**:
1. Spawn Forecast worker (background) — trains ML model synchronously, marks step-8 COMPLETE
2. Spawn Deploy worker (background) — deploys SiS app, marks step-9 COMPLETE
3. Synthesizer waits for both task notifications (convergence)
4. Synthesizer runs step-10 validation and IDD summary

## Execution

### Spawn Team

```python
team_create("streetlights-app-phase")
task_create("Train ML Forecast", subject="step-8")
task_create("Deploy SiS App", subject="step-9")
```

### Spawn Forecast Worker (background)

Spawn a background general-purpose agent with `team_name="streetlights-app-phase"`, name
`"Forecast"`. Worker instructions:

> Follow `steps/step-8.md` from the Execution section onward (gate already passed and step
> marked IN_PROGRESS by Synthesizer). Run `05_ml_forecast.sql` synchronously. When training
> completes, run `uv run gate --step step-8 --action complete` and mark the task done.
> Do NOT ask the user a "Next" question — the Synthesizer handles convergence.

### Spawn Deploy Worker (background)

Spawn a background general-purpose agent with `team_name="streetlights-app-phase"`, name
`"Deploy"`. Worker instructions:

> Follow `steps/step-9.md` from the Execution section onward (gate already passed and step
> marked IN_PROGRESS by Synthesizer). Invoke `$developing-with-streamlit-in-snowflake`
> [bundled] to deploy the app from `app/` directory. When deployment completes, run
> `uv run gate --step step-9 --action complete` and mark the task done.
> Do NOT ask the user a "Next" question — the Synthesizer handles convergence.

### Synthesizer: Wait for Convergence

Wait for both worker task notifications. Both must complete before proceeding to step 10.

Present a status update when each worker finishes:
- Forecast complete: "✅ ML Forecast trained — `energy_daily_tbl` Dynamic Table live."
- Deploy complete: "✅ Streamlit app deployed — all 6 pages accessible."

### Step 10 — Validation

```bash
uv run gate --step step-10 --prior-step step-9 --action check
uv run gate --step step-10 --desc "Validating end-to-end demo" --action start
```

Run the sanity gate:

```bash
uv run python scripts/sanity_gate.py
```

Verify all 8 components pass:
- Manifest valid
- PG instance reachable
- CLD healthy (all 7 tables visible)
- Semantic View queryable
- Cortex Search ACTIVE
- Agent accessible
- Forecast model trained
- SiS app accessible

```bash
uv run gate --step step-10 --action complete
```

### Tear Down Team

```python
team_delete("streetlights-app-phase")
```

## What we did

- ✅ Forecast worker: `energy_daily_tbl` Dynamic Table created (TARGET_LAG=1 hour), `energy_forecast` model trained
- ✅ Deploy worker: Streamlit app deployed to `{PREFIX}_STREETLIGHTS.PUBLIC.STREETLIGHTS_APP`
- ✅ Sanity gate: all 8 components passed
- ✅ Step 10 marked COMPLETE

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user.

### IDD Metrics — App Phase

| Step | Invocation | Trad. Ops (baseline) | Step ICR |
|------|------------|----------------------|----------|
| 8 — ML Forecast | Forecast worker | 5  | 5  |
| 9 — Deploy SiS  | Deploy worker   | 9  | 9  |
| 10 — Validate   | Synthesizer     | 8  | 8  |
| **App phase**   | **1 `$streetlights-demo app` invocation** | **22** | **22** |

> **App phase ICR: 22** — all three App steps ran from a single `$streetlights-demo app` invocation.

### Full Session IDD Summary

Run `uv run idd-metrics` for the combined Infrastructure + App picture, or present from
`references/idd-metrics.md`:

| Phase | Invocations | Trad. Ops | ICR |
|-------|:-----------:|:---------:|----:|
| Infrastructure (steps 1–7) | 7 | 60 | 8 avg/step |
| App (steps 8–10, parallel) | 1 | 22 | 22 |
| **Total** | **8** | **82** | — |

> End-to-end [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c):
> infrastructure as intent + parallelism as intent + AI handles *how*.
