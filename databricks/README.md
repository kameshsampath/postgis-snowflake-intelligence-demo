# Databricks Perspective — Lakebase + Genie

This directory contains the Databricks implementation of the PostGIS data intelligence demo,
mirroring the Snowflake path using Databricks Lakebase and Genie.

## Architecture Overview

The Databricks perspective replaces Snowflake components with equivalent Databricks services:

| Snowflake Component | Databricks Equivalent | Location |
|---|---|---|
| Snowflake Postgres + pg_lake | **Lakebase** (managed Postgres) | `init/` (reuse existing DDL) |
| CLD zero-pipeline sync | **Lakebase ↔ Unity Catalog sync** | Automatic |
| Semantic View | **Genie space** configuration | `sql/02_genie_space.sql` |
| Cortex Search | **Vector Search** index | `sql/03_vector_search.sql` |
| Intelligence Agent | **Genie** agent | `sql/04_genie_agent.sql` |
| ML FORECAST | **AI_FORECAST()** function | `sql/04_forecast.sql` |
| Streamlit in Snowflake | **Databricks Apps (Streamlit)** | `sql/05_app.sql` |

## Directory Structure

```
databricks/
├── README.md                      # This file
├── databricks.yml                 # Asset bundle configuration
├── sql/
│   ├── 01_setup.sql               # Catalog, schema, Lakebase→UC sync, curated views
│   ├── 02_genie_space.sql         # Genie space configuration over UC schema
│   ├── 03_vector_search.sql       # Vector Search index on maintenance text
│   ├── 04_forecast.sql            # ML Forecast model using AI_FORECAST()
│   └── 05_app.sql                 # Databricks App (Streamlit) configuration
└── .gitignore                    # Local development ignores
```

## Prerequisites

- Databricks Workspace with:
  - Lakebase enabled
  - Unity Catalog enabled
  - Vector Search enabled
  - Genie enabled
  - ML capabilities
- Databricks CLI installed and configured
- Appropriate permissions for catalog/schema creation

## Configuration

Environment variables (via Databricks CLI profile):
- `DATABRICKS_HOST` — Workspace URL
- `DATABRICKS_TOKEN` — Personal access token (or use CLI profile auth)

See `.env.example` in the project root for the expected variables.

## Usage

Use the Taskfile commands (mirrors Snowflake path):

```bash
# Setup catalog, schema, and Lakebase sync
task dbx:setup

# Configure Genie space
task dbx:genie-space

# Create Vector Search index
task dbx:vector-search

# Train forecast model
task dbx:forecast

# Deploy Databricks App
task dbx:app
```

Or use the Databricks CLI directly with the asset bundle:

```bash
# Deploy all resources
databricks bundle deploy -t dev

# Run all jobs
databricks bundle run -t dev
```

## Asset Bundle Structure

The `databricks.yml` file defines:
- Workspace resources (jobs, models, etc.)
- Target configurations for different environments
- Dependencies between resources

## Lakebase ↔ Unity Catalog Sync

Lakebase provides managed PostgreSQL instances that automatically sync with Unity Catalog.
This enables direct querying of PostgreSQL tables from Databricks SQL without data movement.

- PostgreSQL tables from `init/01_enable_extensions.sql` are reused
- Lakebase instance connects to the same PostgreSQL data
- Unity Catalog makes tables queryable in Databricks SQL

## Genie Space Configuration

Genie spaces provide natural language interfaces over structured and unstructured data:

- Curated views define the semantic layer
- Instructions guide query understanding
- Verified answers provide reference responses

See `sql/02_genie_space.sql` for the complete configuration.

## Vector Search Index

Creates a semantic index on maintenance record text for innovation and maintenance text search:

- Indexes maintenance descriptions, notes, and observations
- Uses Databricks AI embeddings
- Enables semantic similarity search

See `sql/03_vector_search.sql` for index creation.

## Forecast Model

Uses Databricks' `AI_FORECAST()` function for time-series prediction:

- Target: `energy_consumption` data
- Automated model selection and training
- Configurable forecast horizon

See `sql/04_forecast.sql` for model creation.

## Databricks App

Deploys a Streamlit application using Databricks Apps:

- Connects to Lakebase UC schema
- Reuses views from the semantic layer
- Provides interactive dashboard with spatial visualizations

See `sql/05_app.sql` for app configuration.

## Component Mapping Details

### 01_setup.sql
- Creates catalog and schema in Unity Catalog
- Configures Lakebase instance connection
- Sets up curated views matching Snowflake Semantic View structure
- Creates external location for PostgreSQL data access

### 02_genie_space.sql
- Creates Genie space with appropriate permissions
- Configures semantic layer over curated views
- Defines query instructions for natural language understanding
- Sets up verified answers for common queries

### 03_vector_search.sql
- Creates Vector Search endpoint
- Defines index on maintenance_records table
- Configures embedding model and dimensions
- Sets up query parameters

### 04_forecast.sql
- Creates ML forecast model using AI_FORECAST()
- Configures time series analysis on energy_consumption
- Sets up prediction schedule

### 05_app.sql
- Creates Databricks App (Streamlit)
- Configures connection to Lakebase data
- Sets up multi-page dashboard structure
- Configures permissions and sharing

## Testing

Refer to `scripts/gate.py` for Databricks-specific gates:
- `lakebase_reachable` — Lakebase instance is accessible
- `uc_sync_healthy` — Unity Catalog sync is operational
- `genie_space_active` — Genie space responds to queries
- `vector_index_ready` — Vector Search index is built and queryable
- `forecast_ready` — ML forecast model is trained and available
- `app_deployed` — Databricks App is deployed and accessible

## Cleanup

To remove all Databricks resources:

```bash
databricks bundle destroy -t dev
```

This will remove:
- Catalog and schema (if empty)
- Genie spaces
- Vector Search indexes
- ML models
- Databricks Apps

> **Warning**: This is destructive and cannot be undone. Backup important data first.
