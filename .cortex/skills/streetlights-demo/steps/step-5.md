---
name: streetlights-demo-step-5
description: Create Semantic View over CLD tables
---

## Gate

```bash
uv run gate --step step-5 --prior-step step-4 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-5 --desc "Creating Semantic View" --action start
```

# Step 5: Create Semantic View

## Why this matters

**Semantic Views as AI's "query plan"** — A Semantic View is structured metadata that tells Cortex Analyst *how* to translate natural language into SQL. It defines dimensions (columns to group by), measures (what to aggregate), and filters (valid WHERE clauses). Without it, the AI would need to guess table relationships and column meanings.

**NL→SQL accuracy** — The semantic layer eliminates ambiguity. When a user asks "how many faulty lights?", the Semantic View tells Analyst exactly which table, which column (`status`), and which value (`'faulty'`) to use — no hallucination possible.

**IDD connection** — The Semantic View is [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c) applied to analytics: you declare the *meaning* of your data once, and every future natural language query benefits from that intent. It's a reusable contract between data and AI.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

---

**STOP** — Use `ask_user_question` to confirm:
- Header: "Step 5"
- Question: "Ready to proceed with Semantic View creation? (enables NL→SQL via Cortex Analyst)"
- Options: ["Yes, proceed", "Skip this step"]

---

## What we'll do

Create a Semantic View over the CLD tables that defines dimensions, measures, and filters for natural language querying via Cortex Analyst.

- Deploy the semantic view DDL referencing CLD tables
- Validate the view was created and is queryable
- This enables structured SQL generation from natural language

> **File**: `snowflake/02_semantic_view.sql` (executed with `PREFIX=<prefix>` template variable)

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> **Note**: Enter plan mode before presenting the dry-run output (per SKILL.md global dry-run rule).

Show the execution plan to the user:
```bash
uv run gate --step step-5 --action dry-run
```
Present the output, then ask user to proceed.

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 5"
- Question: "Ready to create the Semantic View for natural language analytics?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- CLD database exists and tables are visible (Step 4 complete)

### Steps

1. Read manifest for database/warehouse names
2. Execute Semantic View DDL:
   ```bash
   snow sql -f snowflake/02_semantic_view.sql
   ```
3. Verify the Semantic View was created successfully

### Key Details

- The Semantic View references CLD tables with **quoted lowercase identifiers**
  (e.g., `"streetlights"."street_lights"`) because CLD preserves PostgreSQL casing
- Geography columns use `ST_MAKEPOINT(longitude, latitude)` for spatial reconstruction
- Dimensions, measures, and filters are defined for natural language querying

### Verification

Run the gate check (validates existence AND YAML primary_key column format):
```bash
uv run gate --step step-5 --action check
```
- **PASS** = view exists + all `primary_key.columns` are unquoted identifiers (e.g. `ID`, not `'"id"'`)
- **BLOCK** = view missing, OR primary_key columns contain double-quote wrappers — redeploy `02_semantic_view.sql`

Show the Semantic View definition to user:
```sql
SHOW SEMANTIC VIEWS IN DATABASE {database};
```

## What we did

- ✅ Semantic View created on CLD tables
- ✅ Quoted lowercase identifiers preserved for CLD compatibility
- ✅ Gate check: semantic view exists and YAML primary_key columns are valid unquoted identifiers

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 5` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~7 — (1 SQL semantic view + 1 bash deploy + 3 SQL verification queries + 2 gate calls without this skill) |
| **Step ICR** | **7** (7 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Mark COMPLETE

```bash
uv run gate --step step-5 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 6: Create Cortex Search Service?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 6` for later resumption.
