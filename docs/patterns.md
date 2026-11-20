# Patterns discovered while building this demo

Each pattern: **Problem** (2–5 lines) → **Solution** (concise) → **Maps to** (product features) → **In this repo**.
Both platform paths are shown where a pattern exists on each.

---

## 1. Zero-pipeline Postgres → lakehouse

**Problem:** Getting Postgres data into an analytics/AI platform usually means CDC
(Debezium/OpenFlow), WAL publications, schema sync, and WKB serialization — a pipeline
to operate, lag to absorb, and data duplicated in two places.

**Solution:** Store Postgres tables as Iceberg and let the analytics catalog read the
*same metadata* — no data movement. Query the database in place from warehouses, agents,
and apps.

**Maps to:** Snowflake: pg_lake (`CREATE TABLE ... USING iceberg`) + Catalog-Linked
Database (CLD). Databricks: Lakebase database registered in Unity Catalog via
`databricks postgres create-catalog` (foreign catalog).

**In this repo:** `init/02_create_iceberg_tables.sql` (generated), skill step-4 (CLD),
`databricks/sql/01_setup.sql` (views over `${var.prefix}_STREETLIGHTS_PG`).

## 2. PostGIS stays in Postgres; analytics reads coordinates

**Problem:** Geo logic gets re-implemented per platform (GEOGRAPHY vs `ST_*`), and
moving geometry through pipelines forces WKB/WKT handling. Demos also risk implying
real infrastructure from real-looking coordinates.

**Solution:** Keep spatial truth in Postgres with the PostGIS extension (both managed
Postgres offerings support it natively); store plain lat/lng columns and rebuild
points at read time (`ST_POINT(lon, lat)`). Ship a synthetic-data disclaimer with any
demo map output.

**Maps to:** PostGIS on Snowflake Postgres and on Lakebase; Snowflake `GEOGRAPHY` /
Databricks DBSQL `ST_*` for analytics-side geo; README disclaimer.

**In this repo:** `init/01_enable_extensions.sql`, `databricks/sql/00_lakebase_schema.sql`,
`databricks/sql/01_setup.sql` (`location` column), `.cortex/skills/streetlights-demo/references/postgis-contrast.md`, README "Demo Data Disclaimer".

## 3. Semantic layer before natural language

**Problem:** NL questions fail or hallucinate when the model must guess table names,
joins, and business terms. Every analyst rewrites the same SQL.

**Solution:** Encode joins, entities, and business vocabulary once in a semantic
layer; the NL agent only generates SQL *through* it. On DBX the same role is played
by curated `*_clean` views plus Genie space instructions and verified answers.

**Maps to:** Snowflake Semantic View + Cortex Analyst. Databricks: curated views +
Genie space (instructions, verified answers, sample questions).

**In this repo:** `snowflake/02_semantic_view.sql`; `databricks/sql/01_setup.sql` (`*_clean` views),
`databricks/sql/02_genie_space.sql` (`v_q_*` verified-question views), `databricks/databricks.yml` (`genie_spaces`).

## 4. Hybrid retrieval: NL-to-SQL + vector search

**Problem:** "How many lights are faulty?" is structured, but "find reports about
exposed wires or sparking" is free text — SQL alone can't answer it, and embeddings
alone can't count.

**Solution:** Pair a semantic layer (NL→SQL) with a vector index over the text
column, and let the agent route per intent (structured → analyst, text → search,
hybrid → both).

**Maps to:** Snowflake Cortex Search + Intelligence Agent (Analyst + Search tools).
Databricks AI Search (Vector Search Delta Sync index, embeddings computed by a model
such as `databricks-bge-large-en`) + Genie space; query via `vector_search()`.

**In this repo:** `snowflake/03_cortex_search.sql`, `snowflake/04_intelligence_agent.sql`;
`databricks/sql/03_vector_search.sql` (`maintenance_records_text`), guide step 7.

## 5. Forecasting as a SQL function, not a Python job

**Problem:** Time-series forecasting usually means exporting data to Python/R,
training, hosting a model, and re-importing predictions — none of it visible in SQL.

**Solution:** Call the platform's forecast function in SQL where the data already
lives, and store predictions as a table the agent/app can query.

**Maps to:** Snowflake `ML FORECAST`. Databricks `ai_forecast(observed => TABLE(...),
horizon => ..., time_col => ..., value_col => ...)` — note it requires a **serverless**
SQL warehouse.

**In this repo:** `snowflake/05_ml_forecast.sql`; `databricks/sql/04_forecast.sql`
(`energy_forecast`, `energy_forecast_by_neighborhood`); serverless WH in
`databricks/databricks.yml` (`enable_serverless_compute: true`).

## 6. Cloud resources as code: bundles, not clicks

**Problem:** Creating catalogs, warehouses, jobs, spaces, and apps in the UI doesn't
version, review, or reproduce; raw SQL files alone don't express dependencies.

**Solution:** Declare resources + jobs in a bundle with variable interpolation and
dev/prod targets; validate → deploy → run → destroy is fully repeatable.

**Maps to:** Databricks Asset Bundles (`databricks.yml`, `${var.*}` interpolation,
`targets`, `engine: direct` for Genie/Vector Search). Snowflake equivalent here:
`snow` CLI + SQL files with `<% PREFIX %>` STANDARD templating.

**In this repo:** `databricks/databricks.yml` (jobs run `sql/01-05` via `sql_task`),
`Taskfile.yml` `dbx:*` tasks, `snowflake/0*.sql` + skill step rules.

## 7. Platform choice is explicit — and the other platform is ignored

**Problem:** A dual-platform repo can silently load or gate-check the wrong
platform's assets (e.g. Snowflake gates in a Databricks run), and defaulting to
"both" hides misconfiguration.

**Solution:** Resolve the platform from an explicit choice only (env var, manifest
field, cwd, or CLI flag). When one platform is chosen, ignore all of the other
platform's paths (SQL, gates, skills); if nothing is chosen, fail immediately —
never assume "both".

**Maps to:** repo tooling, not a product feature: `scripts/platform.py`
(`require_platform()`, `get_ignored_paths()`), `gate --platform`, `PLATFORM` env
(`.mise.toml`, `.env.example`), `scripts/gates/{base,snowflake,databricks}_gates.py`.

**In this repo:** `scripts/platform.py`, `scripts/gate.py` (`--platform`), `tests/test_platform.py` (`TestChosenPlatformIsolation`).

## 8. Gates as the per-step correctness contract

**Problem:** Multi-step demos drift silently: step N assumes step N−1's objects
exist, and failures surface far from the cause.

**Solution:** Every step has a gate function returning a pass/fail `GateResult`;
the CLI validates the chain before checking readiness, and the test suite pins
the contract so refactors can't quietly drop checks.

**Maps to:** repo tooling: `scripts/gate.py` + `scripts/gates/` (base + per-platform),
`tests/test_gates.py`.

**In this repo:** `scripts/gate.py`, `scripts/gates/`, `tests/test_gates.py`,
`tests/test_platform.py`.

---

## Cross-cutting observations

- **The Postgres wire protocol is the stable interface.** Both platforms are "just
  Postgres" to psql and drivers — schema DDL, `\copy` loads, and PostGIS work
  unchanged; only the sync/registration mechanism differs (CLD vs `create-catalog`).
- **AI features live next to the data, not in a sidecar.** Semantic views, search,
  forecasting, and agents all run in the analytics platform over the same tables —
  that is what makes the demo "zero-pipeline" end to end.
- **Fail fast on ambiguity.** Whether it's platform choice (`require_platform`) or
  billable resources (skill confirms before creating instances), explicit beats
  inferred.
