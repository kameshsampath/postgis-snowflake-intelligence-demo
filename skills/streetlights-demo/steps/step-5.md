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

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 5: Create Semantic View

## Why this matters

**What is a Semantic View?** — A Semantic View is a named metadata layer that sits between natural language and raw SQL tables. Unlike a regular database view (which reshapes data), a Semantic View *annotates* data with meaning: which columns are dimensions (group by), which are measures (aggregate), how tables join, and what language humans use (synonyms). It is the schema's vocabulary, not a query.

**Dimensions, measures, filters** — The three building blocks Cortex Analyst uses when parsing a question. Dimensions are categorical attributes like `neighborhood`, `status`, `light_type`. Measures are numeric computations like `COUNT(faulty)`, `SUM(kwh)`. Filters are pre-approved WHERE clause values. When a user asks a question, Analyst looks up the answer in this lookup table of intent — it does not guess.

**Semantic layer vs raw SQL** — Without a semantic layer, an AI model would need to inspect raw column names, infer what `status = 'faulty'` means, and guess which tables to join. With a Semantic View, those decisions are declared once and reused by every future query. The AI is *reading* the intent you already encoded.

**NL→SQL accuracy** — The semantic layer eliminates ambiguity. When a user asks "how many faulty lights?", the Semantic View tells Analyst exactly which table, which column (`status`), and which value (`'faulty'`) to use — no hallucination possible.

**IDD connection** — The Semantic View is [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c) applied to analytics: you declare the *meaning* of your data once, and every future natural language query benefits from that intent. It's a reusable contract between data and AI.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

## What we'll do

Create a Semantic View over the CLD tables that defines dimensions, measures, and filters for natural language querying via Cortex Analyst.

- Deploy the semantic view DDL referencing CLD tables
- Validate the view was created and is queryable
- This enables structured SQL generation from natural language

> **File**: `snowflake/02_semantic_view.sql` (executed with `PREFIX=<prefix>` template variable)

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> ⚠️ **MANDATORY**: Plan mode is already active. Run the dry-run command and present the output to the user.

Show the execution plan to the user:
```bash
uv run gate --step step-5 --action dry-run
```
Present the output, then ask user to proceed.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a plan summary of what the step will execute. Proceed to Execution only after the user confirms.

## Execution

### Prerequisites

Verify CLD tables are present before deploying the Semantic View (which references them as source tables):

```sql
SHOW TABLES IN DATABASE {cld_database};
```

- 7 tables → proceed
- < 7 tables → **STOP**: "CLD propagation not yet complete — wait 30s and retry. If 0 tables, re-run Step 4."

Do not self-heal. The Semantic View deployment will fail silently with wrong references if the CLD is incomplete.

### Steps

1. Read manifest for database, warehouse, role, and connection names

2. Create main database and grant access:

   > **Source**: `snowflake/01_setup.sql` — warehouse creation, database creation, and role grants

   ```bash
   snow sql -f snowflake/01_setup.sql \
     -D "PREFIX={manifest.demo.prefix.upper()}" \
     -D "ROLE={manifest.snowflake.role}" \
     -c {manifest.snowflake.connection} \
     --enable-templating STANDARD --format json
   ```

   This creates `{PREFIX}_STREETLIGHTS` database and grants the working role permission to create Semantic Views, Cortex Search services, and Agents. Safe to re-run — all statements use `IF NOT EXISTS`.

3. Deploy Semantic View DDL:

   > **Source**: `snowflake/02_semantic_view.sql` — Semantic View over all 7 CLD tables

   ```bash
   snow sql -f snowflake/02_semantic_view.sql \
     -D "PREFIX={manifest.demo.prefix.upper()}" \
     -c {manifest.snowflake.connection} \
     --enable-templating STANDARD --format json
   ```

4. Verify the Semantic View was created successfully

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
