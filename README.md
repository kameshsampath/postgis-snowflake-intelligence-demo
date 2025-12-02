# PostGIS + Snowflake Openflow + Snowflake ML Demo

## Street Lights Maintenance - Production-Ready Architecture

This demo showcases a production-ready architecture for managing smart city street lights, featuring PostGIS for operational spatial queries, Snowflake Openflow for CDC, and Snowflake ML for predictive maintenance.

**All Phases Complete**: ✅ PostGIS + Enrichment + Streamlit + Snowflake CDC + Cortex Search + ML + Testing + Documentation

> **DISCLAIMER**: This project uses entirely fictitious data for demonstration and educational purposes. All company names, supplier names, contact information, and other data are computer-generated and do not represent real entities. Any resemblance to actual companies, organizations, or individuals is purely coincidental.

---

## 🚀 Quick Start

**⚡ Want to start immediately? See [QUICKSTART.md](QUICKSTART.md) for 5-minute setup!**

---

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for data generation)
- `uv` package manager (recommended) or `pip`
- 4GB RAM minimum
- Internet connection (for Docker image downloads)

**Install uv (recommended):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on macOS: brew install uv
```

### 1. Start the Environment

```bash
# Clone repository (if not already)
git clone <your-repo-url>
cd postgis-nifi-pipeline

# Copy environment template
cp .env.example .env
# Edit .env if needed (defaults work for Phase 1-5)

# Start Docker containers
docker-compose up -d

# Wait for PostgreSQL to be ready (~30 seconds)
docker logs streetlights-postgres
```

### 2. Load Data

**Option A: Quick Start with Sample Data** (10 lights, 5 neighborhoods)

```bash
# Load pre-generated sample data (fastest - no Python needed)
docker exec -it streetlights-postgres psql -U postgres -d streetlights -f /data/load_sample_data.sql
```

**Option B: Generate Full Dataset** (5,000 lights, 50 neighborhoods)

```bash
# Install Python dependencies with uv
uv pip install -e .

# Or with pip
pip install -e .

# Generate and load full dataset
cd data
./generate_all_data.sh

# Load into PostgreSQL
docker exec -it streetlights-postgres psql -U postgres -d streetlights -f /data/load_data.sql
```

### 3. Validate Installation

```bash
# Run validation tests
./test/test_phase1_5.sh

# Should see: "✓ ALL TESTS PASSED!"
```

### 4. Access the Dashboard

```bash
# Streamlit dashboard will start automatically with docker-compose
# Open in browser:
open http://localhost:8501

# Or access database directly
docker exec -it streetlights-postgres psql -U postgres -d streetlights

# Run sample PostGIS queries
cd queries/postgis && ./run_queries.sh
```

**Dashboard Features:**

- 🏘️ Neighborhood Overview - Interactive map with all layers
- 🔴 Faulty Lights Analysis - With nearest suppliers
- 🔮 Predictive Maintenance - ML predictions and timeline
- 🏭 Supplier Coverage - Service area analysis
- 🎮 Live Demo Controls - Simulate failures in real-time

---

## 📁 Project Structure

```
postgis-nifi-pipeline/
├── docker-compose.yml          # Infrastructure definition
├── .env.example               # Environment variables template
│
├── init/                      # PostgreSQL initialization scripts
│   ├── 01_enable_extensions.sql
│   ├── 02_enable_wal.sql
│   ├── 03_create_base_tables.sql
│   ├── 04_create_enrichment_tables.sql
│   ├── 05_create_enriched_views.sql
│   ├── 06_create_indexes.sql
│   └── 07_create_replication_slots.sql
│
├── data/                      # Data generation scripts
│   ├── generate_neighborhoods.py
│   ├── generate_street_lights.py
│   ├── generate_maintenance_history.py
│   ├── generate_suppliers.py
│   ├── generate_enrichment_data.py
│   ├── generate_all_data.sh
│   └── load_data.sql
│
├── queries/postgis/           # PostGIS query library
│   ├── q01_lights_in_neighborhood.sql
│   ├── q02_faulty_lights_radius.sql
│   ├── q03_lights_per_neighborhood.sql
│   ├── q04_maintenance_dispatch.sql
│   ├── q05_enriched_data_query.sql
│   ├── q06_nearest_supplier.sql
│   └── run_queries.sh
│
├── dashboard/                 # Streamlit dashboard (Phase 5.5)
│   └── app.py                # (to be created)
│
├── test/                      # Testing and validation
│   └── test_phase1_5.sh
│
├── work/                      # Documentation and planning
│   ├── about.md
│   ├── cfp.md
│   ├── architecture_diagram.md
│   ├── data_dictionary.md
│   ├── enrichment_strategy.md
│   ├── snowflake_ml_guide.md
│   ├── demo_script.md
│   └── implementation_plan.md
│
└── docs/                      # Additional documentation
    └── (future phase docs)
```

---

## 🏗️ Architecture

### Phase 1-5 (Current)

```
┌─────────────────────────────────────────────┐
│           PostGIS Database                  │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ Base Tables  │──┐   │  Enrichment     │ │
│  │              │  │   │  Tables         │ │
│  │ • Lights     │  ├──▶│                 │ │
│  │ • Neighborhoods  │   │ • Weather       │ │
│  │ • Requests   │  │   │ • Demographics  │ │
│  │ • Suppliers  │  │   │ • Power Grid    │ │
│  └──────────────┘  │   └─────────────────┘ │
│                    │                         │
│                    ▼                         │
│         ┌──────────────────────┐            │
│         │  Enriched Views      │            │
│         │                      │            │
│         │ street_lights_       │            │
│         │    enriched          │            │
│         └──────────┬───────────┘            │
└────────────────────┼────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  Streamlit Dashboard │
          │                      │
          │  • Interactive Maps  │
          │  • Analytics         │
          │  • Live Demo Controls│
          └──────────────────────┘
```

### Future Phases

```
PostGIS → Apache NiFi CDC → Snowflake RAW → Snowflake ML → Predictions
```

---

## 🗄️ Database Schema

### Base Tables

- **neighborhoods**: Geographic boundaries (polygons) with population data
- **street_lights**: Operational data (location, status, installation date)
- **maintenance_requests**: Historical maintenance records
- **suppliers**: Equipment suppliers with service coverage

### Enrichment Tables

- **weather_enrichment**: Seasonal patterns (monsoon, summer, winter) with failure risk scores
- **demographics_enrichment**: Neighborhood characteristics
- **power_grid_enrichment**: Electrical grid data per light

### Enriched Views

- **street_lights_enriched**: Combines lights with all enrichment (main CDC view)
- **maintenance_requests_enriched**: Maintenance history with context

See `data/SCHEMA_REFERENCE.md` for complete schema reference.

---

## 🔍 Sample Queries

### Find faulty lights within 1km

```sql
SELECT light_id, status,
       ST_Distance(location::geography, 
                   ST_MakePoint(77.5946, 12.9716)::geography) as distance_m
FROM street_lights
WHERE status = 'faulty'
  AND ST_DWithin(location::geography, 
                 ST_MakePoint(77.5946, 12.9716)::geography, 
                 1000);
```

### Query enriched view

```sql
SELECT light_id, status, neighborhood_name, season,
       failure_risk_score, predicted_failure_date,
       maintenance_urgency
FROM street_lights_enriched
WHERE failure_risk_score > 0.7
ORDER BY predicted_failure_date;
```

More queries in `queries/postgis/`

---

## 📊 Sample Data

- **5,000 street lights** across Bengaluru
- **50 neighborhoods** with realistic boundaries
- **25 suppliers** with service coverage
- **500 maintenance requests** (historical)
- **15,000 enrichment records** (3 seasons × 5,000 lights)

Status distribution:

- 85% operational
- 10% maintenance required
- 5% faulty

---

## 🎯 Key Features (Phase 1-5)

### PostGIS Spatial Operations

- ✅ Sub-second spatial queries (ST_Within, ST_DWithin, ST_Distance)
- ✅ Spatial indexes (GIST) for performance
- ✅ Point-in-polygon, proximity search, nearest neighbor
- ✅ Geography type for accurate meter-based distances

### Enrichment Strategy

- ✅ Separate enrichment tables (weather, demographics, power grid)
- ✅ Enriched views for combined data
- ✅ No external API dependencies (demo reliability)
- ✅ Educational SQL JOIN patterns

### Data Generation

- ✅ Realistic Bengaluru coordinates
- ✅ Seasonal patterns (monsoon = higher failures)
- ✅ Predicted failure dates for proactive maintenance
- ✅ Reproducible and customizable

---

## 🧪 Testing

```bash
# Run full validation
./test/test_phase1_5.sh

# Manual tests
docker exec -it streetlights-postgres psql -U postgres -d streetlights

# Check PostGIS version
SELECT PostGIS_Version();

# Count loaded data
SELECT COUNT(*) FROM street_lights;
SELECT COUNT(*) FROM neighborhoods;
SELECT COUNT(*) FROM suppliers;

# Test enriched view
SELECT * FROM street_lights_enriched LIMIT 5;
```

---

## 📖 Documentation

### Core Documentation

- **Architecture**: `work/architecture_diagram.md`
- **Schema Reference**: `data/SCHEMA_REFERENCE.md` (complete data dictionary)
- **Enrichment Strategy**: `work/enrichment_strategy.md`
- **Demo Script**: `work/demo_script.md` (30-minute presentation guide)

### Implementation

- **Full Plan**: `work/implementation_plan.md`
- **About**: `work/about.md` (technical specification)
- **CFP**: `work/cfp.md` (conference proposal)

---

## 🚦 Phase Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Documentation & Planning |
| Phase 2 | ✅ Complete | Docker Compose + Init Scripts |
| Phase 3 | ✅ Complete | Data Generation Scripts |
| Phase 4 | ✅ Complete | PostGIS Query Library |
| Phase 5 | ✅ Complete | Enrichment Documentation + Validator |
| **Phase 5.5** | **✅ Complete** | **Streamlit Dashboard** |
| **Phase 6** | **✅ Complete** | **Snowflake Openflow CDC** |
| **Phase 7** | **✅ Complete** | **Snowflake Cortex Search** |
| **Phase 8** | **✅ Complete** | **Snowflake ML Forecasting** |
| **Phase 9** | **✅ Complete** | **End-to-End Testing** |
| **Phase 10** | **✅ Complete** | **Final Documentation** |

---

## 🛠️ Common Commands

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker logs streetlights-postgres
docker logs streetlights-streamlit

# Restart services
docker-compose restart

# Remove volumes (clean slate)
docker-compose down -v
```

### Database Access

**Option 1: Via Docker (no local psql needed)**

```bash
# Interactive psql
docker exec -it streetlights-postgres psql -U postgres -d streetlights

# Run SQL file
docker exec -it streetlights-postgres psql -U postgres -d streetlights -f /path/to/file.sql

# Backup database
docker exec streetlights-postgres pg_dump -U postgres streetlights > backup.sql
```

**Option 2: Direct Connection (requires local PostgreSQL client)**

```bash
# Configure .env with connection details
cp .env.example .env

# Load PG* environment variables
source .env

# Connect (uses PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
psql

# Run queries directly
psql -c "SELECT COUNT(*) FROM street_lights;"
psql -f queries/postgis/q01_lights_in_neighborhood.sql

# Backup
pg_dump streetlights > backup.sql
```

### Data Management

```bash
# Regenerate all data
cd data
./generate_all_data.sh

# Load specific CSV
docker exec -it streetlights-postgres psql -U postgres -d streetlights -c "\copy street_lights FROM '/data/street_lights.csv' WITH CSV HEADER"
```

---

## 🎓 Educational Value

This demo is designed to teach:

1. **PostGIS Spatial Queries**: Real-world GIS operations
2. **Enrichment Patterns**: Separate enrichment tables + views
3. **CDC Preparation**: WAL configuration, replication slots
4. **Spatial Indexes**: GIST indexes for performance
5. **Docker Compose**: Multi-container application setup
6. **Data Generation**: Realistic sample data with Python
7. **Demo Reliability**: No external dependencies

---

## 🐛 Troubleshooting

### PostgreSQL won't start

```bash
# Check logs
docker logs streetlights-postgres

# Ensure port 5432 is available
lsof -i :5432

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Data not loading

```bash
# Verify CSV files exist
ls -lh data/*.csv

# Check permissions
chmod 644 data/*.csv

# Manual load
docker exec -it streetlights-postgres psql -U postgres -d streetlights -f /data/load_data.sql
```

### Streamlit not accessible

```bash
# Check if container is running
docker ps | grep streamlit

# Check logs
docker logs streetlights-streamlit

# Restart
docker-compose restart streamlit
```

---

## 🤝 Contributing

This is a demo project. Feel free to:

- Fork and customize for your use case
- Add new queries or visualizations
- Improve data generation algorithms
- Submit issues or suggestions

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Kamesh Sampath

---

## 🙏 Acknowledgments

- PostGIS for spatial database capabilities
- Snowflake Openflow for CDC capabilities
- Snowflake for AI Data Cloud
- Streamlit for rapid dashboard development

---

## 📧 Contact

For questions or demo requests, reach out via [your contact method]

---

**Built with ❤️ for the spatial data community**
