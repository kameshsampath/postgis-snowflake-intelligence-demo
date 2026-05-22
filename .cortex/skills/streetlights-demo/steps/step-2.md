---
name: streetlights-demo-step-2
description: Create or reuse Snowflake Postgres instance with managed storage
---

## Gate

```bash
uv run gate --step step-2 --prior-step step-1 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-2 --desc "Creating Snowflake Postgres instance" --action start
```

# Step 2: Snowflake Postgres Instance

## What we'll do

Create a Snowflake Postgres instance with managed storage (required for CLD). This is a **billable action** — the instance consumes credits while running.

- Verify account parameters are enabled
- Create (or reuse) a Postgres instance with managed storage
- Create the `streetlights` database on the instance

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

Show the execution plan to the user:
```bash
uv run gate --step step-2 --action dry-run
```
Present the output, then ask user to proceed.

## ⚠️ Proceed?

> **⚠️ Billable**: This creates a Snowflake Postgres instance. Credits consumed while running.

Use `ask_user_question` to confirm:
- Header: "Step 2"
- Question: "Ready to create a Snowflake Postgres instance? (billable — credits consumed while running)"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Pre-flight Checks

1. **Validate Snowflake connection**:
   - Run `uv run gate --step step-2 --prior-step step-1 --action check`
   - If BLOCK: STOP — connection in manifest is invalid, run `$streetlights-demo setup` to reconfigure

> **Connection**: Read from manifest `[snowflake].connection`. Do NOT re-ask the user.

2. **Check account parameters**:
   ```sql
   SHOW PARAMETERS LIKE 'ENABLE_SNOWFLAKE_POSTGRES' IN ACCOUNT;
   SHOW PARAMETERS LIKE 'ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME' IN ACCOUNT;
   ```
   If not enabled: STOP — inform user these params must be enabled by account admin.

3. **Check if instance already exists**:
   ```sql
   SHOW POSTGRES INSTANCES LIKE '{pg_instance}';
   ```
   - If exists: ask user: "Instance `{pg_instance}` already exists. Reuse it?"
     - If reuse AND demo database exists: "Database `streetlights` exists on this instance. Drop it for a clean start?"
   - If not exists: proceed to create

### Create Instance

Route to `$snowflake-postgres` to create instance:

> **Routing**: Invoke `$snowflake-postgres` via the `skill` tool (bundled system skill). Do NOT run SQL directly for PG instance operations.

- Instance name: from manifest `pg_instance`
- **Must use managed storage** (required for CLD)
- **Use role**: from manifest `admin_role` (typically ACCOUNTADMIN — set during setup)
  - Pass `--use-role <admin_role>` to `pg_connect.py --create`
- Create database: `streetlights`

### Network Access Check

After instance is created (or reused), verify network connectivity:

- The gate check (`uv run gate --step step-2 --prior-step step-1 --action check`) verifies PG reachability internally.
- If **IP MISMATCH** detected:
  - Show current IP vs allowed IPs
  - Use `ask_user_question`: "Your IP ({current_ip}) isn't in the network policy. Update it?"
    - Options: ["Yes, update network policy", "No, I'll fix it manually"]
  - If yes: Route to `$snowflake-postgres` to update the network policy with the new IP
- This check runs on **every step that needs PG access** (steps 3, 4) — not just step 2.
  Users commonly switch WiFi/VPN between steps.

### Verification

- Run `uv run gate --step step-2 --action check` — this internally verifies PG reachability and managed storage
- Show connection details to user

## What we did

- ✅ Snowflake Postgres instance created (or reused) with managed storage
- ✅ Database `streetlights` created on instance
- ✅ Gate check passed (PG reachable + managed storage confirmed)

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

## Mark COMPLETE

```bash
uv run gate --step step-2 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 3: Create Schema + Load Data?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 3` for later resumption.
