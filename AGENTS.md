# Streetlights Demo — AI Agent Rules

Rules for any AI agent (Claude, Copilot, Cursor, etc.) running this demo.

## snow CLI

- `snow sql` always requires: `--format json`, `-c {connection}`, `--enable-templating ALL`
- Execute SQL templates: `snow sql -f snowflake/FILE.sql -D "PREFIX=KAMESHS" -c {connection} --enable-templating ALL`
- Template syntax is `<% PREFIX %>` (Snowflake STANDARD mode). Never use `${PREFIX}` — that is bash-only and is not expanded by snow CLI.

## Configuration: manifest.toml is source of truth

- All config comes from `.streetlights-demo/manifest.toml` via `load_manifest()`.
- `.env` is a derived convenience file — never read it as a configuration source.
- `manifest.demo.prefix` is lowercase (`kameshs`). SQL `-D "PREFIX=..."` value must be UPPERCASE (`KAMESHS`).
- Key manifest fields: `connection`, `role`, `admin_role`, `warehouse`, `database`, `cld_database`, `pg_service`, `prefix`.

## CLD column quoting

- CLD tables come from PostgreSQL where all identifiers are lowercase.
- **Always double-quote column names** in Snowflake SQL: `"status"`, `"light_id"`, `"date"`, `"kwh"`, etc.
- Unquoted identifiers are uppercased by Snowflake and raise "invalid identifier" errors.

## Object placement

- Semantic views, Cortex Search services, Agents, ML Forecast models, Streamlit apps → `{PREFIX}_STREETLIGHTS.PUBLIC`
- CLD (`{PREFIX}_STREETLIGHTS_CLD`) is **read-only** — it mirrors PostgreSQL. Only TABLE references (SELECT FROM) are valid there.
- Attempting to CREATE any object in CLD produces: `operation not supported in catalog-linked database`

## Real CLD table names (from PostgreSQL)

| Table | Columns |
|---|---|
| `"street_lights"` | `"id"`, `"pole_id"`, `"latitude"`, `"longitude"`, `"neighborhood"`, `"install_date"`, `"wattage"`, `"light_type"`, `"status"` |
| `"maintenance_records"` | `"id"`, `"light_id"`, `"date"`, `"type"`, `"description"`, `"cost"`, `"technician"` |
| `"energy_consumption"` | `"id"`, `"light_id"`, `"date"`, `"hour"`, `"kwh"`, `"voltage"`, `"power_factor"` |
| `"light_sensors"` | `"id"`, `"light_id"`, `"timestamp"`, `"lux"`, `"motion_detected"`, `"temperature"` |
| `"demographics"` | `"neighborhood"`, `"population"`, `"median_income"`, `"commercial_pct"` |
| `"power_grid_zones"` | `"zone_id"`, `"zone_name"`, `"capacity_kw"`, `"current_load_kw"`, `"latitude"`, `"longitude"` |
| `"weather_enrichment"` | `"date"`, `"season"`, `"temperature"`, `"humidity"`, `"wind_speed"`, `"precipitation"` |

> No `maintenance_requests`, `neighborhoods`, or `suppliers` tables exist.

## PostgreSQL connections

- Always connect via: `psql "service={pg_service}"`. Never use `-h`/`-U`/`-d` directly.
- Credentials come from `~/.pg_service.conf`, set up by the `snowflake-postgres` bundled skill.
- `pg_service` is `manifest.demo.pg_service`, **not** the `PGSERVICE` environment variable.

## Warehouse resilience

- `{PREFIX}_STREETLIGHTS_WH` can be dropped by account-level cleanup jobs.
- If a gate step fails with "warehouse not found": recreate with `CREATE WAREHOUSE IF NOT EXISTS {PREFIX}_STREETLIGHTS_WH ...` and re-grant: `GRANT USAGE ON WAREHOUSE {PREFIX}_STREETLIGHTS_WH TO ROLE KAMESH_DEMOS`.

## Roles

- Use `admin_role` (ACCOUNTADMIN) for DDL: `CREATE WAREHOUSE`, `GRANT`, `CREATE SEMANTIC VIEW`, `CREATE CORTEX SEARCH SERVICE`.
- Use `role` (KAMESH_DEMOS) for DML and verification queries.

## Gate timing

- Gate cache TTL: 1 hour. After expiry it re-verifies live infra state.
- Always pass `--prior-step` to enforce the full step-chain check.
- Cortex Search: wait **1–2 min** after creation for `ACTIVE` status.
- ML Forecast: wait **2–5 min** after `CREATE` for model training to complete.
