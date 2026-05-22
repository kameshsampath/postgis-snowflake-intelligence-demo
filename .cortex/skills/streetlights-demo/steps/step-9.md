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

# Step 9: Deploy SiS App

## What we'll do

Deploy the multi-page Streamlit in Snowflake (SiS) application that provides a visual dashboard for the streetlight data, including maps, charts, search, and an agent chat interface.

- Deploy app source from `app/` directory
- Configure warehouse and database references
- Verify the app loads and all pages work

## Dry-Run

Show the execution plan to the user:
```bash
uv run gate --step step-9 --action dry-run
```
Present the output, then ask user to proceed.

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 9"
- Question: "Ready to deploy the Streamlit dashboard app?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

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
