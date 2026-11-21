# PostGIS Data Intelligence Demo

A demonstration of PostGIS data intelligence across Snowflake and Databricks platforms.

> **Note**
> This project began as a Snowflake-only implementation (`postgis-snowflake-intelligence-demo`) and was later expanded to support Databricks, prompting the rename to `postgis-data-intelligence-demo`. The Snowflake path remains the primary, production-tested implementation; the Databricks implementation follows the same patterns and architecture.

Reusable patterns behind this demo (problem, solution, product mapping): [docs/patterns.md](docs/patterns.md).

## ⚠️ Demo Data Disclaimer

All data in this demo — including street light locations, maintenance records,
sensor readings, energy consumption figures, and operational statuses — is
**entirely synthetic and computer-generated** for demonstration and educational
purposes only.

Geographic coordinates are placed within real map areas using the user's
detected or specified city as a reference point. **These coordinates do not
represent actual street light infrastructure.** Map links are provided solely
to demonstrate location-aware query capabilities. Any resemblance to actual
streetlight locations, infrastructure, or operational data is coincidental.

This demo is provided "as is" for educational purposes only and is not intended
to reflect the actual condition of any city's infrastructure. No reliance should
be placed on any data shown for operational, commercial, safety, or any other
real-world decisions.

## Architecture

Both platforms follow the same architecture pattern:

| Component | Snowflake | Databricks |
|-----------|-----------|------------|
| Managed PostgreSQL | Snowflake Postgres + pg_lake | Lakebase |
| Table format | Iceberg | Iceberg |
| Zero-pipeline sync | Catalog-Linked Database | Unity Catalog Auto-Sync |
| Semantic layer | Semantic View | Genie |
| Vector search | Cortex Search | Vector Search |
| AI agent | Intelligence Agent | Genie |
| Forecasting | ML FORECAST | AI_FORECAST |
| Visualization | Streamlit in Snowflake | Databricks Apps |

## Prerequisites

### Tools

Install mise for tool management:

```bash
curl https://mise.run | sh
```

Then install the project tools:

```bash
mise install
```

### Additional manual installations

> **Warning**
> The following tools are not in the mise registry and must be installed manually:

- **Snowflake CLI**: `brew install snowflake-cli` (macOS) or see [Snowflake docs](https://docs.snowflake.com/en/user-guide/snowsql-install-config)
- **PostgreSQL CLI**: `brew install libpq` (macOS) or `sudo apt-get install postgresql-client` (Ubuntu)

After installing, run:

```bash
mise trust
```

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/kameshsampath/postgis-data-intelligence-demo.git
cd postgis-data-intelligence-demo
```

### 2. Choose your platform

Copy the environment template and pick a platform (`snowflake`, `databricks`, or `both`):

```bash
cp .env.example .env   # then edit .env — never commit it
```

- Snowflake path → see [Snowflake Implementation Guide](docs/snowflake-guide.md)
- Databricks path → see [Databricks Implementation Guide](docs/databricks-guide.md)

### 3. Install dependencies

```bash
mise install
uv sync
```

## Quickstart

### Snowflake

```bash
# Generate synthetic data, apply PostGIS schema, load CSVs
mise run generate   # Portland, 5000 lights (see .mise.toml)
task pg:schema
task pg:load

# Set up Snowflake infrastructure
task sf:setup
task sf:semantic-view
task sf:search
task sf:agent
task sf:forecast
```

Or run the guided flow with Cortex Code: `$streetlights-demo infra` then `$streetlights-demo app`.

### Databricks

```bash
# Generate synthetic data
mise run generate

# Deploy the Databricks bundle (catalog, schema, SQL warehouse, jobs, Genie, app)
# and run the setup jobs — the full e2e walkthrough (Lakebase project, data load,
# UC registration, Genie space) is in docs/databricks-guide.md
task dbx:deploy
task dbx:run-all
```

See [docs/databricks-guide.md](docs/databricks-guide.md) for the complete step-by-step.

## Project Structure

```
.
├── .mise.toml                    # Tool and environment configuration
├── .env.example                  # Environment template (Snowflake + Databricks keys)
├── init/                         # PostgreSQL DDL (shared)
│   ├── 01_enable_extensions.sql
│   └── 02_create_iceberg_tables.sql
├── snowflake/                     # Snowflake SQL scripts
│   ├── 01_setup.sql
│   ├── 02_semantic_view.sql
│   ├── 03_cortex_search.sql
│   ├── 04_intelligence_agent.sql
│   └── 05_ml_forecast.sql
├── databricks/                    # Databricks implementation
│   ├── sql/                      # SQL scripts
│   │   ├── 01_setup.sql
│   │   ├── 02_genie_space.sql
│   │   ├── 03_vector_search.sql
│   │   ├── 04_forecast.sql
│   │   └── 05_app.sql
│   ├── databricks.yml            # Asset bundle configuration
│   └── README.md                 # Databricks-specific documentation
├── app/                           # Streamlit application
├── scripts/                       # Python scripts
│   ├── generate_all.py            # Data generation
│   ├── gate.py                    # Gate checks
│   ├── gates/                     # Modular gate checks
│   │   ├── __init__.py
│   │   ├── base_gates.py
│   │   ├── snowflake_gates.py
│   │   └── databricks_gates.py
│   ├── idd_metrics.py            # IDD metrics collection
│   └── platform.py               # Platform detection
├── docs/                          # Documentation
│   ├── snowflake-guide.md         # Snowflake implementation guide
│   └── databricks-guide.md        # Databricks implementation guide
├── .cortex/                       # Cortex Code skills (autoload)
│   └── skills/
│       ├── streetlights-demo/            # Guided demo skill (canonical)
│       ├── streetlights-demo-snowflake   # alias -> ../../skills/streetlights-demo-snowflake
│       └── streetlights-demo-databricks  # alias -> ../../skills/streetlights-demo-databricks
└── skills/                        # Neutral skill home (symlinks into .cortex/skills)
    ├── streetlights-demo -> ../.cortex/skills/streetlights-demo
    ├── streetlights-demo-snowflake -> streetlights-demo
    └── streetlights-demo-databricks -> streetlights-demo
├── pyproject.toml                 # Python project configuration
└── README.md                      # This file
```

## Documentation

- [Snowflake Implementation Guide](docs/snowflake-guide.md)
- [Databricks Implementation Guide](docs/databricks-guide.md)
- [Patterns discovered while building this demo](docs/patterns.md)

## Skills

This project includes Cortex Code skills for guided execution. See `.cortex/skills/streetlights-demo/` for:

- `$streetlights-demo` - Main demo orchestrator
- `$streetlights-demo-snowflake` - Snowflake-specific routing
- `$streetlights-demo-databricks` - Databricks-specific routing

> **Tip**
> Use `mise trust` to allow mise to manage tools in this project directory.
> Personal tweaks belong in `.mise.local.toml` (gitignored; copy
> `.mise.local.toml.example`), and secrets/connection values in `.env`
> (gitignored, auto-loaded by mise) — the committed `.mise.toml` stays a safe
> base template.

## License

Apache License 2.0. Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>. See
[LICENSE](LICENSE), [NOTICE](NOTICE), and [CITATION.cff](CITATION.cff).

This is an independent, personal open-source project. It was initially developed by
the author while employed at Snowflake, but it has been open source under the Apache
License from day one and contains no employer intellectual property. It is not
affiliated with, sponsored, or endorsed by Snowflake Inc.
