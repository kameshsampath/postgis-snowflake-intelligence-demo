---
name: streetlights-demo-step-9
description: Deploy multi-page Streamlit in Snowflake application
---

## Gate

```bash
uv run gate --step step-9 --prior-step step-7 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

> **Note**: In `$streetlights-demo app`, this step runs as the **Deploy worker** in Team
> `streetlights-app-phase`, in parallel with the Forecast worker (step 8). Both workers gate
> on step-7 completion; the Synthesizer waits for both before starting step 10.

## Mark IN_PROGRESS

```bash
uv run gate --step step-9 --desc "Deploying SiS app" --action start
```

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 9: Deploy SiS App

## Why this matters

**Last-mile delivery, zero external deployment** — Streamlit in Snowflake (SiS) runs entirely *inside* your Snowflake account. No external servers, no Docker containers, no cloud provider accounts needed. The app accesses data with Snowflake's built-in security — no credentials to manage, no network rules to punch through.

**Composing everything built so far** — The SiS app is the user-facing surface that combines *all* prior steps into one interface: maps (from Iceberg data), search (from Cortex Search), analytics (from Semantic View), forecasts (from ML model), and the agent chat (from Intelligence Agent). Each page exercises a different piece of the infrastructure stack.

**IDD connection** — The SiS deployment is the final layer of [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14): the app source directory *is* the intent, and the `$developing-with-streamlit-in-snowflake` skill handles deployment mechanics (staging, permissions, CREATE STREAMLIT).

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

## What we'll do

Deploy the multi-page Streamlit in Snowflake (SiS) application that provides a visual dashboard for the streetlight data, including maps, charts, search, and an agent chat interface.

- Deploy app source from `app/` directory
- Configure warehouse and database references
- Verify the app loads and all pages work

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> ⚠️ **MANDATORY**: Plan mode is already active. Run the dry-run command and present the output to the user.

Show the execution plan to the user:
```bash
uv run gate --step step-9 --action dry-run
```
Present the output, then ask user to proceed.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a plan summary of what the step will execute. Proceed to Execution only after the user confirms.

## Execution

### Prerequisites

- All Snowflake objects created (Steps 5-8 complete)
- App source exists in `app/` directory

### Steps

1. Read manifest for `prefix`, `connection`.

2. Deploy via `snow streamlit deploy`:
   ```bash
   cd app && snow streamlit deploy --replace -c {manifest.snowflake.connection}
   ```
   `app/snowflake.yml` defines the entity: entry point `home.py`, warehouse
   `{PREFIX}_STREETLIGHTS_WH`, target `{PREFIX}_STREETLIGHTS.PUBLIC.STREETLIGHTS_APP`.
   Note: `definition_version: 2` does NOT resolve Jinja `{{ ctx.env.PREFIX }}` in
   identifier fields — values are hardcoded in `snowflake.yml`.

3. Verify the app is accessible

### App Pages

| Page | File | Purpose |
|------|------|---------|
| Home | `views/overview.py` | KPI metrics — total, operational %, faulty count, neighbourhoods |
| Neighbourhood Overview | `views/1_infrastructure_overview.py` | Pydeck map — all lights color-coded by status, zone load overlay |
| Faulty Lights | `views/2_faulty_lights.py` | Fault inspector — map + table row selection → detail map + SI query |
| Analytics | `views/3_analytics.py` | Energy trends, neighbourhood comparison, seasonal maintenance patterns |
| Energy Forecast | `views/4_forecasting.py` | ML FORECAST predictions with confidence intervals |

> Navigation is defined in `home.py` via `st.navigation()`. Pages live in `app/views/` (not `app/pages/`) to prevent SiS auto-discovery from overriding the custom page titles.

### Verification

- Verify the STREAMLIT object exists:
  ```sql
  SHOW STREAMLITS IN SCHEMA {database}.{schema};
  ```
- Open the app URL and confirm it loads
- Test navigation between pages

## What we did

- ✅ Streamlit app deployed to Snowflake
- ✅ All 5 pages accessible
- ✅ App URL available for sharing

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 9` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~9 — (1 bash deploy + 1 SQL SHOW STREAMLITS + 1 SQL grant verify + 5 page navigations + 1 gate call without this skill) |
| **Step ICR** | **9** (9 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Mark COMPLETE

```bash
uv run gate --step step-9 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 10: Validate & Demo?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 10` for later resumption.
