---
name: streetlights-demo-step-7
description: Create Intelligence Agent with Semantic View and Cortex Search
---

## Gate

```bash
uv run gate --step step-7 --prior-step step-6 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-7 --desc "Creating Intelligence Agent" --action start
```

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 7: Create Intelligence Agent

## Why this matters

**What is an Intelligence Agent?** — A Cortex Agent is an LLM given named, described tools. It reads your question, reasons about which tool best answers it, calls that tool, interprets the result, and synthesizes a response. The agent does not "know" your data — it knows how to *route* questions to the right tool. It is an orchestrator, not an oracle.

**FROM SPECIFICATION as declarative orchestration** — Instead of writing Python to chain tool calls, you write YAML inside a DDL statement. The spec declares routing instructions (when to use each tool), tool configurations (which semantic view, which search service), and response format. The platform handles all LLM calls, tool invocations, and response synthesis. Infrastructure as intent, applied to AI orchestration.

**Tool-use architecture** — The Intelligence Agent doesn't answer questions directly. It *routes* them: Cortex Analyst for structured SQL queries, or Cortex Search for text retrieval. This is a tool-use pattern — the agent is a coordinator that composes multi-tool answers from a single natural language question.

**Composing multi-source answers** — A question like "Tell me about maintenance issues in the busiest neighborhood" requires *both* SQL (to find the busiest neighborhood) and text search (to find maintenance records). The agent decomposes the question, routes sub-parts to the right tools, and synthesizes a unified answer.

**IDD connection** — The agent's `FROM SPECIFICATION` block is the purest form of [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c) — you declare routing rules, sample questions, and tool configurations as intent. The platform handles LLM orchestration, tool invocation, and response synthesis.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

## What we'll do

Create the Cortex Intelligence Agent that combines Semantic View (structured analytics) with Cortex Search (text retrieval) into a single natural language interface.

- Deploy Agent DDL with full FROM SPECIFICATION (orchestration rules, tools, sample questions)
- Verify the agent routes queries correctly
- Test both structured and unstructured queries
- Register agent with `SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT` so it appears in the Snowflake Intelligence UI

> **File**: `snowflake/04_intelligence_agent.sql` (executed with `PREFIX=<prefix>`, `ROLE=<role>`, `CURRENCY_SYMBOL=<symbol>` template variables)

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

> ⚠️ **MANDATORY**: Plan mode is already active. Run the dry-run command and present the output to the user.

Show the execution plan to the user:
```bash
uv run gate --step step-7 --action dry-run
```
Present the output, then ask user to proceed.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a plan summary of what the step will execute. Proceed to Execution only after the user confirms.

## Execution

### Prerequisites

Verify both agent tools are fully ready before deploying the agent:

```sql
-- Check Semantic View exists (step-5)
SHOW SEMANTIC VIEWS IN DATABASE {database};

-- Check Cortex Search service exists and is ACTIVE (step-6)
SHOW CORTEX SEARCH SERVICES IN DATABASE {database};
```

- Semantic View missing → **STOP**: "Re-run Step 5."
- Search service missing → **STOP**: "Re-run Step 6."
- Search service `STATUS = 'BUILDING'` → wait 60s and recheck (indexing in progress, not an error).

Do not deploy the agent until both tools are confirmed ready. An agent created against a non-ACTIVE search service will have broken tool routing.

### Steps

1. Read manifest for database/warehouse/role names
2. Execute Agent DDL + Grant Access:
   ```bash
   snow sql -f snowflake/04_intelligence_agent.sql \
     -D "PREFIX={manifest.demo.prefix.upper()}" \
     -D "ROLE={manifest.snowflake.role}" \
     -D "CURRENCY_SYMBOL={manifest.demo.currency_symbol}" \
     -c {manifest.snowflake.connection} \
     --enable-templating STANDARD
   ```
3. Verify agent responds to a test query
4. Verify grants were applied:
   ```sql
   SHOW GRANTS TO ROLE {manifest.snowflake.role};
   ```
   Expect `USAGE` on `STREETLIGHTS_AGENT`, `SELECT` on `STREETLIGHTS_SEMANTIC_VIEW`, `USAGE` on `MAINTENANCE_SEARCH`, `USAGE` on `STREETLIGHTS_WH`.

### Key Details

- The Intelligence Agent combines TWO tools:
  - **StreetlightsAnalyst** (Cortex Analyst) — for structured SQL queries (counts, aggregations, rankings)
  - **MaintenanceSearch** (Cortex Search) — for unstructured text retrieval (descriptions, issues)
- Orchestration instructions control routing between tools
- Map links are auto-generated when results include lat/lng columns
- **Intelligence registration** — accounts with `SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT` show only explicitly registered agents in the UI; `04_intelligence_agent.sql` handles this automatically

> ⚠️ **FORBIDDEN** — These patterns do not exist and will error immediately:
> - `snow cortex agent` — this CLI subcommand does not exist
> - `SNOWFLAKE.CORTEX.COMPLETE(model, ARRAY)` for agent queries — COMPLETE is for LLM text generation only, not Intelligence Agent tool routing; produces `COMPLETE$V6` argument type errors

### Verification

- Run `gate.py check_agent_accessible`
- Test with a structured query:
  ```
  "How many street lights are currently faulty?"
  ```
- Test with a text search query:
  ```
  "Find maintenance records about exposed wires"
  ```
- Verify routing: structured → Analyst, text → Search

## What we did

- ✅ Intelligence Agent created with FROM SPECIFICATION
- ✅ Orchestration routing rules configured (Analyst vs Search)
- ✅ Map link generation enabled for lat/lng results
- ✅ Grant Access applied: configured role can open the agent in Snowflake Intelligence
- ✅ Agent registered with `SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT` — visible in Snowflake Intelligence UI
- ✅ Gate check: `check_agent_accessible` passed

### Try it in Snowflake Intelligence (CoWork)

Open **Snowflake Intelligence** in your Snowflake account, select the `STREETLIGHTS_AGENT`, and try these questions:

**Structured queries** (routes to Cortex Analyst):
- "How many street lights are currently faulty?"
- "Which neighborhoods have the highest energy consumption?"
- "Show me the top 5 neighborhoods by maintenance frequency"
- "What is the average repair cost by maintenance type?"
- "Predict energy consumption for the next 30 days"

**Text search queries** (routes to Cortex Search):
- "Find maintenance records about exposed wires or sparking"
- "What does the maintenance history say about pole integrity?"
- "Show me reports mentioning water damage"

**Hybrid queries** (triggers both tools):
- "Tell me about maintenance issues in the busiest neighborhood"
- "What's the repair status for flickering light reports?"

> **Tip**: The agent auto-generates OpenStreetMap links when results include coordinates. Try: "Show me faulty lights in [your neighborhood]"

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 7` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~8 — (1 SQL agent DDL + 1 bash deploy + 1 SQL grant verify + 3 bash/SQL test queries + 2 gate calls without this skill) |
| **Step ICR** | **8** (8 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Live Demo

> ⚠️ **MANDATORY**: Run these queries after step completion to show the agent's tools working end-to-end. Present each question, run it, and show the formatted response.

> ⚠️ **FORBIDDEN**:
> - `snow cortex agent` — does not exist
> - `SNOWFLAKE.CORTEX.COMPLETE` for agent routing — use only the patterns below

> **Source**: `snowflake/04_intelligence_agent.sql` — agent tool configurations

### Query 1 — Cortex Search (unstructured) — via SQL

Test the **MaintenanceSearch** tool directly. This confirms the search index is working.

**Question**: "Find maintenance records about sparking or exposed wires"

```sql
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
  '{PREFIX}_STREETLIGHTS.PUBLIC.MAINTENANCE_SEARCH',
  PARSE_JSON('{
    "query": "sparking or exposed wires",
    "columns": ["neighborhood", "maintenance_type", "description"],
    "limit": 5
  }')
);
```

Expected: JSON with 3–5 maintenance records describing electrical hazards.
Show results as a short list with `description`, `maintenance_type`, `neighborhood`.

### Query 2 — Full Agent (structured + unstructured) — via Snowflake Intelligence UI

The Intelligence Agent is designed for the Snowflake Intelligence UI. Direct the user to:

1. Open **Snowflake Intelligence** in your Snowflake account
2. Select agent: `{PREFIX}_STREETLIGHTS.PUBLIC.STREETLIGHTS_AGENT`
3. Ask: **"How many street lights are faulty by neighborhood?"**
   - Routes to: `StreetlightsAnalyst` (Cortex Analyst → SQL → Semantic View)
   - Expected output: table with `neighborhood`, `faulty_count`, sorted descending
4. Ask: **"Which neighborhood has the most faulty lights, and where are they located?"**
   - Routes to: `StreetlightsAnalyst` first (finds top neighborhood), then returns lat/lng
   - Expected output: neighborhood name + OSM map links
   - Format: `[POLE-XXXXX](https://www.openstreetmap.org/?mlat=...&mlon=...&zoom=16)`

> **Note**: The agent infers from orchestration instructions that OSM map links are appropriate — do NOT explicitly say "with map links" in your question.

Present all query results to the user before marking COMPLETE.

## Mark COMPLETE

```bash
uv run gate --step step-7 --action complete
```

## Infrastructure Phase Complete — Opt-In Gate

> ⚠️ **MANDATORY**: After presenting "What we did" and marking step-7 COMPLETE, present the
> two-phase framing and ask the user whether to continue to the App phase.

The Infrastructure phase (setup + steps 1–7) is now complete. The Intelligence Agent is live
and queryable in Snowflake Intelligence.

Use the `ask_user_question` tool:
- Header: `"Continue?"`
- Question: `"The Infrastructure phase is complete (setup + steps 1–7). Your Intelligence Agent is live and queryable. Continue to the App phase (ML Forecast + Streamlit app + Validation)?"`
- Options:
  - `"Continue → App phase (steps 8–10)"`
  - `"Stop here — show Infrastructure summary"`

### If "Stop here":

Present the Infrastructure IDD summary:

```
## IDD Summary — Infrastructure Phase

| Step | Invocation | Trad. Ops (baseline) | Step ICR |
|------|------------|----------------------|----------|
| 1 — Generate Data   | `$streetlights-demo step 1` | 6  | 6  |
| 2 — PG Instance     | `$streetlights-demo step 2` | 12 | 12 |
| 3 — Schema + Load   | `$streetlights-demo step 3` | 10 | 10 |
| 4 — CLD             | `$streetlights-demo step 4` | 8  | 8  |
| 5 — Semantic View   | `$streetlights-demo step 5` | 8  | 8  |
| 6 — Cortex Search   | `$streetlights-demo step 6` | 8  | 8  |
| 7 — Agent           | `$streetlights-demo step 7` | 8  | 8  |
| **Total**           | **7 invocations**           | **60** | **8** (floor 60÷7) |
```

> **Infrastructure ICR: 8** — each skill invocation replaced ~8 manual operations on average.

Then close with:

> Run `$streetlights-demo app` any time to deploy the SiS app + ML Forecast + Validation.

### If "Continue → App phase":

Respond with:

> Run `$streetlights-demo app` to start the App phase (ML Forecast + Streamlit + Validation).
