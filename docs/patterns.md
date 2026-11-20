<!-- Copyright 2025 Kamesh Sampath <kamesh.sampath@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Patterns from this demo

Reusable patterns observed while building the PostGIS data intelligence demo on two
platforms. Each entry covers the problem, the solution in platform-neutral terms, the
product features it maps to, and where it lives in this repo.

## Overview

| # | Pattern | Essence |
|---|---------|---------|
| 1 | Zero-pipeline Postgres sync | Query Postgres from the lakehouse without moving data |
| 2 | Geo truth stays in Postgres | PostGIS in the database, coordinates in analytics |
| 3 | Semantic layer before NL | Encode joins and vocabulary once; agents generate SQL through it |
| 4 | Hybrid retrieval for agents | NL-to-SQL plus vector search, routed per question |
| 5 | Forecasting as a SQL function | Predict in place, store predictions as a table |
| 6 | Cloud resources as code | Bundles with variables and targets, not UI clicks |
| 7 | Explicit platform choice | One platform chosen; the other is ignored; no choice fails fast |
| 8 | Per-step gates | Every step has a pass/fail check; tests pin the contract |

---

## 1. Zero-pipeline Postgres sync

**Problem**

Moving operational Postgres data into an analytics platform usually requires a CDC
pipeline: WAL capture, connectors, schema sync, and duplicated storage. The pipeline
lags behind, breaks on DDL changes, and costs money to operate.

**Solution**

Store Postgres tables in an open table format (Apache Iceberg) and register that
metadata with the analytics catalog. Warehouses, agents, and apps then query the
database in place. No data is copied or streamed.

**Maps to**

| Platform | Feature |
|----------|---------|
| Snowflake | pg_lake (`CREATE TABLE ... USING iceberg`) + Catalog-Linked Database (CLD) |
| Databricks | Lakebase database registered in Unity Catalog via `databricks postgres create-catalog` (foreign catalog) |

**In this repo:** `init/02_create_iceberg_tables.sql` (generated), skill step 4 (CLD), `databricks/sql/01_setup.sql` (views over the registered catalog)

## 2. Geo truth stays in Postgres

**Problem**

Re-implementing spatial logic per analytics platform is error-prone: each platform has
its own geo types and functions, and pushing geometry through pipelines adds WKB/WKT
serialization overhead.

**Solution**

Keep spatial data in the database using the PostGIS extension. Store plain
latitude/longitude columns and rebuild points at read time (`ST_POINT(lon, lat)`) in
the analytics layer.

**Maps to**

| Platform | Feature |
|----------|---------|
| Both | PostGIS extension on the managed Postgres service |
| Snowflake | `GEOGRAPHY` type for read-side geo |
| Databricks | SQL `ST_*` functions (e.g. `ST_POINT`) for read-side geo |

**In this repo:** `init/01_enable_extensions.sql`, `databricks/sql/00_lakebase_schema.sql`, `location` column in `databricks/sql/01_setup.sql`, `.cortex/skills/streetlights-demo/references/postgis-contrast.md`

## 3. Semantic layer before natural language

**Problem**

NL-to-SQL fails or invents schemas when the model has to guess table names, joins, and
business terms. Every user ends up rewriting the same queries.

**Solution**

Encode joins, entities, and vocabulary once in a semantic layer. The NL agent
generates SQL only through that layer, and verified question/answer pairs pin down
known intents.

**Maps to**

| Platform | Feature |
|----------|---------|
| Snowflake | Semantic View + Cortex Analyst |
| Databricks | Curated views + Genie space (instructions, verified answers, sample questions) |

**In this repo:** `snowflake/02_semantic_view.sql`; `databricks/sql/01_setup.sql` (`*_clean` views), `databricks/sql/02_genie_space.sql` (`v_q_*` verified-question views), `genie_spaces` resource in `databricks/databricks.yml`

## 4. Hybrid retrieval for NL agents

**Problem**

Some questions are structured ("how many lights are faulty?") and some are free text
("find reports about exposed wires or sparking"). SQL alone cannot answer the second;
embeddings alone cannot answer the first.

**Solution**

Combine a semantic layer for NL-to-SQL with a vector index over the text column, and
let the agent route each question to the right tool, or both for hybrid intents.

**Maps to**

| Platform | Feature |
|----------|---------|
| Snowflake | Cortex Search service + Intelligence Agent (Analyst + Search tool routing) |
| Databricks | AI Search / Vector Search Delta Sync index with a managed embedding model (e.g. `databricks-bge-large-en`) + Genie; query via `vector_search()` |

**In this repo:** `snowflake/03_cortex_search.sql`, `snowflake/04_intelligence_agent.sql`; `databricks/sql/03_vector_search.sql`, `docs/databricks-guide.md` step 7

## 5. Forecasting as a SQL function

**Problem**

Time-series forecasting often means exporting data to Python, training a model,
hosting it, and importing predictions back. None of it is visible in SQL where the
data lives.

**Solution**

Call the platform's forecast function in SQL and materialize predictions as a table
that agents and apps can query like any other table.

**Maps to**

| Platform | Feature |
|----------|---------|
| Snowflake | `ML FORECAST` |
| Databricks | `ai_forecast(observed => TABLE(...), horizon => ..., time_col => ..., value_col => ...)`; requires a serverless SQL warehouse |

**In this repo:** `snowflake/05_ml_forecast.sql`; `databricks/sql/04_forecast.sql` (`energy_forecast`, `energy_forecast_by_neighborhood`); serverless warehouse flag in `databricks/databricks.yml`

## 6. Cloud resources as code

**Problem**

Creating catalogs, warehouses, jobs, spaces, and apps by hand in a UI does not
version, review, or reproduce. Raw SQL files alone do not express dependencies
between objects.

**Solution**

Declare resources and jobs in a bundle file with variable interpolation and
per-environment targets. Validate, deploy, run, destroy becomes a repeatable
pipeline.

**Maps to**

| Platform | Feature |
|----------|---------|
| Databricks | Asset Bundles: `databricks.yml`, `${var.*}` interpolation, `targets` (dev/prod), `engine: direct` for Genie spaces and Vector Search endpoints |
| Snowflake | `snow` CLI running SQL files with `<% PREFIX %>` STANDARD templating |

**In this repo:** `databricks/databricks.yml` (jobs run `sql/01` to `sql/05` via `sql_task`), `Taskfile.yml` `dbx:*` tasks, `snowflake/*.sql`

## 7. Explicit platform choice, fail fast otherwise

**Problem**

In a repo that supports two platforms, tooling can silently load or gate-check the
wrong platform's assets. Defaulting to "both" hides that misconfiguration.

**Solution**

Resolve the platform only from an explicit choice: environment variable, manifest
field, working directory, or CLI flag. When one platform is chosen, ignore all of the
other platform's paths (SQL, gates, skills). If nothing is chosen, fail immediately
instead of assuming both.

**Maps to**

| Area | Feature |
|------|---------|
| Repo tooling | `scripts/platform.py` (`require_platform()`, `get_ignored_paths()`), `gate --platform`, `PLATFORM` env var, per-platform gate modules in `scripts/gates/` |

**In this repo:** `scripts/platform.py`, `scripts/gate.py`, `scripts/gates/`, `tests/test_platform.py` (`TestChosenPlatformIsolation`)

## 8. Per-step gates as a correctness contract

**Problem**

Multi-step demos drift silently. Step N assumes step N-1 created its objects, so
failures surface far from the actual cause.

**Solution**

Give every step a gate check that returns pass/fail. The CLI validates the whole
chain before checking readiness, and the test suite pins the checks so refactors
cannot quietly drop them.

**Maps to**

| Area | Feature |
|------|---------|
| Repo tooling | Gate CLI (`scripts/gate.py`), per-platform gate modules (`scripts/gates/`), contract tests (`tests/test_gates.py`) |

**In this repo:** `scripts/gate.py`, `scripts/gates/`, `tests/test_gates.py`, `tests/test_platform.py`

---

## How the patterns compose

The end-to-end demo is these patterns stacked:

PostGIS in Postgres (2) → register the database in the lakehouse catalog (1) →
build the semantic layer (3) → attach hybrid retrieval (4) and forecasting (5) →
expose through an agent and an app. Pattern 6 declares the cloud side as code;
patterns 7 and 8 keep the repository tooling honest.

## Cross-cutting observations

- The Postgres wire protocol is the stable interface across platforms. Schema DDL,
  `\copy` loads, and PostGIS behave identically; only the registration mechanism
  differs.
- AI features run next to the data, inside the analytics platform. That is what makes
  the demo zero-pipeline end to end.
- Fail fast on ambiguity. Explicit choices (platform, billable resources) beat
  inferred defaults.
