# Streetlights Demo — AI Agent Rules

Rules for any AI agent (Claude, Copilot, Cursor, etc.) running this demo.
All `{field}` values resolve from `.streetlights-demo/manifest.toml` via `load_manifest()`.

## 1. snow CLI

- All `snow sql` calls require: `--format json`, `-c {connection}`, `--enable-templating STANDARD`
- Template syntax is `<% PREFIX %>` (STANDARD mode). Never use `${VAR}` — bash-only, not expanded by snow CLI.
- Full execution pattern:
  ```bash
  snow sql -f snowflake/FILE.sql \
    -D "PREFIX={prefix.upper()}" \
    -D "ROLE={role}" \
    -c {connection} \
    --enable-templating STANDARD
  ```

## 2. Manifest: single source of truth

- All config from `.streetlights-demo/manifest.toml` via `load_manifest()`. Never use `.env` as a config source.
- `manifest.demo.prefix` is **lowercase**. SQL `-D "PREFIX=..."` must be **UPPERCASE**.

| Field | Purpose |
|-------|---------|
| `demo.prefix` | Resource name prefix (uppercase in SQL `-D` flags) |
| `demo.database` | Main Snowflake database (`{PREFIX}_STREETLIGHTS`) |
| `demo.cld_database` | Catalog-Linked Database — read-only (`{PREFIX}_STREETLIGHTS_CLD`) |
| `demo.warehouse` | Compute warehouse |
| `demo.pg_instance` | Snowflake Postgres instance name |
| `demo.pg_service` | psql service name (maps to `~/.pg_service.conf`) |
| `snowflake.connection` | snow CLI connection name |
| `snowflake.role` | Non-admin working role (grants target) |
| `snowflake.admin_role` | Elevated role for DDL and grants |

## 3. CLD column quoting

- CLD tables mirror PostgreSQL — all column names are **lowercase**.
- Always double-quote in Snowflake SQL: `"status"`, `"light_id"`, `"date"`, `"kwh"`.
- Unquoted identifiers are uppercased by Snowflake → `invalid identifier` error.

## 4. Object placement

- **All Snowflake objects** (Semantic Views, Cortex Search, Agents, ML Forecast, Streamlit) → `{database}.PUBLIC`
- **CLD** (`{cld_database}`) is **read-only** — SELECT only. Never CREATE in CLD.
  Error: `operation not supported in catalog-linked database`

## 5. PostgreSQL connections

- Connect via: `psql "service={pg_service}"`. Never use `-h`, `-U`, or `-d` flags.
- Credentials live in `~/.pg_service.conf` (managed by `$snowflake-postgres` skill).
- `pg_service` is `manifest.demo.pg_service`, **not** the `PGSERVICE` env var.

## 6. Roles

- **`admin_role`** (typically `ACCOUNTADMIN`): DDL — `CREATE WAREHOUSE`, `GRANT`, `CREATE SEMANTIC VIEW`, `CREATE CORTEX SEARCH SERVICE`, `CREATE AGENT`, `ALTER SNOWFLAKE INTELLIGENCE`.
- **`role`**: DML, verification queries, and day-to-day operations.

## 7. Warehouse resilience

- `{warehouse}` can be dropped by account-level cleanup jobs.
- If any gate step fails with "warehouse not found", recreate:
  ```sql
  USE ROLE {admin_role};
  CREATE WAREHOUSE IF NOT EXISTS {warehouse}
    WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE;
  GRANT USAGE ON WAREHOUSE {warehouse} TO ROLE {role};
  ```

## 8. Intelligence registration

- Agents must be explicitly registered to appear in the Snowflake Intelligence UI:
  ```sql
  ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
    ADD AGENT {database}.PUBLIC.STREETLIGHTS_AGENT;
  ```
- `04_intelligence_agent.sql` handles this automatically at the end of each deployment.
- `CREATE OR REPLACE AGENT` invalidates prior registration — re-registration always runs after redeploy.

## 9. Map links

- Always use **OpenStreetMap** (public, no API key, no billing):
  ```
  https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}&zoom=16
  ```
- Never display raw coordinates — always wrap in a map link with neighborhood name or pole_id as anchor text.

## 10. Gate timing

- Cache TTL: 1 hour. After expiry the gate re-verifies live state.
- Always pass `--prior-step` to enforce the full step-chain check.
- Cortex Search: wait **1–2 min** after creation for `ACTIVE` status.
- ML Forecast: wait **2–5 min** after `CREATE` for model training to complete.
