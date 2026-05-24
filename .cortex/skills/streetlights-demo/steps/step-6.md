---
name: streetlights-demo-step-6
description: Create Cortex Search service on maintenance records
---

## Gate

```bash
uv run gate --step step-6 --prior-step step-5 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-6 --desc "Creating Cortex Search service" --action start
```

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 6: Create Cortex Search Service

## Why this matters

**Vector/hybrid search for unstructured data** — SQL is great for structured queries ("count faulty lights") but terrible for finding *patterns in text* ("exposed wires", "flickering at night"). Cortex Search indexes text with embeddings and enables semantic similarity search — finding records by meaning, not exact keywords.

**Complementing Semantic Views** — Together, Semantic View (structured SQL) + Cortex Search (unstructured retrieval) give the Intelligence Agent two complementary tools. Some questions need SQL aggregation; others need text similarity. The agent routes to the right tool automatically.

**IDD connection** — The Cortex Search service is another layer of [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14) — declared once in DDL and continuously maintained by Snowflake. The skill file captures the *what*, the platform handles the *how* (embedding generation, index maintenance, refresh cycles).

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

## What we'll do

Create a Cortex Search service that indexes maintenance record descriptions for semantic text search. This enables queries like "find safety hazards" or "flickering light issues."

- Deploy Cortex Search DDL on the maintenance_records table
- Wait for indexing to complete (service becomes ACTIVE)
- Test semantic search capability

> **File**: `snowflake/03_cortex_search.sql` (executed with `PREFIX=<prefix>` template variable)

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> ⚠️ **MANDATORY**: Plan mode is already active. Run the dry-run command and present the output to the user.

Show the execution plan to the user:
```bash
uv run gate --step step-6 --action dry-run
```
Present the output, then ask user to proceed.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a plan summary of what the step will execute. Proceed to Execution only after the user confirms.

## Execution

### Prerequisites

- CLD database exists with tables visible (Step 4 complete)
- Snowflake warehouse exists (from `snowflake/01_setup.sql`)

### Steps

1. Read manifest for database/warehouse names
2. Execute Cortex Search DDL:
   ```bash
   snow sql -f snowflake/03_cortex_search.sql -D "PREFIX=KAMESHS" -c local-oauth --enable-templating STANDARD
   ```
3. Wait for service to become ACTIVE (may take 1-2 minutes)

### Key Details

- Creates a Cortex Search service on maintenance record descriptions
- Enables semantic text search (e.g., "find safety hazards", "flickering lights")
- Service indexes the `description` column from `maintenance_records`

### Verification

- Run `gate.py check_cortex_search_ready`
- Service status must be `ACTIVE`
- Test a sample search query:
  ```bash
  snow cortex search "safety hazard exposed wires" \
    --service MAINTENANCE_SEARCH \
    --columns NEIGHBORHOOD --columns MAINTENANCE_TYPE --columns DESCRIPTION \
    --limit 5 \
    -c {connection} \
    --database {database} \
    --schema PUBLIC
  ```

## What we did

- ✅ Cortex Search service created and indexed
- ✅ Service status: ACTIVE
- ✅ Semantic search verified with test query
- ✅ Gate check: `check_cortex_search_ready` passed

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 6` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~6 — (1 SQL search DDL + 1 bash deploy + 1 wait + 1 bash test query + 2 gate calls without this skill) |
| **Step ICR** | **6** (6 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Mark COMPLETE

```bash
uv run gate --step step-6 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 7: Create Intelligence Agent?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 7` for later resumption.
