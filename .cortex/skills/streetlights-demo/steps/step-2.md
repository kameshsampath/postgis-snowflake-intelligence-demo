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

> **Note**: No SQL file — network policy creation and PG instance operations use inline `snow sql` calls.

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

### Create Demo Network Policy

After instance is ready, create a dedicated network policy for this demo:

1. **Detect current IP** (always mask last two octets in display — show `xxx.xxx.*.*` format)

2. **Create network rule**:
   ```sql
   CREATE OR REPLACE NETWORK RULE {PREFIX}_STREETLIGHTS_HOME_RULE
     TYPE = IPV4
     MODE = POSTGRES_INGRESS
     VALUE_LIST = ('{current_ip}/32')
     COMMENT = 'Home IP for streetlights demo Postgres access';
   ```

3. **Create network policy**:
   ```sql
   CREATE OR REPLACE NETWORK POLICY {PREFIX}_STREETLIGHTS_INGRESS
     ALLOWED_NETWORK_RULE_LIST = ('{DATABASE}.NETWORKS.{PREFIX}_STREETLIGHTS_HOME_RULE')
     COMMENT = 'Streetlights demo Postgres ingress policy';
   ```
   Note: The network rule should be created in a NETWORKS schema in the main database. Create the schema if needed: `CREATE SCHEMA IF NOT EXISTS {database}.NETWORKS;`
   And the network rule should be `{database}.NETWORKS.{PREFIX}_STREETLIGHTS_HOME_RULE`.

4. **Attach to PG instance**:
   ```sql
   ALTER POSTGRES INSTANCE {pg_instance} SET NETWORK_POLICY = {PREFIX}_STREETLIGHTS_INGRESS;
   ```

5. **Persist in manifest**: Write `pg_network_policy = "{PREFIX}_STREETLIGHTS_INGRESS"` to manifest.

> ⚠️ **IP display**: Always show IPs in masked form (`xxx.xxx.*.*`). Never display full IP in output.

### Verification

- Run `uv run gate --step step-2 --action check` — this internally verifies PG reachability and managed storage
- Show connection details to user

## What we did

- ✅ Snowflake Postgres instance created (or reused) with managed storage
- ✅ Database `streetlights` created on instance
- ✅ Gate check passed (PG reachable + managed storage confirmed)

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 2` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~7 — (2 SQL param checks + 1 PG create + 3 SQL network ops + 1 verification without this skill) |
| **Step ICR** | **7** (7 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

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
