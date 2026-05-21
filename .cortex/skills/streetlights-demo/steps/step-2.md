---
name: streetlights-demo-step-2
description: Create or reuse Snowflake Postgres instance with managed storage
---

# Step 2: Snowflake Postgres Instance

## What we'll do

Create a Snowflake Postgres instance with managed storage (required for CLD). This is a **billable action** — the instance consumes credits while running.

- Verify account parameters are enabled
- Create (or reuse) a Postgres instance with managed storage
- Create the `streetlights` database on the instance

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 2"
- Question: "Ready to create a Snowflake Postgres instance? (billable — credits consumed while running)"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Pre-flight Checks

1. **Check account parameters**:
   ```sql
   SHOW PARAMETERS LIKE 'ENABLE_SNOWFLAKE_POSTGRES' IN ACCOUNT;
   SHOW PARAMETERS LIKE 'ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME' IN ACCOUNT;
   ```
   If not enabled: STOP — inform user these params must be enabled by account admin.

2. **Check if instance already exists**:
   ```sql
   SHOW POSTGRES INSTANCES LIKE '{pg_instance}';
   ```
   - If exists: ask user: "Instance `{pg_instance}` already exists. Reuse it?"
     - If reuse AND demo database exists: "Database `streetlights` exists on this instance. Drop it for a clean start?"
   - If not exists: proceed to create

### Create Instance

Route to `$snowflake-postgres` to create instance:
- Instance name: from manifest `pg_instance`
- **Must use managed storage** (required for CLD)
- Create database: `streetlights`

### Verification

- Run `gate.py check_pg_reachable`
- Run `gate.py check_pg_managed_storage`
- Show connection details to user

## What we did

- ✅ Snowflake Postgres instance created (or reused) with managed storage
- ✅ Database `streetlights` created on instance
- ✅ Gate checks: `check_pg_reachable` and `check_pg_managed_storage` passed
