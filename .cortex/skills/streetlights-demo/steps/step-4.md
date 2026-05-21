---
name: streetlights-demo-step-4
description: Create Catalog Integration and CLD database
---

## Gate

```bash
python3 scripts/gate.py --step step-4 --prior-step step-3 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
python3 scripts/gate.py --step step-4 --desc "Catalog Integration + CLD" --action start
```

# Step 4: Catalog Integration + CLD

## What we'll do

Create the Snowflake catalog integration pointing to the Postgres instance, then create a Catalog-Linked Database (CLD) that auto-syncs Iceberg tables. This is a **billable action**.

- Create catalog integration with `CATALOG_SOURCE = SNOWFLAKE_POSTGRES`
- Create CLD database linked to the catalog
- Wait for table propagation (~30 seconds)

## ⚠️ Proceed?

> **⚠️ Billable**: This creates a Catalog Integration and enables continuous sync. Credits consumed while running.

Use `ask_user_question` to confirm:
- Header: "Step 4"
- Question: "Ready to create the Catalog Integration and CLD? (billable — enables continuous sync)"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Pre-flight

- Run `gate.py check_pg_managed_storage` — CLD ONLY works with managed storage

> **Connection**: Read from manifest `[snowflake].connection`. Do NOT re-ask the user.

### Steps

Route to `$snowflake-postgres` pg_lake to:

> **Routing**: Invoke `$snowflake-postgres` via the `skill` tool (bundled system skill). Do NOT run SQL directly for CLD operations.

1. Create catalog integration for the PG instance:
   ```sql
   CREATE CATALOG INTEGRATION {prefix}_streetlights_catalog_int
     CATALOG_SOURCE = SNOWFLAKE_POSTGRES
     POSTGRES_INSTANCE_NAME = '{pg_instance}'
     ENABLED = TRUE;
   ```

2. Create CLD database: `{cld_database}` with `CATALOG_SOURCE = SNOWFLAKE_POSTGRES`:
   ```sql
   CREATE DATABASE {cld_database}
     CATALOG = '{prefix}_streetlights_catalog_int'
     LINKED_CATALOG = TRUE;
   ```

### CLD Propagation

After CLD creation, tables take ~30 seconds to appear.
- Wait 30s, then verify: `SHOW TABLES IN DATABASE {cld_database}`
- If tables not visible after 3 retries (30s each): STOP and report issue

### Verification

- Run `gate.py check_cld_healthy`
- Show table list from CLD to user
- Confirm all 7 tables are visible

## What we did

- ✅ Catalog integration created
- ✅ CLD database created and linked
- ✅ All 7 tables propagated and visible
- ✅ Gate check: `check_cld_healthy` passed

## Mark COMPLETE

```bash
python3 scripts/gate.py --step step-4 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 5: Create Semantic View?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 5` for later resumption.
