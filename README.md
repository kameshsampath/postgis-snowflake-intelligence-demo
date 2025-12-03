# PostGIS + Snowflake Openflow + Snowflake ML Demo

## Street Lights Maintenance - Production-Ready Architecture

This demo showcases a production-ready architecture for managing smart city street lights, featuring PostGIS for operational spatial queries, Snowflake Openflow for CDC, and Snowflake ML for predictive maintenance.

> **DISCLAIMER**: This project uses entirely fictitious data for demonstration and educational purposes. All company names, supplier names, contact information, and other data are computer-generated and do not represent real entities.

---

## Quick Start

**See [QUICKSTART.md](QUICKSTART.md) for the complete setup guide.**

The quickstart covers:

1. Prerequisites and tool installation
2. Snowflake-managed PostgreSQL setup via Snowsight
3. Database initialization and data loading
4. Streamlit dashboard launch
5. Snowflake CDC configuration
6. Cortex Search and Analyst setup
7. ML Forecasting configuration

---

## Prerequisites

| Tool | Purpose | Installation |
|------|---------|--------------|
| **Snowflake Account** | Database, CDC, ML, and AI capabilities | [Sign up](https://signup.snowflake.com/) |
| **Snowflake CLI** | Execute SQL and manage resources | [Docs](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) |
| **psql** | PostgreSQL command-line client | `brew install libpq` (macOS) |
| **Python 3.12+** | Dashboard and data generation | [python.org](https://www.python.org/) |
| **uv** | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

> **Tip**: Use [~/.pgpass](https://www.postgresql.org/docs/current/libpq-pgpass.html) for secure Snowflake PostgreSQL credentials:
> ```
> <host>:5432:postgres:snowflake_admin:<password>
> ```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Snowflake-Managed PostgreSQL                        │
│                                                                             │
│  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐  │
│  │   Base Tables    │      │   Enrichment     │      │   Enriched       │  │
│  │                  │──────│   Tables         │──────│   Views          │  │
│  │ • street_lights  │      │ • weather        │      │                  │  │
│  │ • neighborhoods  │      │ • demographics   │      │ street_lights_   │  │
│  │ • maintenance_   │      │ • power_grid     │      │ _enriched        │  │
│  │   requests       │      └──────────────────┘      └────────┬─────────┘  │
│  │ • suppliers      │                                         │            │
│  └──────────────────┘                                         │            │
│           │                                                   │            │
│           │ Publication: streetlights_publication             │            │
└───────────┼───────────────────────────────────────────────────┼────────────┘
            │                                                   │
            │ Snowflake Openflow CDC                            │
            ▼                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Snowflake                                      │
│                                                                             │
│  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐  │
│  │   Raw Tables     │      │   Cortex Search  │      │   ML Forecasting │  │
│  │   (CDC Sync)     │──────│                  │      │                  │  │
│  │                  │      │ MAINTENANCE_     │      │ BULB_FAILURE_    │  │
│  │ Real-time sync   │      │ SEARCH           │      │ FORECASTER       │  │
│  │ from PostgreSQL  │      │                  │      │                  │  │
│  └──────────────────┘      └──────────────────┘      └──────────────────┘  │
│                                    │                          │            │
│                                    ▼                          ▼            │
│                            ┌──────────────────────────────────────────┐    │
│                            │        Snowflake Intelligence            │    │
│                            │                                          │    │
│                            │ • Cortex Search (semantic queries)       │    │
│                            │ • Cortex Analyst (analytics via YAML)    │    │
│                            │ • ML Predictions (30/90-day forecasts)   │    │
│                            └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────┐
│   Streamlit Dashboard    │
│                          │
│ • Interactive Maps       │
│ • Faulty Light Analysis  │
│ • Predictive Maintenance │
│ • Supplier Coverage      │
│ • Live Demo Controls     │
└──────────────────────────┘
```

---

## Project Structure

```
postgis-nifi-pipeline/
├── QUICKSTART.md              # Setup guide (start here!)
├── DEMO_SCRIPT.md             # Detailed demo walkthrough
├── pyproject.toml             # Python project configuration
│
├── init/                      # PostgreSQL initialization scripts
│   ├── 00_init_all.sql        # Master init script (run this)
│   ├── 01_enable_extensions.sql
│   ├── 02_enable_wal.sql
│   ├── 03_create_base_tables.sql
│   ├── 04_create_enrichment_tables.sql
│   ├── 05_create_enriched_views.sql
│   ├── 06_create_indexes.sql
│   └── 07_create_publication.sql
│
├── data/                      # Data generation and loading
│   ├── load_data.sql          # Load full dataset
│   ├── load_sample_data.sql   # Load sample dataset
│   ├── generate_all.py        # Generate full datasets (uv run generate-all-data)
│   ├── generate_sample.py     # Generate sample datasets (uv run generate-sample)
│   └── *.csv                  # Generated data files
│
├── dashboard/                 # Streamlit dashboard
│   ├── app.py                 # Main dashboard application
│   ├── run.py                 # Dashboard runner (uv run dashboard)
│   └── requirements.txt
│
├── snowflake/                 # Snowflake SQL scripts
│   ├── 07_cortex_search_setup.sql
│   ├── 08_cortex_analyst_setup.sql
│   ├── 09_ml_training_view.sql
│   ├── 10_ml_model_training.sql
│   ├── 11_ml_queries.sql
│   ├── streetlights_semantic_model.yaml
│   └── SNOWFLAKE_INTELLIGENCE_QUESTIONS.md
│
├── queries/postgis/           # PostGIS query examples
│   └── *.sql
│
└── work/                      # Implementation notes
    ├── snowflake_ml_guide.md
    └── *.md
```

---

## Database Schema

### Base Tables

| Table | Description |
|-------|-------------|
| `neighborhoods` | Geographic boundaries (polygons) with population data |
| `street_lights` | Operational data (location, status, installation date) |
| `maintenance_requests` | Historical maintenance records |
| `suppliers` | Equipment suppliers with service coverage |

### Enrichment Tables

| Table | Description |
|-------|-------------|
| `weather_enrichment` | Seasonal patterns with failure risk scores |
| `demographics_enrichment` | Neighborhood characteristics |
| `power_grid_enrichment` | Electrical grid data per light |

### Key View

- **`street_lights_enriched`**: Combines lights with all enrichment data (main CDC view)

See [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md) for complete schema documentation.

---

## Data Generation

Generate data using `uv run` commands:

```bash
# Install dependencies first
uv sync

# Generate full dataset (5,000 lights, 50 neighborhoods, 1,500 maintenance requests)
uv run generate-all-data

# Generate sample dataset for quick testing (10 lights, 5 neighborhoods)
uv run generate-sample
```

### Dataset Sizes

| Entity | Full Dataset | Sample Dataset |
|--------|--------------|----------------|
| Street lights | 5,000 | 10 |
| Neighborhoods | 50 | 5 |
| Suppliers | 25 | 3 |
| Maintenance requests | 1,500 | 10 |
| Enrichment records | 15,000 | 30 |

**Status distribution**: 85% operational, 10% maintenance required, 5% faulty

---

## Key Features

### PostGIS Spatial Operations

- Sub-second spatial queries (ST_Within, ST_DWithin, ST_Distance)
- GIST indexes for performance
- Point-in-polygon, proximity search, nearest neighbor
- Geography type for accurate meter-based distances

### Snowflake Openflow CDC

- Real-time change data capture from PostgreSQL
- Automatic schema synchronization
- ~1-5 second sync latency
- Setup guide: [Getting Started with Openflow PostgreSQL CDC](https://quickstarts.snowflake.com/guide/getting-started-with-openflow-postgresql-cdc/)

### Snowflake Intelligence

- **Cortex Search**: Semantic search on maintenance descriptions
- **Cortex Analyst**: Structured analytics via YAML semantic model
- Natural language queries for both search and analytics
- Setup guide: [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)

**Recommended Orchestration Instructions:**

```
- Whenever possible try to visualize the data graphically
- *CRITICAL*: When you get WKT format for location, try parsing it as 
  geometric location as latitude and longitude. Don't show SQL parsing errors.
- *CRITICAL*: Wherever possible provide Google Map URL with latitude and 
  longitude that were parsed from the SQL result in the response
```

> [WKT (Well-Known Text)](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) is a standard format for geometry like `POINT(77.5946 12.9716)`.

### ML Forecasting

- Time-series forecasting for bulb failures
- 30/90-day predictions with confidence intervals
- Budget planning with cost breakdowns (INR)
- Seasonal risk analysis

---

## Sample Queries

### PostgreSQL: Find faulty lights within 1km

```sql
SELECT light_id, status,
       ST_Distance(location::geography, 
                   ST_MakePoint(77.5946, 12.9716)::geography) as distance_m
FROM streetlights.street_lights
WHERE status = 'faulty'
  AND ST_DWithin(location::geography, 
                 ST_MakePoint(77.5946, 12.9716)::geography, 1000);
```

### Snowflake: Semantic search for issues

```sql
SELECT * FROM TABLE(
  ANALYTICS.MAINTENANCE_SEARCH!SEARCH(
    query => 'flickering light electrical problem',
    columns => ['SEARCH_DESCRIPTION'],
    limit => 10
  )
);
```

### Snowflake: Weekly forecast with budget

```sql
SELECT
    DATE_TRUNC('week', FORECAST_DATE)::DATE AS WEEK_START,
    SUM(PREDICTED_FAILURES) AS TOTAL_FAILURES,
    SUM(PREDICTED_FAILURES) * 1650 AS TOTAL_BUDGET_INR
FROM ANALYTICS.BULB_REPLACEMENT_SCHEDULE
GROUP BY DATE_TRUNC('week', FORECAST_DATE)
ORDER BY WEEK_START;
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Complete setup guide |
| [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md) | Database schema, tables, views, and query patterns |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Detailed demo walkthrough |
| [snowflake/SNOWFLAKE_INTELLIGENCE_QUESTIONS.md](snowflake/SNOWFLAKE_INTELLIGENCE_QUESTIONS.md) | Sample Cortex queries |
| [work/snowflake_ml_guide.md](work/snowflake_ml_guide.md) | ML forecasting details |

---

## Troubleshooting

### psql connection fails

```bash
# Verify environment variables
source .env
echo $PGHOST $PGPORT $PGDATABASE

# Test connection
psql -c "SELECT 1;"
```

### Snow CLI issues

```bash
# Check version
snow --version

# Test connection
snow connection test

# List connections
snow connection list
```

### Dashboard won't start

```bash
# Ensure dependencies installed
uv sync

# Check .env file exists with correct values
cat .env

# Run dashboard
uv run dashboard
```

### CDC not syncing

```bash
# Verify publication exists
psql -c "SELECT * FROM pg_publication;"

# Check replication slot
psql -c "SELECT * FROM pg_replication_slots;"
```

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Kamesh Sampath

---

## Acknowledgments

- PostGIS for spatial database capabilities
- Snowflake Openflow for CDC capabilities
- Snowflake for AI Data Cloud
- Streamlit for rapid dashboard development

---

**Built for the spatial data community**
