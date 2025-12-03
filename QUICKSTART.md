# Quick Start Guide

Get the Street Lights Maintenance Demo running with Snowflake-managed PostgreSQL, CDC, Cortex Intelligence, and ML Forecasting.

---

## Prerequisites

Before starting, ensure you have the following installed and configured:

### Required Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| **Snowflake Account** | Snowflake with Openflow PostgreSQL access | [Sign up](https://signup.snowflake.com/) |
| **Snowflake CLI** | Execute SQL and manage Snowflake resources | [Installation Guide](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) |
| **psql** | PostgreSQL command-line client | macOS: `brew install libpq` / Linux: `apt install postgresql-client` |
| **Python 3.12+** | Data generation and dashboard | [python.org](https://www.python.org/downloads/) |
| **uv** | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### Verify Installations

```bash
# Snowflake CLI
snow --version

# PostgreSQL client
psql --version

# Python
python3 --version

# uv
uv --version
```

### Snowflake CLI Configuration

Ensure your Snowflake CLI is configured:

```bash
# Test connection
snow connection test

# If not configured, add a connection
snow connection add
```

---

## Step 1: Setup Snowflake-Managed PostgreSQL

Deploy a PostgreSQL instance via Snowflake Openflow in Snowsight.

### 1.1 Deploy PostgreSQL via Snowsight

Follow the official guide: [Getting Started with Openflow Snowflake Deployments](https://www.snowflake.com/en/developers/guides/getting-started-with-openflow-spcs/)

**Key steps:**

1. Open **Snowsight** and navigate to **Data > Databases**
2. Click **+ Database** > **From Openflow PostgreSQL**
3. Configure the deployment settings
4. Wait for deployment to complete

### 1.2 Get Connection Details

After deployment, retrieve your PostgreSQL connection details from Snowsight:

- **Host**: `<your-instance>.snowflakecomputing.com`
- **Port**: `5432`
- **Database**: `postgres`
- **Username**: `snowflake_admin`
- **Password**: (from Snowsight)

### 1.3 Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your connection details
# Update: PGHOST, PGPORT, PGDATABASE, PGUSER (snowflake_admin), PGPASSWORD
```

**Tip**: Use [~/.pgpass](https://www.postgresql.org/docs/current/libpq-pgpass.html) for secure password storage:

```bash
# Add entry to ~/.pgpass (create if doesn't exist)
echo "<your-host>:5432:postgres:snowflake_admin:<your-password>" >> ~/.pgpass
chmod 600 ~/.pgpass
```

**Tip**: Use [direnv](https://direnv.net/) for automatic environment loading:

```bash
echo "dotenv" > .envrc
direnv allow
```

---

## Step 2: Initialize Database and Load Data

### 2.1 Install Dependencies

```bash
uv sync
```

### 2.2 Initialize Database Schema

Run the master initialization script to create all database objects:

```bash
source .env
psql -f init/00_init_all.sql
```

**What this creates:**

- PostGIS and uuid-ossp extensions
- WAL configuration for CDC
- Base tables (neighborhoods, street_lights, maintenance_requests, suppliers)
- Enrichment tables (weather, demographics, power grid)
- Enriched views and indexes
- Publication for Snowflake CDC

**Expected output:**

```
========================================================
Database Initialization Complete!
========================================================
```

### 2.3 Generate Data (Optional)

If you need to regenerate the data files:

```bash
# Generate full dataset (5,000 lights, 50 neighborhoods, 1,500 maintenance requests)
uv run generate-all-data

# Or generate small sample dataset for quick testing (10 lights, 5 neighborhoods)
uv run generate-sample
```

### 2.4 Load Data

```bash
# Load full dataset
psql -f data/load_data.sql

# Or load sample dataset for quick testing
psql -f data/load_sample_data.sql
```

**Expected output:**

```
============================================
Data loading complete!
============================================
```

### 2.5 Verify Data

```bash
psql -c "
SELECT 
  (SELECT COUNT(*) FROM streetlights.neighborhoods) AS neighborhoods,
  (SELECT COUNT(*) FROM streetlights.street_lights) AS street_lights,
  (SELECT COUNT(*) FROM streetlights.suppliers) AS suppliers,
  (SELECT COUNT(*) FROM streetlights.maintenance_requests) AS maintenance_requests;
"
```

**Expected result:**

| neighborhoods | street_lights | suppliers | maintenance_requests |
|---------------|---------------|-----------|----------------------|
| 50            | 5000          | 25        | 500                  |

Test the enriched view:

```bash
psql -c "SELECT light_id, status, neighborhood_name, season, failure_risk_score 
FROM streetlights.street_lights_enriched LIMIT 5;"
```

---

## Step 3: Launch Streamlit Dashboard

### 3.1 Run Dashboard

```bash
uv run dashboard
```

### 3.2 Access Dashboard

Open your browser to: **http://localhost:8501**

**Dashboard Pages:**

| Page | Description |
|------|-------------|
| **Neighborhood Overview** | Interactive map with all layers |
| **Faulty Lights Analysis** | View faulty lights with nearest suppliers |
| **Predictive Maintenance** | ML predictions and timeline |
| **Supplier Coverage** | Service area analysis |
| **Live Demo Controls** | Simulate failures in real-time |

---

## Step 4: Configure Snowflake CDC (Openflow)

Set up real-time Change Data Capture from PostgreSQL to Snowflake.

**Reference**: [Getting Started with Openflow PostgreSQL CDC](https://quickstarts.snowflake.com/guide/getting-started-with-openflow-postgresql-cdc/)

### 4.1 Verify PostgreSQL is Ready for CDC

```bash
psql -c "
SELECT
    current_setting('wal_level') AS wal_level,
    current_setting('max_replication_slots') AS max_replication_slots,
    (SELECT count(*) FROM pg_publication) AS publication_count;
"
```

**Expected:**

| wal_level | max_replication_slots | publication_count |
|-----------|-----------------------|-------------------|
| logical   | 10                    | 1                 |

### 4.2 Verify Publication

```bash
psql -c "SELECT * FROM pg_publication_tables WHERE pubname = 'streetlights_publication';"
```

### 4.3 Configure CDC in Snowsight

1. Open **Snowsight** > **Data** > **Databases**
2. Select your target database (e.g., `STREETLIGHTS_DEMO`)
3. Click **Configure CDC**
4. Enter PostgreSQL connection details
5. Select publication: `streetlights_publication`
6. Start replication

### 4.4 Verify Data in Snowflake

```sql
-- In Snowflake
SELECT COUNT(*) FROM STREETLIGHTS_DEMO."streetlights"."street_lights";
```

---

## Step 5: Snowflake Intelligence (Cortex Search + Analyst)

**Reference**: [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)

### 5.1 Create Analytics Schema and Cortex Search

```bash
snow sql -f snowflake/07_cortex_search_setup.sql
```

This creates:

- `ANALYTICS` schema
- `MAINTENANCE_SEARCHABLE` view
- `MAINTENANCE_SEARCH` Cortex Search service

### 5.2 Test Semantic Search

```bash
snow sql --stdin <<EOF
USE DATABASE STREETLIGHTS_DEMO;
SELECT * FROM TABLE(
  ANALYTICS.MAINTENANCE_SEARCH!SEARCH(
    query => 'flickering light electrical issue',
    columns => ['SEARCH_DESCRIPTION'],
    limit => 5
  )
);
EOF
```

### 5.3 Upload Semantic Model for Cortex Analyst

```bash
snow sql --stdin <<EOF
USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;
CREATE STAGE IF NOT EXISTS SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for Cortex Analyst semantic model files';
EOF

snow stage copy ./snowflake/streetlights_semantic_model.yaml '@streetlights_demo.analytics.semantic_models'
```

### 5.4 Wire to Snowflake Intelligence

1. Open **Snowflake Intelligence** (AI & ML > Snowflake Intelligence)
2. Click **Add Data Sources**
3. Add **Cortex Search** service: `MAINTENANCE_SEARCH`
4. Add **Semantic Model**: Navigate to `STREETLIGHTS_DEMO > ANALYTICS > SEMANTIC_MODELS > streetlights_semantic_model.yaml`
5. Click **Add**

### 5.5 Configure Orchestration Instructions

In Snowflake Intelligence settings, add these orchestration instructions:

```
- Whenever possible try to visualize the data graphically

- *CRITICAL*: When you get WKT format for location, try parsing it as geometric location as latitude and longitude. Don't show that you encountered SQL parsing error.

- *CRITICAL*: Wherever possible provide Google Map URL with latitude and longitude that were parsed from the SQL result in the response
```

> **Note**: [WKT (Well-Known Text)](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) is a standard text format for representing geometry objects like `POINT(77.5946 12.9716)`.

### 5.6 Test Combined Capabilities

Try these queries in Snowflake Intelligence:

| Query | Capability |
|-------|------------|
| "Find flickering lights in Koramangala" | Cortex Search |
| "How many street lights by status?" | Cortex Analyst |
| "Where are the faulty street lights?" | Cortex Analyst (returns coordinates) |

---

## Step 6: ML Forecasting

Train a forecasting model to predict future bulb failures.

### 6.1 Create Training Data Views

```bash
snow sql -f snowflake/08_ml_training_view.sql
```

### 6.2 Train Forecast Model

```bash
snow sql -f snowflake/09_ml_model_training.sql
```

### 6.3 View Model Metrics

```bash
snow sql --stdin <<EOF
USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;
CALL BULB_FAILURE_FORECASTER!SHOW_EVALUATION_METRICS();
EOF
```

### 6.4 Query Forecasts

**Next 7 days schedule:**

```bash
snow sql --stdin <<EOF
USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;
SELECT FORECAST_DATE, PREDICTED_FAILURES, PRIORITY, STAFFING_RECOMMENDATION, BULBS_TO_STOCK
FROM BULB_REPLACEMENT_SCHEDULE
WHERE FORECAST_DATE <= DATEADD('day', 7, CURRENT_DATE())
ORDER BY FORECAST_DATE;
EOF
```

**Weekly budget planning:**

```bash
snow sql --stdin <<EOF
USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;
SELECT
    DATE_TRUNC('week', FORECAST_DATE)::DATE AS WEEK_START,
    SUM(PREDICTED_FAILURES) AS TOTAL_FAILURES,
    SUM(PREDICTED_FAILURES) * 1650 AS TOTAL_BUDGET_INR
FROM BULB_REPLACEMENT_SCHEDULE
GROUP BY DATE_TRUNC('week', FORECAST_DATE)
ORDER BY WEEK_START;
EOF
```

**Seasonal risk comparison:**

```bash
snow sql --stdin <<EOF
USE DATABASE STREETLIGHTS_DEMO;
USE SCHEMA ANALYTICS;
SELECT SEASON, SUM(PREDICTED_FAILURES) AS total_failures,
       ROUND(AVG(PREDICTED_FAILURES), 1) AS avg_daily
FROM BULB_FAILURE_FORECAST_30D
GROUP BY SEASON
ORDER BY total_failures DESC;
EOF
```

---

## Validation Checklist

Run this validation query in Snowflake:

```sql
USE DATABASE STREETLIGHTS_DEMO;

SELECT 'Phase: CDC' AS phase, 
    CASE WHEN (SELECT COUNT(*) FROM "streetlights"."street_lights") > 0 
         THEN 'COMPLETE' ELSE 'INCOMPLETE' END AS status
UNION ALL
SELECT 'Phase: Cortex Search', 
    CASE WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.VIEWS 
                      WHERE TABLE_NAME = 'MAINTENANCE_SEARCHABLE') 
         THEN 'COMPLETE' ELSE 'INCOMPLETE' END
UNION ALL
SELECT 'Phase: ML Forecasting',
    CASE WHEN (SELECT COUNT(*) FROM ANALYTICS.BULB_FAILURE_FORECAST_30D) > 0 
         THEN 'COMPLETE' ELSE 'PENDING' END;
```

---

## Demo Complete!

Your environment now has:

| Component | Status |
|-----------|--------|
| **PostgreSQL + PostGIS** | Operational database with spatial capabilities |
| **Streamlit Dashboard** | Interactive visualization at localhost:8501 |
| **CDC Pipeline** | Real-time sync to Snowflake via Openflow |
| **Cortex Search** | Natural language search on maintenance data |
| **Cortex Analyst** | Structured analytics via semantic model |
| **ML Forecasting** | Bulb failure predictions with budget planning |

---

## Troubleshooting

### psql connection fails

```bash
# Verify environment variables are loaded
echo $PGHOST $PGPORT $PGDATABASE

# Test connection
psql -c "SELECT 1;"
```

### Snow CLI not working

```bash
# Check configuration
snow connection list

# Test connection
snow connection test
```

### Dashboard shows "Connection Error"

```bash
# Verify .env file has correct values
cat .env

# Ensure PostgreSQL is accessible
psql -c "SELECT PostGIS_Version();"
```

### CDC not syncing

```bash
# Check publication exists
psql -c "SELECT * FROM pg_publication;"

# Check replication slot status
psql -c "SELECT * FROM pg_replication_slots;"
```

---

## Next Steps

- See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for detailed demo scenarios
- Explore [snowflake/SNOWFLAKE_INTELLIGENCE_QUESTIONS.md](snowflake/SNOWFLAKE_INTELLIGENCE_QUESTIONS.md) for sample queries
- Review [work/snowflake_ml_guide.md](work/snowflake_ml_guide.md) for ML details

---

*Ready to demo!*
