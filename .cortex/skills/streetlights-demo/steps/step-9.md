---
name: streetlights-demo-step-9
description: Deploy multi-page Streamlit in Snowflake application
---

# Step 9: Deploy SiS App

## Prerequisites

- All Snowflake objects created (Steps 5-8 complete)
- App source exists in `app/` directory

## Steps

1. Read manifest for database/warehouse names
2. Route to `$developing-with-streamlit-in-snowflake` to deploy:
   - Source directory: `app/`
   - Entry point: `app/Home.py`
   - Pages: `app/pages/`
   - Environment: `app/environment.yml`
   - Target: `{database}.{schema}.STREETLIGHTS_APP`
   - Warehouse: from manifest

3. Verify the app is accessible

## App Pages

| Page | Purpose |
|------|---------|
| Home | Overview dashboard with key metrics |
| Infrastructure Overview | Map view of all street lights |
| Maintenance Search | Cortex Search interface |
| Analytics | Charts and aggregations |
| Forecasting | ML predictions visualization |
| Ask Agent | Chat interface to Intelligence Agent |

## Verification

- Verify the STREAMLIT object exists:
  ```sql
  SHOW STREAMLITS IN SCHEMA {database}.{schema};
  ```
- Open the app URL and confirm it loads
- Test navigation between pages
