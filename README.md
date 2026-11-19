# PostGIS Data Intelligence Demo

A demonstration of PostGIS data intelligence across Snowflake and Databricks platforms.

> **Note**
> This project began as a Snowflake-only implementation (`postgis-snowflake-intelligence-demo`) and was later expanded to support Databricks, prompting the rename to `postgis-data-intelligence-demo`. The Snowflake path remains the primary, production-tested implementation; the Databricks implementation follows the same patterns and architecture.

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

Copy the appropriate environment template for your platform:

```bash
# For Snowflake
cp .env.snowflake .env

# For Databricks
cp .env.databricks .env
```

Edit `.env` with your settings. Never commit this file to git.

### 3. Install dependencies

```bash
mise install
uv sync
```

## Quickstart

### Snowflake

```bash
# Generate synthetic data
uv run generate --city "Portland" --prefix "DEMO"

# Create PostGIS schema and tables
psql -f init/01_enable_extensions.sql
psql -f init/02_create_iceberg_tables.sql

# Load data
for table in street_lights maintenance_records energy_consumption light_sensors weather_enrichment demographics power_grid_zones; do
  psql -c "\\copy streetlights.$table FROM 'data/${table}.csv' CSV HEADER"
done

# Set up Snowflake infrastructure
snow sql -f snowflake/01_setup.sql
snow sql -f snowflake/02_semantic_view.sql
snow sql -f snowflake/03_cortex_search.sql
snow sql -f snowflake/04_intelligence_agent.sql
snow sql -f snowflake/05_ml_forecast.sql
snow sql -f snowflake/06_streamlit.sql
```

### Databricks

```bash
# Generate synthetic data
uv run generate --city "Austin" --prefix "DEMO"

# Create PostGIS schema and tables
psql -f init/01_enable_extensions.sql
psql -f init/02_create_iceberg_tables.sql

# Load data
for table in street_lights maintenance_records energy_consumption light_sensors weather_enrichment demographics power_grid_zones; do
  psql -c "\\copy streetlights.$table FROM 'data/${table}.csv' CSV HEADER"
done

# Set up Databricks infrastructure
databricks sql -f databricks/sql/01_setup.sql
databricks sql -f databricks/sql/02_genie_space.sql
databricks sql -f databricks/sql/03_vector_search.sql
databricks sql -f databricks/sql/04_forecast.sql
databricks sql -f databricks/sql/05_app.sql

# Deploy bundle
databricks bundle deploy -t dev
```

## Project Structure

```
.
├── .mise.toml                    # Tool and environment configuration
├── .env.snowflake                # Snowflake environment template
├── .env.databricks               # Databricks environment template
├── .env.example                  # Generic environment template
├── init/                         # PostgreSQL DDL (shared)
│   ├── 01_enable_extensions.sql
│   └── 02_create_iceberg_tables.sql
├── snowflake/                     # Snowflake SQL scripts
│   ├── 01_setup.sql
│   ├── 02_semantic_view.sql
│   ├── 03_cortex_search.sql
│   ├── 04_intelligence_agent.sql
│   ├── 05_ml_forecast.sql
│   └── 06_streamlit.sql
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
│   ├── databricks-guide.md        # Databricks implementation guide
│   └── plans/                     # Planning documents
├── .cortex/                       # Cortex Code skills
│   └── skills/
│       └── streetlights-demo/     # Guided demo skills
├── pyproject.toml                 # Python project configuration
└── README.md                      # This file
```

## Documentation

- [Snowflake Implementation Guide](docs/snowflake-guide.md)
- [Databricks Implementation Guide](docs/databricks-guide.md)

## Skills

This project includes Cortex Code skills for guided execution. See `.cortex/skills/streetlights-demo/` for:

- `$streetlights-demo` - Main demo orchestrator
- `$streetlights-demo-snowflake` - Snowflake-specific routing
- `$streetlights-demo-databricks` - Databricks-specific routing

> **Tip**
> Use `mise trust` to allow mise to manage tools in this project directory.

## License

Apache-2.0
