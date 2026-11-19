# Databricks Implementation — Lakebase + Genie

Databricks perspective of the PostGIS Data Intelligence Demo. For the full
step-by-step walkthrough (from a fresh workspace to a running demo), see
[`docs/databricks-guide.md`](../docs/databricks-guide.md).

## What lives here

```
databricks/
├── databricks.yml        # Asset Bundle (DAB) — catalog, schema, SQL warehouse, jobs, Genie space, app
├── app/                  # Streamlit app deployed as a Databricks App (source_code_path: ./app)
│   ├── main.py
│   └── requirements.txt
└── sql/
    ├── 00_lakebase_schema.sql  # psql vs Lakebase: PostGIS + streetlights tables (plain Postgres DDL)
    ├── 01_setup.sql            # bundle job: curated views over the Lakebase UC catalog
    ├── 02_genie_space.sql      # bundle job: verified-question views for the Genie space
    ├── 03_vector_search.sql    # bundle job: Delta source table for the AI Search index
    ├── 04_forecast.sql         # bundle job: ai_forecast() energy forecast tables
    └── 05_app.sql              # bundle job: app KPI/map views
```

## Component mapping (Snowflake → Databricks)

| Snowflake | Databricks |
|---|---|
| Snowflake Postgres + pg_lake | **Lakebase** (managed Postgres; `sql/00_lakebase_schema.sql`) |
| CLD zero-pipeline sync | `databricks postgres create-catalog` — register the Lakebase DB in UC |
| Semantic View | curated views (`01_setup.sql`) + **Genie space** |
| Cortex Search | **AI Search** (Vector Search) index on `maintenance_records_text` |
| Intelligence Agent | **Genie** space chat |
| ML FORECAST | `ai_forecast()` (`04_forecast.sql`) |
| Streamlit in Snowflake | Databricks Apps (`app/`) |

## Quick commands

```bash
# from the repo root
task dbx:validate    # databricks bundle validate -t dev
databricks bundle deploy -t dev        # from databricks/
task dbx:run-all     # runs setup -> genie_views -> vector_search -> forecast -> app
task dbx:destroy     # tears down bundle resources
```

The Lakebase project/branch/endpoint creation and data load happen with psql
against the Lakebase endpoint — see the guide.
