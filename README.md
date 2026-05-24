# Streetlights Intelligence Demo

**Snowflake Postgres + pg_lake + Cortex AI**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

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

The recommended path uses Cortex Code's guided workflow. Each step follows a
**What we'll do → Proceed? → Execute → What we did** pattern — you always see
what's about to happen and confirm before anything runs.

### 1. Open Cortex Code in this project

```bash
cd postgis-snowflake-intelligence-demo
cortex
```

### 2. Run the guided setup

Type in the Cortex Code prompt:

```
$streetlights-demo setup
```

This will:
- Ask for your **resource prefix** (e.g., `kameshs` → resources named `KAMESHS_STREETLIGHTS_*`)
- Auto-detect your **city** (or ask you to pick one)
- Ask which **Snowflake connection** to use
- Write `.streetlights-demo/manifest.toml` (gitignored, local only)

### 3. Walk through steps 1–10

Each step shows what it will do, asks you to confirm, executes, then shows results:

```
$streetlights-demo step 1    # Generate synthetic data (7 CSVs for your city)
$streetlights-demo step 2    # Create Snowflake Postgres instance (⚠️ billable)
$streetlights-demo step 3    # Create Iceberg tables + load data
$streetlights-demo step 4    # Create CLD — zero-pipeline sync (⚠️ billable)
$streetlights-demo step 5    # Create Semantic View
$streetlights-demo step 6    # Create Cortex Search service
$streetlights-demo step 7    # Create Intelligence Agent
$streetlights-demo step 8    # Train ML Forecast model
$streetlights-demo step 9    # Deploy Streamlit app
$streetlights-demo step 10   # Validate everything + demo questions
```

> **Tip**: You can run steps individually or ask CoCo to "run all remaining steps"
> and it will walk you through each one sequentially.

### 4. Test the demo end-to-end

After step 10 completes, your Intelligence Agent is live. Test it in **Snowflake Intelligence** (Snowsight) or directly via CoCo:

```sql
-- In Snowsight → Intelligence → select your agent
-- Or via SQL:
SELECT SNOWFLAKE.CORTEX.AGENT(
  '{PREFIX}_STREETLIGHTS_CLD.streetlights.streetlights_agent',
  'How many street lights are currently faulty?'
);
```

**Sample intents — grouped by routing path:**

| Category | Intent | Routes to |
|---|---|---|
| Status | "How many street lights are currently faulty?" | Analyst |
| Geographic | "Show me faulty lights in Koramangala" | Analyst |
| Energy | "Which neighborhoods have the highest energy consumption?" | Analyst |
| Cost | "What is the average repair cost by maintenance type?" | Analyst |
| Rankings | "Show me the top 5 neighborhoods by maintenance frequency" | Analyst |
| Predictive | "Predict energy consumption for the next 30 days" | Analyst (Forecast) |
| Safety | "Find maintenance reports about exposed wires or sparking" | Search |
| Maintenance | "What does the maintenance history say about pole integrity?" | Search |
| Hybrid | "Tell me about maintenance issues in the busiest neighborhood" | Analyst + Search |
| Hybrid | "What's the repair status for flickering light reports?" | Analyst + Search |

> **Routing logic**: Structured questions involving counts, trends, or rankings route to
> **Cortex Analyst** (generates SQL via the Semantic View). Questions about maintenance
> descriptions, observations, or field notes route to **Cortex Search** (semantic similarity
> over maintenance text). Hybrid intents trigger both tools.

The Agent will:
- Route structured questions to **Cortex Analyst** (generates SQL via Semantic View)
- Route text/description queries to **Cortex Search** (semantic similarity)
- Generate **map links** when results include lat/lng coordinates
- Produce **charts** when data is suitable for visualization

### 5. Clean up when done

```
$streetlights-demo cleanup
```

Tears down all resources in reverse order (drops Agent → Search → View → CLD → PG instance).
Confirms each destructive step before executing.

---

### What each step verifies (gate checks)

| Step | Gate Check | What it confirms |
|------|-----------|-----------------|
| setup | `manifest_exists` | Config file parseable |
| 2 | `pg_reachable` + `pg_managed_storage` | Instance up + managed storage |
| 3 | Row count queries | All 7 tables loaded |
| 4 | `cld_healthy` (30s retry) | CLD propagation complete, 7 tables visible |
| 5 | `semantic_view_exists` | DDL succeeded |
| 6 | `cortex_search_ready` | Service status = ACTIVE |
| 7 | `agent_accessible` | Agent responds to test query |
| 8 | `forecast_model_ready` | Model trained |
| 9 | `SHOW STREAMLITS` | App deployed |
| 10 | `sanity_gate.py` | Full end-to-end smoke test |

## Intent-Driven Development (IDD)

This demo is a working example of IDD in practice — you express *what* you want,
the agent determines *how*. No table names. No JOIN syntax. No schema knowledge required.

### Intent Compression Ratio (ICR)

ICR measures how much operational complexity the system absorbs per unit of developer intent
([blog](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)):

$$
\text{ICR} = \frac{\text{Total Operations Required}}{\text{Number of Intent Expressions}}
$$

**"Traditional ops"** includes all discrete manual actions without this skill:
SQL statements written, bash/shell commands run, Python scripts called, API calls made,
and configuration files written.

**ICR score** (per [icr-lab](https://github.com/kameshsampath/icr-lab) formula) measures
token efficiency — ops achieved per intent token spent:

$$
\text{ICR score} = \left\lfloor \frac{\text{Ops Achieved}}{\text{NL Tokens}} \times 1000 \right\rfloor
$$

Run `uv run idd-metrics` to compute live ICR scores for the demo intents.

**Demo ICR — this session:**

| Intent | Traditional ops | ICR |
|---|---|---|
| "How many street lights are faulty?" | SELECT + WHERE + COUNT + GROUP BY + format = 5 | **5** |
| "Which neighborhoods use most energy?" | 2-table JOIN + GROUP BY + ORDER BY + LIMIT = 5 | **5** |
| "Find reports about exposed wires" | Semantic search + rank + dedupe + display = 4 | **4** |
| "Predict energy for next 30 days" | FORECAST call + params + execute + chart = 5 | **5** |
| "Issues in the busiest neighborhood" | Subquery + JOIN + Search + merge results = 8 | **8** |

**Average ICR: 5** (27 ops ÷ 5 intents, floor — ops are always whole numbers)

### Token Economics

SQL tokens generated per NL token expressed — measured with `SNOWFLAKE.CORTEX.COUNT_TOKENS`
([blog](https://blogs.kameshs.dev/icr-and-token-economics-9a014a75b399)):

| Intent | NL tokens | Est. SQL tokens | SQL tokens / NL token |
|---|---|---|---|
| "How many street lights are faulty?" | 8 | ~42 | 5.3 |
| "Which neighborhoods use most energy?" | 7 | ~58 | 8.3 |
| "Tell me about issues in the busiest neighborhood" | 9 | ~85 (SQL + search query) | 9.4 |

> Run `uv run idd-metrics` to compute live token counts using `SNOWFLAKE.CORTEX.COUNT_TOKENS`.
> tiktoken (cl100k_base) is used as offline fallback when no Snowflake connection is configured.

### Other IDD Signals

| Metric | Value | What it means |
|---|---|---|
| **Schema abstraction** | 7 tables, 0 mentioned by user | User never specifies a table or column name |
| **Tool routing** | 2 tools, automatic selection | Agent chooses Analyst or Search per intent |
| **Join elimination** | Avg ~2 joins per query, 0 specified | Semantic View encodes all join logic |
| **Intent log** | 500 operational intents tracked | Maintenance work surfaces as structured data |

> See [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
> for the broader IDD philosophy.

---

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
│   └── 02_create_iceberg_tables.sql    # All 7 Iceberg tables (generated)
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

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

Copyright 2025 Kamesh Sampath
