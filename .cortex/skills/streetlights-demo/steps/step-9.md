---
name: streetlights-demo-step-9
description: Deploy multi-page Streamlit in Snowflake application
---

## Gate

```bash
uv run gate --step step-9 --prior-step step-8 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

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

1. Read manifest for database/warehouse names
2. Route to `$developing-with-streamlit-in-snowflake` to deploy:
   - Source directory: `app/`
   - Entry point: `app/Home.py`
   - Pages: `app/pages/`
   - Environment: `app/environment.yml`
   - Target: `{database}.{schema}.STREETLIGHTS_APP`
   - Warehouse: from manifest

3. Verify the app is accessible

### App Pages

| Page | Purpose |
|------|---------|
| Home | Overview dashboard with key metrics |
| Infrastructure Overview | Map view of all street lights |
| Maintenance Search | Cortex Search interface |
| Analytics | Charts and aggregations |
| Forecasting | ML predictions visualization |
| Ask Agent | Chat interface to Intelligence Agent |

### Verification

- Verify the STREAMLIT object exists:
  ```sql
  SHOW STREAMLITS IN SCHEMA {database}.{schema};
  ```
- Open the app URL and confirm it loads
- Test navigation between pages

## What we did

- ✅ Streamlit app deployed to Snowflake
- ✅ All 6 pages accessible
- ✅ App URL available for sharing

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 9` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~7 — (1 bash SiS deploy + 1 SQL SHOW STREAMLITS + 3 page tests + 2 gate calls without this skill) |
| **Step ICR** | **7** (7 ops replaced by 1 invocation) |

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
