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

# Step 7: Create Intelligence Agent

## Why this matters

**Tool-use architecture** — The Intelligence Agent doesn't answer questions directly. It *routes* them to the right tool: Cortex Analyst for structured SQL queries, or Cortex Search for text retrieval. This is a tool-use pattern — the agent is an orchestrator that composes multi-tool answers from a single natural language question.

**Composing multi-source answers** — A question like "Tell me about maintenance issues in the busiest neighborhood" requires *both* SQL (to find the busiest neighborhood) and text search (to find maintenance records). The agent decomposes the question, routes sub-parts to the right tools, and synthesizes a unified answer.

**IDD connection** — The agent's `FROM SPECIFICATION` block is the purest form of [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c) — you declare routing rules, sample questions, and tool configurations as intent. The platform handles LLM orchestration, tool invocation, and response synthesis.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

---

**STOP** — Use `ask_user_question` to confirm:
- Header: "Step 7"
- Question: "Ready to proceed with Intelligence Agent creation? (combines Analyst + Search)"
- Options: ["Yes, proceed", "Skip this step"]

---

## What we'll do

Create the Cortex Intelligence Agent that combines Semantic View (structured analytics) with Cortex Search (text retrieval) into a single natural language interface.

- Deploy Agent DDL with full FROM SPECIFICATION (orchestration rules, tools, sample questions)
- Verify the agent routes queries correctly
- Test both structured and unstructured queries
- Register agent with `SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT` so it appears in the Snowflake Intelligence UI

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

## Dry-Run

Show the execution plan to the user:
```bash
uv run gate --step step-7 --action dry-run
```
Present the output, then ask user to proceed.

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 7"
- Question: "Ready to create the Intelligence Agent?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

### Prerequisites

- Semantic View exists (Step 5 complete)
- Cortex Search service is ACTIVE (Step 6 complete)

### Steps

1. Read manifest for database/warehouse/role names
2. Execute Agent DDL + Grant Access:
   ```bash
   snow sql -f snowflake/04_intelligence_agent.sql \
     -D "PREFIX={manifest.demo.prefix.upper()}" \
     -D "ROLE={manifest.snowflake.role}" \
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

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

## Mark COMPLETE

```bash
uv run gate --step step-7 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 8: Train ML Forecast?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 8` for later resumption.
