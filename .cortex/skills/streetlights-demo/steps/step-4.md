---
name: streetlights-demo-step-4
description: Create Catalog Integration and CLD database
---

## Gate

```bash
uv run gate --step step-4 --prior-step step-3 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-4 --desc "Creating Catalog Integration + CLD" --action start
```

# Step 4: Catalog Integration + CLD

## Why this matters

**Catalog Integration** — This tells Snowflake: "this Postgres instance is an Iceberg catalog — poll its metadata for table changes." It's the bridge that makes PG-managed Iceberg tables visible to Snowflake without any data copying.

**CLD (Catalog-Linked Database)** — A read-only Snowflake database that *auto-discovers* all current and future Iceberg tables from the catalog. You don't register tables individually — the CLD watches the catalog and surfaces whatever it finds. Add a table in PG → it appears in Snowflake automatically.

**IDD connection** — The CLD is the [Ghost in the Machine](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2) — a live, self-updating data contract that bridges two systems without human intervention. Combined with [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c), the entire setup (catalog integration + CLD + access grants) is declared as intent in this skill file and executed by CoCo.

---

**STOP** — Use `ask_user_question` to confirm:
- Header: "Step 4"
- Question: "Ready to proceed with catalog integration? (billable — enables continuous Iceberg sync)"
- Options: ["Yes, proceed", "Skip this step"]

---

## What we'll do

Create the Snowflake catalog integration pointing to the Postgres instance, then create a Catalog-Linked Database (CLD) that auto-syncs Iceberg tables. This is a **billable action**.

- Create catalog integration with `CATALOG_SOURCE = SNOWFLAKE_POSTGRES`
- Create CLD database linked to the catalog
- Wait for table propagation (~30 seconds)

## Dry-Run

Show the execution plan to the user:
```bash
uv run gate --step step-4 --action dry-run
```
Present the output, then ask user to proceed.

## Proceed?

> ⚠️ **Billable**: This creates a Catalog Integration and enables continuous sync. Credits consumed while running.

Use `ask_user_question` to confirm:
- Header: "Step 4"
- Question: "Ready to create the Catalog Integration and CLD? (billable — enables continuous sync)"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Pre-flight

- Run `uv run gate --step step-4 --prior-step step-3 --action check` — internally verifies PG managed storage (CLD ONLY works with managed storage)

> **Connection**: Read from manifest `[snowflake].connection`. Do NOT re-ask the user.

### Access Control (CRITICAL)

The catalog integration and CLD require elevated privileges. The strategy is:
1. Determine the user's default role
2. Create resources as `ACCOUNTADMIN`
3. Grant access on created resources back to the user's default role

```sql
-- Capture user's default role first
SELECT CURRENT_ROLE() AS user_role;
```

Then switch to ACCOUNTADMIN for creation:
```sql
USE ROLE ACCOUNTADMIN;
```

After creating the catalog integration and CLD (see Steps below), grant access back:
```sql
-- Grant integration access
GRANT USAGE ON INTEGRATION {prefix}_streetlights_catalog_int TO ROLE {user_default_role};

-- Grant CLD database access
GRANT USAGE ON DATABASE {cld_database} TO ROLE {user_default_role};
GRANT USAGE ON SCHEMA {cld_database}.streetlights TO ROLE {user_default_role};
GRANT SELECT ON ALL TABLES IN SCHEMA {cld_database}.streetlights TO ROLE {user_default_role};
```

Finally switch back:
```sql
USE ROLE {user_default_role};
```

### Steps

Route to `$snowflake-postgres` pg_lake to:

> **Routing**: Invoke `$snowflake-postgres` via the `skill` tool (bundled system skill). Do NOT run SQL directly for CLD operations.

1. Create catalog integration for the PG instance (as ACCOUNTADMIN):

   > ⚠️ **`POSTGRES_INSTANCE` must be UPPERCASE** — Snowflake normalizes unquoted identifiers to uppercase. If your PG instance name is `my_pg`, pass `'MY_PG'` here, otherwise the catalog won't resolve.

   > ⚠️ **`CATALOG_NAMESPACE` = lowercase** — This must match the PG schema name exactly (`'streetlights'`). It's a string literal, so it stays lowercase.

   ```sql
   CREATE OR REPLACE CATALOG INTEGRATION {prefix}_streetlights_catalog_int
     CATALOG_SOURCE = SNOWFLAKE_POSTGRES
     TABLE_FORMAT = ICEBERG
     CATALOG_NAMESPACE = 'streetlights'
     REST_CONFIG = (
       POSTGRES_INSTANCE = '{pg_instance}'
       CATALOG_NAME = 'postgres'
       ACCESS_DELEGATION_MODE = VENDED_CREDENTIALS
     )
     ENABLED = TRUE;
   ```

2. Verify the integration was created correctly:
   ```sql
   DESCRIBE CATALOG INTEGRATION {prefix}_streetlights_catalog_int;
   ```
   Confirm: `ENABLED = true`, `CATALOG_NAMESPACE = streetlights`, `REST_CONFIG` contains `POSTGRES_INSTANCE`.

3. Create CLD database (as ACCOUNTADMIN):

   > ⚠️ **`LINKED_CATALOG = (...)`** — This uses nested block syntax with parentheses, not `= TRUE` or a simple value. The inner `CATALOG =` references the integration name (unquoted identifier).

   ```sql
   CREATE DATABASE {cld_database}
     LINKED_CATALOG = (
       CATALOG = {prefix}_streetlights_catalog_int
       ALLOWED_WRITE_OPERATIONS = NONE
     );
   ```

   > Ref: https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-pg_lake#catalog-linked-databases

4. Grant access to user's default role:

   > ⚠️ **Access control** — Resources created as ACCOUNTADMIN are invisible to other roles until explicitly granted. Always grant back to the user's working role immediately.

   ```sql
   GRANT USAGE ON INTEGRATION {prefix}_streetlights_catalog_int TO ROLE {user_default_role};
   GRANT USAGE ON DATABASE {cld_database} TO ROLE {user_default_role};
   GRANT USAGE ON SCHEMA {cld_database}.streetlights TO ROLE {user_default_role};
   GRANT SELECT ON ALL TABLES IN SCHEMA {cld_database}.streetlights TO ROLE {user_default_role};
   USE ROLE {user_default_role};
   ```

### CLD Propagation

> **Propagation delay** — Tables take ~30 seconds to appear after CLD creation (one `REFRESH_INTERVAL_SECONDS` cycle). Do NOT assume failure immediately — always wait and retry.

After CLD creation, tables take ~30 seconds to appear (one `REFRESH_INTERVAL_SECONDS` cycle).
- Wait 35s, then verify: `SHOW TABLES IN DATABASE {cld_database}`
- If tables not visible after 3 retries (30s each): STOP and report issue
- Tables will appear under schema `streetlights` (matching `CATALOG_NAMESPACE`)

### Verification

Run these checks in order:

1. **Catalog integration status**:
   ```sql
   DESCRIBE CATALOG INTEGRATION {prefix}_streetlights_catalog_int;
   ```
   Confirm: `ENABLED = true`, `CATALOG_NAMESPACE = streetlights`, `REST_CONFIG` contains `POSTGRES_INSTANCE`.

2. **CLD status**:
   ```sql
   SELECT SYSTEM$CATALOG_LINKED_DATABASE_STATUS('{cld_database}');
   ```
   Confirm: status is `ACTIVE` or `READY`.

3. **Table visibility**:
   ```sql
   SHOW TABLES IN DATABASE {cld_database};
   ```
   Confirm: all 7 tables are listed under schema `streetlights`.

4. **Data check** (confirms end-to-end flow):
   ```sql
   SELECT COUNT(*) FROM {cld_database}.streetlights.street_lights;
   ```
   Confirm: row count matches what was loaded in Step 3 (~500 rows).

5. **Gate health check**:
   - Run `gate.py check_cld_healthy`
   - Show table list from CLD to user
   - Confirm all 7 tables are visible and queryable

## What we did

- ✅ Catalog integration created
- ✅ CLD database created and linked
- ✅ All 7 tables propagated and visible
- ✅ Gate check: `check_cld_healthy` passed

## Mark COMPLETE

```bash
uv run gate --step step-4 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 5: Create Semantic View?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 5` for later resumption.
