# Plan: Databricks Implementation + Rename to `postgis-data-intelligence-demo`

Status: **Implementation in progress**
Scope: add Databricks implementation alongside the existing Snowflake implementation, and
rename the project from `postgis-snowflake-intelligence-demo` to
`postgis-data-intelligence-demo`.

## Current state (inspected on `main`)

- Snowflake-only demo: `init/` (PostGIS + pg_lake DDL), `snowflake/` (5 DDL
  scripts: setup, semantic view, Cortex Search, Intelligence Agent, ML
  forecast), `app/` (Streamlit in Snowflake), `.cortex/skills/streetlights-demo/`
  (guided 10-step skill), `scripts/` (gates, manifest, generation).
- Manifest (`scripts/_manifest.py`) has only a `[snowflake]` section.
- Old repo name appears in 4 files (5 refs): `CITATION.cff`, `pyproject.toml`,
  `README.md`, `uv.lock` — plus the GitHub repo itself.
- `AGENTS.md` marks `.cortex/skills/streetlights-demo/`, `scripts/`, `snowflake/`,
  `init/`, `tests/` as stable framework areas.

## Part A — Rename to `postgis-data-intelligence-demo`

1. **GitHub repo rename** (when approved):
   `gh api -X PATCH /repos/kameshsampath/postgis-snowflake-intelligence-demo -f name=postgis-data-intelligence-demo`
   (verify `gh auth status` = `kameshsampath` first, per `AGENTS.md`), then
   `git remote set-url origin https://github.com/kameshsampath/postgis-data-intelligence-demo`.
2. **In-repo refs**: `CITATION.cff` (`repository-code`, `url`),
   `pyproject.toml` `name`, `README.md` title + `cd` line; regenerate
   `uv.lock` with `uv lock` after the `pyproject.toml` edit.
3. **Deliberately unchanged**: `.streetlights-demo/` manifest dir, the
   `streetlights-demo` skill name, and the `snowflake/` directory — the
   streetlights scenario and the Snowflake path stay intact; only the platform
   framing broadens. Reword `AGENTS.md` purpose line and README subtitle to
   "PostGIS data intelligence demo — Snowflake + Databricks".

## Part B — Databricks Implementation (Lakebase + Genie)

Component mapping from the Snowflake implementation to the Databricks stack:

| Snowflake Implementation | Databricks Implementation |
|---|---|
| Snowflake Postgres + pg_lake Iceberg | **Lakebase** (managed Postgres; `init/01_enable_extensions.sql` PostGIS DDL reuses directly) |
| CLD zero-pipeline sync | Lakebase ↔ Unity Catalog sync (PG tables queryable in UC) |
| Semantic View | **Genie space** config over UC schema (curated views + instructions + verified answers) |
| Cortex Search | Vector Search index on maintenance text (Delta + AI embeddings) |
| Intelligence Agent | **Genie** (NL over structured + vector search tools) |
| ML FORECAST | `AI_FORECAST()` on `energy_consumption` |
| Streamlit in Snowflake | Databricks Apps (Streamlit) on a Lakebase UC connection |
| `snow` CLI | Databricks CLI + Asset Bundles (`databricks.yml`) |

### New / changed files

- `databricks/` — new top-level dir: `databricks.yml` bundle,
  `sql/01_setup.sql` (catalog/schema, Lakebase→UC sync, curated views),
  `02_genie_space.sql`, `03_vector_search.sql`, `04_forecast.sql`, `05_app`,
  plus `databricks/README.md`.
- `scripts/_manifest.py` — additive `[databricks]` section (host/profile, SQL
  warehouse, catalog, schema, Lakebase instance/branch) + a `platform` field
  (`snowflake` | `databricks` | `both`); `[snowflake]` untouched.
- `scripts/gates/` + `tests/` — new Databricks gates (lakebase reachable, UC sync
  healthy, Genie space responds, vector index ready, forecast ready, app
  deployed) and manifest tests; no existing assertions weakened.
- `Taskfile.yml` — `dbx:*` tasks mirroring `sf:*`.
- `.cortex/skills/streetlights-demo/` — new `dbx` phase steps + `SKILL.md`
  routing entries, following the skill standards in `AGENTS.md` (frontmatter
  `name`/`description` only, `SKILL.md` under 500 lines).
- `app/` — Lakebase connection profile variant for Databricks Apps; views reused.
- `.env.example` — `DATABRICKS_HOST` / `DATABRICKS_PROFILE` only (auth via CLI
  profile/OAuth; no secrets).
- `AGENTS.md` / `README.md` — add `databricks/` to the stable framework areas;
  two-platform Mermaid architecture + Databricks quick start.

## Sequencing

1. Rename only (GitHub repo + 4 in-repo files) — one isolated commit.
2. `databricks/` skeleton + manifest `[databricks]` section + tests.
3. Lakebase → UC sync → Genie space + vector search steps and gates.
4. Forecast (`AI_FORECAST`) + Databricks App + cleanup + skill routing + docs.

## Guardrails

- `AGENTS.md` protected areas stay protected: Databricks work goes in new
  `databricks/` plus additive changes elsewhere; `tests/` assertions are never
  weakened.
- Conventional Commits style; `pre-commit run --all-files` must pass before
  committing.
- All GitHub operations via the `kameshsampath` account (`gh auth status`
  check first).
- No secrets in `.env.example` / manifest; Lakebase credentials via Databricks
  CLI profile or Unity Catalog connections.
- `data/` CSVs remain git-ignored; generated artifacts never committed.
