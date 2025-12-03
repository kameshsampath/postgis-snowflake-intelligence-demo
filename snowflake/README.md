# Snowflake Configuration Files

This directory contains SQL scripts and documentation for Phases 6-8 of the Street Lights Maintenance Demo.

> **Important:** Snowflake Openflow is configured via **Web UI**, not pure SQL.  
> SQL files here provide prerequisites and verification queries only.

---

## Phase 6: Snowflake Openflow CDC

### Quick Start

1. **Run SQL Prerequisites**: `OPENFLOW_QUICK_REFERENCE.sql`
   - Create OPENFLOW_ADMIN role
   - Grant permissions
   - Enable behavior change bundle

2. **Configure in Snowflake UI**:
   - Navigate to: Data → Ingestion → Openflow
   - Create deployment
   - Add PostgreSQL connector
   - Start pipeline

3. **Detailed Guide**: See `../work/PHASE6_SNOWFLAKE_OPENFLOW.md`
   - Complete step-by-step UI instructions
   - Troubleshooting
   - Verification queries

### Files

| File | Purpose |
|------|---------|
| `OPENFLOW_QUICK_REFERENCE.sql` | Copy-paste SQL commands for Openflow setup |

### What Openflow Does Automatically

- ✅ Creates database: `STREETLIGHTS_DEMO`
- ✅ Creates schema: `"streetlights"` (quoted lowercase from PostgreSQL)
- ✅ Creates all 7 tables with quoted lowercase names
- ✅ Converts PostGIS GEOMETRY → Snowflake GEOGRAPHY
- ✅ Loads initial snapshot data
- ✅ Streams ongoing CDC events in real-time

### ⚠️ CRITICAL: CDC Naming Convention

PostgreSQL CDC creates identifiers with **quoted lowercase** names:

```sql
-- Schema
"streetlights"          -- NOT PUBLIC

-- Tables (quoted lowercase)
"street_lights"         -- NOT STREET_LIGHTS
"neighborhoods"         -- NOT NEIGHBORHOODS
"maintenance_requests"  -- NOT MAINTENANCE_REQUESTS
"suppliers"             -- NOT SUPPLIERS

-- Columns (quoted lowercase)
"light_id"              -- NOT LIGHT_ID
"status"                -- NOT STATUS
"location"              -- NOT LOCATION
```

**Always use quoted identifiers when querying CDC tables:**

```sql
SELECT "light_id", "status" 
FROM STREETLIGHTS_DEMO."streetlights"."street_lights";
```

### Connection Details

```
Database:         streetlights
User:             postgres
Password:         (from .env file)
Port:             5432 (or ngrok port)
Replication Slot: snowflake_cdc_slot
Publication:      streetlights_publication
Plugin:           pgoutput
```

---

## Phase 7: Snowflake Cortex Search

**Status:** ✅ Complete

**Purpose:** Semantic search on maintenance request descriptions via Snowflake Intelligence

### Files

| File | Purpose |
|------|---------|
| `07_cortex_search_setup.sql` | Create Analytics schema, searchable view, and Cortex Search service |
| `SNOWFLAKE_INTELLIGENCE_QUESTIONS.md` | 40+ sample questions for Snowflake Intelligence |

### Quick Start

1. **Run setup script**: Execute `07_cortex_search_setup.sql` in Snowflake
2. **Wire to Snowflake Intelligence**: Connect the Cortex Search service
3. **Ask questions**: Use natural language in the Intelligence chat interface

### What It Does

- Creates `ANALYTICS` schema for search and ML artifacts
- Creates `MAINTENANCE_SEARCHABLE` view with synthesized descriptions
- Creates `MAINTENANCE_SEARCH` Cortex Search service
- Provides 40+ sample questions for Snowflake Intelligence demos
- Supports natural language queries via Snowflake Intelligence

---

## Phase 8: Snowflake Cortex Analyst

**Status:** ✅ Complete

**Purpose:** Structured analytics via semantic model and SQL generation

### Files

| File | Purpose |
|------|---------|
| `08_cortex_analyst_setup.sql` | Upload semantic model and wire to Snowflake Intelligence |
| `streetlights_semantic_model.yaml` | Semantic model definition for Cortex Analyst |

### Quick Start

1. **Upload semantic model**: Follow instructions in `08_cortex_analyst_setup.sql`
2. **Wire to Intelligence**: Connect in Snowflake Intelligence UI
3. **Ask analytical questions**: "How many lights are faulty?", "Average resolution time?"

---

## Phase 9: Snowflake ML for Forecasting

**Status:** ✅ Complete

**Purpose:** ML FORECAST models for bulb failure predictions and total maintenance workload

### Files

| File | Purpose |
|------|---------|
| `09_ml_training_view.sql` | Prepare time-series training data (bulb failures + all issues) |
| `10_ml_model_training.sql` | Train FORECAST models (BULB_FAILURE_FORECASTER + ALL_ISSUES_FORECASTER) |
| `11_ml_queries.sql` | Demo queries for daily/weekly/monthly forecasts |

### Quick Start

1. **Run training view script**: Execute `09_ml_training_view.sql`
2. **Train models**: Execute `10_ml_model_training.sql` (takes 2-5 minutes)
3. **Query forecasts**: Use `11_ml_queries.sql` for examples

### What It Does

- Creates time-series views for bulb failures and all maintenance issues
- Trains TWO FORECAST models:
  - `BULB_FAILURE_FORECASTER` - Predicts daily bulb replacements needed
  - `ALL_ISSUES_FORECASTER` - Predicts total maintenance workload
- Generates 30-day and 90-day forecasts with confidence intervals
- Creates actionable views: `BULB_REPLACEMENT_SCHEDULE`, `MAINTENANCE_SCHEDULE`
- Provides budget and staffing recommendations

---

## Phase 9: End-to-End Testing

**Status:** ✅ Complete

**Purpose:** Comprehensive validation of all Snowflake components

### Files

| File | Purpose |
|------|---------|
| `11_end_to_end_tests.sql` | Automated tests for Phase 6-8 validation |

### Quick Start

1. **Run in Snowflake**: Execute `11_end_to_end_tests.sql`
2. **Review results**: Check PASS/FAIL status for each test
3. **Manual tests**: Run commented queries for interactive testing

### What It Tests

- Phase 6: CDC tables exist and have data
- Phase 7: Analytics schema and Cortex Search service
- Phase 8: ML training views, predictions, and urgency classification
- Combined: ML + Spatial + Search integration

---

## File Naming Convention

- `0X_*` - Files are numbered by phase (06, 07, 08)
- `OPENFLOW_*` - Configuration and reference for Snowflake Openflow
- `*_setup.sql` - Initial setup/creation scripts
- `*_queries.sql` - Demo and example queries
- `*_reference.sql` - Quick reference guides

---

## Prerequisites

### Before Phase 6

- ✅ PostgreSQL with PostGIS running
- ✅ WAL configured (`wal_level = logical`)
- ✅ Replication slot created (`snowflake_cdc_slot`)
- ✅ Publication created (`streetlights_publication`)
- ✅ Sample data loaded

Verify with: `../test/test_phase6_prerequisites.sh`

### Before Phase 7

- Snowflake Openflow configured
- All tables synced to Snowflake
- CDC working (changes flow from PostgreSQL to Snowflake)

### Before Phase 8

- Phase 7 complete (Cortex Search working)
- Sufficient historical maintenance data
- Training data view created

---

## Snowflake Requirements

### Account

- Snowflake account (trial or paid)
- Region: Any (prefer same region as PostgreSQL for lower latency)

### Permissions Required

- `ACCOUNTADMIN` role (or equivalent with):
  - CREATE DATABASE
  - CREATE CONNECTION
  - CREATE STREAM
  - CREATE CORTEX SEARCH SERVICE (Phase 7)
  - CREATE ML MODEL (Phase 8)

### Compute

- **Phase 6 (CDC):** XSMALL warehouse sufficient
- **Phase 7 (Cortex Search):** SMALL warehouse recommended
- **Phase 8 (ML Training):** MEDIUM warehouse for training, SMALL for inference

### Costs (Estimate)

- **CDC Streaming:** ~$2-5/day (continuous XSMALL warehouse)
- **Cortex Search:** ~$0.001 per query
- **ML Training:** ~$1-2 per training run
- **ML Predictions:** ~$0.50/day for daily batch predictions

---

## Network Configuration

### Development (ngrok)

```bash
ngrok tcp 5432
# Use forwarding address in Snowflake connection
```

### Cloud Deployment

- Configure security groups to allow Snowflake IP ranges
- Use public IP or hostname
- Ensure port 5432 is accessible

### Production (Recommended)

- AWS PrivateLink or Azure Private Link
- No public IP exposure required
- Better security and performance

---

## Testing

### Phase 6 Test - CDC Working

```sql
-- In Snowflake, verify row counts match PostgreSQL
SELECT COUNT(*) FROM postgres_streetlights.public.street_lights;

-- Update in PostgreSQL:
-- UPDATE street_lights SET status = 'faulty' WHERE light_id = 'SL-0001';

-- Wait 10 seconds, then check Snowflake:
SELECT * FROM postgres_streetlights.public.street_lights 
WHERE light_id = 'SL-0001';
-- Expected: status = 'faulty'
```

### Phase 7 Test - Cortex Search Working

```sql
-- Search for similar maintenance issues
SELECT * FROM TABLE(
  analytics.maintenance_search!SEARCH('flickering LED bulb')
) LIMIT 10;
```

### Phase 8 Test - ML Predictions Working

```sql
-- View predicted failures
SELECT * FROM analytics.predicted_failures
WHERE maintenance_urgency IN ('CRITICAL', 'HIGH')
ORDER BY predicted_failure_date
LIMIT 10;
```

---

## Documentation References

| Document | Location | Purpose |
|----------|----------|---------|
| Phase 6 Complete Guide | `../work/PHASE6_SNOWFLAKE_OPENFLOW.md` | Detailed Openflow setup |
| Phase 6 Summary | `../PHASE6_SUMMARY.md` | Implementation checklist |
| Main README | `../README.md` | Project overview |
| Prerequisites Test | `../test/test_phase6_prerequisites.sh` | Validation script |

---

## Support

### Common Issues

1. **"Connection refused"**
   - Check PostgreSQL is accessible from internet
   - Verify port and hostname
   - Test with telnet/nc

2. **"Replication slot not found"**
   - Run prerequisites test: `../test/test_phase6_prerequisites.sh`
   - Restart PostgreSQL if needed

3. **"No tables synced"**
   - Check Openflow logs in Snowflake
   - Verify publication exists in PostgreSQL
   - Ensure tables have data

See troubleshooting section in `../work/PHASE6_SNOWFLAKE_OPENFLOW.md`

---

## Next Steps

1. **Configure Openflow** (Phase 6)
   - Follow `OPENFLOW_QUICK_REFERENCE.sql`
   - Verify data sync
   - Test CDC

2. **Add Cortex Search** (Phase 7)
   - Wait for Phase 7 files
   - Configure search service
   - Test semantic search

3. **Train ML Models** (Phase 8)
   - Wait for Phase 8 files
   - Prepare training data
   - Generate predictions

---

**Built with ❤️ for AI-powered data pipelines**
