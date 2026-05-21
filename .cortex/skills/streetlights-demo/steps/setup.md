---
name: streetlights-demo-setup
description: Initialize the streetlights demo manifest and configuration
---

## Gate

```bash
python3 scripts/gate.py --step setup --action check
```

If BLOCK: stop and inform the user what needs fixing.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
python3 scripts/gate.py --step setup --desc "Initialize Streetlights Demo" --action start
```

# Setup: Initialize Streetlights Demo

## What we'll do

Configure the demo by collecting your Snowflake connection, resource prefix, and city location. This creates the `.streetlights-demo/manifest.toml` that all subsequent steps depend on.

- Detect or ask for Snowflake connection
- Set a resource prefix (all objects will be `${PREFIX}_STREETLIGHTS_*`)
- Auto-detect or ask for city + coordinates for data generation

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Setup"
- Question: "Ready to initialize the streetlights demo configuration?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

1. **Check if `.streetlights-demo/manifest.toml` already exists**
   - If yes: load it, show current config, ask if user wants to reconfigure
   - If no: proceed to create

2. **Ask for demo resource prefix**
   - Use `ask_user_question` to confirm the prefix
   - Explain: "All Snowflake resources will be named `${PREFIX}_STREETLIGHTS_*`"
   - Options: suggest username-based prefix (e.g., "kameshs")

3. **Detect or ask for city**
   - Try auto-detection via IP geolocation
   - If fails: ask user for city name
   - Show detected city + coordinates, ask for confirmation

4. **Ask for Snowflake connection**
   - List available connections: `snow connection list`
   - Ask user to pick one

5. **Warehouse resolution**
   - Check if user's connection has a default warehouse:
     ```sql
     SELECT CURRENT_WAREHOUSE();
     ```
   - If a default warehouse exists: ask user:
     - "Use your current warehouse `<name>` or create a dedicated `${PREFIX}_STREETLIGHTS_WH`?"
     - Options: ["Use existing `<name>`", "Create new `${PREFIX}_STREETLIGHTS_WH`"]
   - If no default warehouse: inform user we'll create `${PREFIX}_STREETLIGHTS_WH`
   - Note: Creating a warehouse requires `CREATE WAREHOUSE` privilege (typically `SYSADMIN`+)

6. **Role and privilege check**
   - Check current role: `SELECT CURRENT_ROLE()`
   - Check if role can create PG instances:
     ```sql
     SHOW GRANTS TO ROLE <current_role>;
     ```
     Look for `CREATE POSTGRES INSTANCE ON ACCOUNT`
   - If insufficient:
     - ⚠️ STOP: inform user that Step 2 (PG instance creation) requires
       `CREATE POSTGRES INSTANCE ON ACCOUNT` privilege (typically `ACCOUNTADMIN`)
     - Ask: "Which role should we use for PG instance creation?"
     - Options: ["ACCOUNTADMIN", "Use current role (may fail)"]
   - Store the chosen role in manifest as `pg_create_role`

7. **Write `.streetlights-demo/manifest.toml`**
   - Create directory if needed
   - Write config with all resolved values:
     ```toml
     schema_version = "1"
     project_name   = "streetlights-demo"

     [project]
     demo_resource_prefix = "<prefix>"

      [snowflake]
      connection = "<connection>"
      role       = "<pg_create_role>"

      [demo]
      database     = "<PREFIX>_STREETLIGHTS"
      cld_database = "<PREFIX>_STREETLIGHTS_CLD"
      warehouse    = "<existing_or_new_wh_name>"
      pg_instance  = "<prefix>_streetlights"
      pg_service   = "<prefix>_streetlights"
      city         = "<city>"
      center_lat   = <lat>
      center_lng   = <lng>
     ```

> **Note**: Existing instances keep their current names; only new setups use the shorter naming convention.

8. **Verify setup**
   - Run `gate.py check_manifest_exists`
   - Run `gate.py check_snowflake_connection` — validates the chosen connection works
   - If connection check fails: STOP, ask user to re-select or fix their `snow` config
   - Show summary table of all configured values

## What we did

- ✅ Manifest created at `.streetlights-demo/manifest.toml`
- ✅ Resource prefix, connection, and city configured
- ✅ Gate check: `check_manifest_exists` passed

## Mark COMPLETE

```bash
python3 scripts/gate.py --step setup --action complete
```

## Connecting to PostgreSQL

After Step 2 creates your PG instance, the `$snowflake-postgres` skill saves
connection details to `~/.pg_service.conf` + `~/.pgpass` (standard PostgreSQL files).

To use `psql` without typing host/user/password every time, export these env vars:

```bash
export PGSERVICE="<pg_service>"       # from manifest — matches ~/.pg_service.conf entry
export PGDATABASE="streetlights"
```

Then connect with just:

```bash
psql "service=$PGSERVICE connect_timeout=10"
```

**How to load these automatically** (pick one):

| Method | Setup |
|--------|-------|
| **direnv** (recommended) | `brew install direnv` + add hook to shell. The `.envrc` in this project loads them automatically. |
| **source manually** | Add to your `~/.bashrc` / `~/.zshrc`: `source /path/to/project/.envrc` |
| **export directly** | Copy the two `export` lines above into your shell session |
| **dotenv** | Create a `.env` file with `PGSERVICE=<value>` and source it with your preferred tool |

> **Note**: You do NOT need `PGHOST`, `PGUSER`, or `PGPASSWORD` env vars.
> The `PGSERVICE` var tells psql to look up everything from `~/.pg_service.conf` + `~/.pgpass`.

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 1: Generate Synthetic Data?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 1` for later resumption.
