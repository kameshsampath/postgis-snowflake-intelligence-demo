# Databricks Implementation — Lakebase + Genie

This directory contains the Databricks implementation of the PostGIS data intelligence demo,
providing equivalent functionality to the Snowflake implementation using Databricks Lakebase and Genie.

## Architecture Overview

The Databricks implementation provides equivalent functionality using native Databricks services:

| Snowflake Component | Databricks Equivalent |
|---|---|
| Snowflake Postgres + pg_lake | **Lakebase** (managed Postgres) |
| CLD zero-pipeline sync | **Lakebase ↔ Unity Catalog sync** |
| Semantic View | **Genie space** configuration |
| Cortex Search | **Vector Search** index |
| Intelligence Agent | **Genie** agent |
| ML FORECAST | **AI_FORECAST()** function |
| Streamlit in Snowflake | **Databricks Apps (Streamlit)** |

## Directory Structure

```
databricks/
├── README.md           # This file
├── databricks.yml      # Asset bundle configuration
├── sql/
│   ├── 01_setup.sql    # Catalog, schema, Lakebase→UC sync, curated views
│   ├── 02_genie_space.sql # Genie space configuration over UC schema
│   ├── 03_vector_search.sql # Vector Search index on maintenance text
│   ├── 04_forecast.sql # ML Forecast model using AI_FORECAST()
│   └── 05_app.sql      # Databricks App (Streamlit) configuration
└── .gitignore
```

## Prerequisites

- Databricks Workspace with Lakebase, Unity Catalog, Vector Search, Genie, and ML enabled
- Databricks CLI installed and configured
- Appropriate permissions for catalog/schema creation

## Configuration

Environment variables via Databricks CLI profile:
- `DATABRICKS_HOST` — Workspace URL
- `DATABRICKS_TOKEN` — Personal access token

See `.env.databricks` in project root for template.

## Asset Bundle Usage

This implementation uses **Databricks Asset Bundles** defined in `databricks.yml`:

```bash
# Validate bundle configuration
databricks bundle validate

# Deploy all resources to dev environment
databricks bundle deploy -t dev

# Deploy to production
databricks bundle deploy -t prod

# Check deployment status
databricks bundle status -t dev

# Destroy all resources
databricks bundle destroy -t dev

# Run a specific job
databricks bundle run -t dev -r job:setup_job
```

**Resources defined in bundle:**
- Unity Catalog + Schema
- Lakebase external location + credentials
- SQL Warehouse
- Vector Search endpoint + index
- Genie space + tools
- ML Forecast model
- Databricks App (Streamlit)
- Automation jobs
- Permissions

## Component Details

### sql/01_setup.sql
- Creates catalog and schema in Unity Catalog
- Configures Lakebase instance connection
- Sets up curated views matching Snowflake Semantic View structure

### sql/02_genie_space.sql
- Creates Genie space with appropriate permissions
- Configures semantic layer over curated views
- Defines query instructions for natural language understanding

### sql/03_vector_search.sql
- Creates Vector Search index on maintenance_records table
- Uses Databricks AI embeddings
- Enables semantic similarity search

### sql/04_forecast.sql
- Creates ML forecast model using AI_FORECAST()
- Configures time series analysis on energy_consumption

### sql/05_app.sql
- Creates Databricks App (Streamlit)
- Configures connection to Lakebase data
- Sets up multi-page dashboard structure

## Testing

Refer to `scripts/gate.py` for Databricks-specific gates:
- `lakebase_reachable` — Lakebase instance is accessible
- `uc_sync_healthy` — Unity Catalog sync is operational
- `genie_space_active` — Genie space responds to queries
- `vector_index_ready` — Vector Search index is built and queryable
- `forecast_ready` — ML forecast model is trained and available
- `app_deployed` — Databricks App is deployed and accessible

Run all Databricks gates:
```bash
uv run gate --platform databricks --all
```

## Cleanup

To remove all Databricks resources:

```bash
databricks bundle destroy -t dev
```

> **Warning**: This is destructive and cannot be undone. Backup important data first.

## Links

- [Databricks Documentation](https://docs.databricks.com)
- [Lakebase Documentation](https://docs.databricks.com/en/sql/language-manual/lakebase/index.html)
- [Genie Documentation](https://docs.databricks.com/en/genie/index.html)
- [Databricks CLI Documentation](https://docs.databricks.com/en/dev-tools/cli/index.html)
- [Asset Bundles Documentation](https://docs.databricks.com/en/dev-tools/bundles/index.html)
