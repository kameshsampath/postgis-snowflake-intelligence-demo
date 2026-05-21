# Streetlights Intelligence Demo

**Snowflake Postgres + pg_lake + Cortex AI**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A complete demo showcasing how Snowflake Postgres with pg_lake Iceberg tables connects
natively to Snowflake's AI stack — no CDC pipeline, no ETL, no data movement.

## What This Demonstrates

| Component | Purpose |
|-----------|---------|
| **Snowflake Postgres** | Managed PostgreSQL with pg_lake extension |
| **pg_lake Iceberg tables** | PostgreSQL tables stored as Apache Iceberg |
| **CLD (Catalog-Linked Database)** | Zero-pipeline sync — Snowflake reads PG Iceberg directly |
| **Semantic View** | SQL-native semantic layer for natural language analytics |
| **Cortex Search** | Semantic text search on maintenance records |
| **Intelligence Agent** | NL interface combining structured + unstructured access |
| **ML FORECAST** | Time-series prediction for energy consumption |
| **Streamlit in Snowflake** | Multi-page dashboard for visualization |

## Architecture

```
Snowflake Postgres (pg_lake)          Snowflake
┌──────────────────────────┐          ┌─────────────────────────────────┐
│ Iceberg tables (ALL 7)   │  Shared  │  Catalog Integration (CLD)      │
│ (managed storage ONLY)   │──Iceberg─│         ↓                       │
│                          │          │  Semantic View + Cortex Search  │
│ Location-aware data:     │          │  + ML FORECAST models           │
│ user's city or override  │          │  + Intelligence Agent           │
│                          │          │  (Semantic View + Search)       │
│ Spatial: lat/lng FLOAT   │          │                                 │
│ (no PostGIS GEOMETRY     │          │  + SiS Multi-Page App           │
│  in Iceberg tables)      │          │                                 │
└──────────────────────────┘          └─────────────────────────────────┘
```

**Key insight**: No CDC/OpenFlow/Debezium pipeline between PostgreSQL and Snowflake.
pg_lake stores data as Iceberg; CLD reads the same Iceberg metadata. Zero data movement.

## Prerequisites

| Tool | Purpose | Installation |
|------|---------|--------------|
| Snowflake Account | Must have Snowflake Postgres enabled | Contact account admin |
| Snowflake CLI (`snow`) | Manage resources and run SQL | [Docs](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) |
| Cortex Code (`cortex`) | Guided demo workflow | [Docs](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) |
| `uv` | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `psql` | PostgreSQL client | `brew install libpq` (macOS) |
| `task` | Task runner (optional) | `brew install go-task` |

### Account Requirements

The following account parameters must be enabled:
- `ENABLE_SNOWFLAKE_POSTGRES`
- `ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME`

## Quick Start (Cortex Code)

The recommended path uses Cortex Code's guided workflow:

```bash
# 1. Initialize configuration
$streetlights-demo setup

# 2. Generate location-aware synthetic data
$streetlights-demo step 1

# 3. Create Snowflake Postgres instance
$streetlights-demo step 2

# 4. Create schema and load data
$streetlights-demo step 3

# 5. Create CLD (Catalog-Linked Database)
$streetlights-demo step 4

# 6. Create Semantic View
$streetlights-demo step 5

# 7. Create Cortex Search service
$streetlights-demo step 6

# 8. Create Intelligence Agent
$streetlights-demo step 7

# 9. Train ML Forecast model
$streetlights-demo step 8

# 10. Deploy Streamlit app
$streetlights-demo step 9

# 11. Validate everything works
$streetlights-demo step 10
```

Each step includes pre-flight checks, verification gates, and user confirmations
for billable actions.

## Manual Path (Taskfile)

For users not using Cortex Code:

```bash
# Install dependencies
uv sync

# Generate data for Portland (or your city)
task generate -- --city "Portland" --lat 45.5152 --lng -122.6784 --count 500

# Apply PG schema (requires psql connection to your instance)
task pg:schema

# Load data
task pg:load

# Run Snowflake SQL scripts
task sf:setup
task sf:semantic-view
task sf:search
task sf:agent
task sf:forecast
```

## Directory Structure

```
.
├── .cortex/skills/streetlights-demo/   # CoCo skill (guided workflow)
│   ├── SKILL.md                        # Coordinator + router
│   ├── steps/                          # Step sub-skills (setup, 1-10)
│   ├── cleanup/                        # Teardown skill
│   └── references/                     # Concepts + PostGIS contrast
├── app/                                # Streamlit in Snowflake app
│   ├── Home.py                         # Entry point
│   ├── pages/                          # Multi-page views
│   └── environment.yml                 # SiS dependencies
├── data/                               # Generated CSVs (gitignored)
├── init/                               # PostgreSQL DDL scripts
│   ├── 01_enable_extensions.sql        # pg_lake + PostGIS extensions
│   └── 07_create_iceberg_tables.sql    # All 7 Iceberg tables
├── scripts/                            # CLI tools and gates
│   ├── gate.py                         # Per-step verification checks
│   └── sanity_gate.py                  # End-to-end smoke test
├── snowflake/                          # Snowflake DDL scripts
│   ├── 01_setup.sql                    # Database + warehouse
│   ├── 02_semantic_view.sql            # Semantic View
│   ├── 03_cortex_search.sql            # Cortex Search service
│   ├── 04_intelligence_agent.sql       # Intelligence Agent
│   └── 05_ml_forecast.sql             # ML Forecast model
├── .streetlights-demo/                 # Local config (gitignored)
│   └── manifest.toml                   # Demo configuration
├── Taskfile.yml                        # Task automation
└── pyproject.toml                      # Python project config
```

## Key Concepts

- **pg_lake**: PostgreSQL extension for Iceberg table storage
- **CLD**: Catalog-Linked Database — Snowflake reads PG Iceberg metadata directly
- **Semantic View**: SQL-native semantic layer (replaces YAML models)
- **Cortex Search**: Managed text search service with semantic understanding
- **Intelligence Agent**: Natural language interface combining structured + unstructured data

See [`.cortex/skills/streetlights-demo/references/concepts.md`](.cortex/skills/streetlights-demo/references/concepts.md) for detailed explanations.

## Cleanup

```bash
# Guided teardown (drops all resources in reverse order)
$streetlights-demo cleanup
```

Or manually:
```bash
task cleanup
```

> **CAUTION**: This project uses entirely fictitious data for demonstration and
> educational purposes. All company names, supplier names, contact information,
> and other data are computer-generated and do not represent real entities.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

Copyright 2025 Kamesh Sampath
