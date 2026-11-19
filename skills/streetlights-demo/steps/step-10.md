---
name: streetlights-demo-step-10
description: Run end-to-end validation and demonstrate the complete pipeline
---

## Gate

```bash
uv run gate --step step-10 --prior-step step-9 --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

> **In `$streetlights-demo app`**: The Synthesizer agent runs this step after both the Forecast
> worker (step 8) and the Deploy worker (step 9) send their completion task notifications.
> The `--prior-step step-9` gate confirms the full app phase chain before validation proceeds.

## Mark IN_PROGRESS

```bash
uv run gate --step step-10 --desc "Validating end-to-end demo" --action start
```

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 10: Validate & Demo

## What we'll do

Run the full end-to-end sanity gate to verify all components are operational, then demonstrate the Intelligence Agent with sample queries.

- Execute the sanity gate script (checks all 8 components)
- Display top 5 demo questions with routing explanation
- Show bonus combined queries for advanced testing

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a summary of what validation will run. Proceed to Execution only after the user confirms.

## Execution

### Validation

1. Run the end-to-end sanity gate:
   ```bash
   uv run python scripts/sanity_gate.py
   ```
2. Verify all checks pass:
   - Manifest exists and is valid
   - PG instance reachable
   - CLD healthy (all 7 tables visible)
   - Semantic View queryable
   - Cortex Search service ACTIVE
   - Agent responds to queries
   - Forecast model trained
   - SiS app accessible

### Forecast Demo

```sql
-- 30-day failure forecast
CALL {database}.{schema}.BULB_FAILURE_FORECASTER!FORECAST(
  FORECASTING_PERIODS => 30
);
```

## What we did

- ✅ All gates passed (manifest, PG, CLD, Semantic View, Search, Agent, Forecast, SiS)
- ✅ End-to-end sanity check passed

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 10` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~8 — (8 sanity gate component checks + 2 bash/SQL demo queries without this skill) |
| **Step ICR** | **8** (8 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## IDD Session Summary

Recall the IDD metrics tracked after each step in this session. For any step that was
skipped, use the traditional ops baseline shown. Compile and present the full summary.

### Infrastructure ICR

$$
\text{Infrastructure ICR} = \left\lfloor \frac{\text{Total Traditional Ops}}{\text{Total Skill Invocations}} \right\rfloor
$$

| Step | Invocation | Agent Ops (actual) | Trad. Ops (baseline) | Step ICR |
|---|---|---|---|---|
| 1 — Generate Data | `$streetlights-demo step 1` | (recall from context) | 6  | 6  |
| 2 — PG Instance   | `$streetlights-demo step 2` | (recall from context) | 12 | 12 |
| 3 — Schema + Load | `$streetlights-demo step 3` | (recall from context) | 10 | 10 |
| 4 — CLD           | `$streetlights-demo step 4` | (recall from context) | 8  | 8  |
| 5 — Semantic View | `$streetlights-demo step 5` | (recall from context) | 8  | 8  |
| 6 — Cortex Search | `$streetlights-demo step 6` | (recall from context) | 8  | 8  |
| 7 — Agent         | `$streetlights-demo step 7` | (recall from context) | 8  | 8  |
| **Infrastructure subtotal** | **7 invocations** | | **60** | **8** avg |
| 8 — ML Forecast   | Forecast worker (app phase) | (recall from context) | 5  | 5  |
| 9 — SiS App       | Deploy worker (app phase)   | (recall from context) | 9  | 9  |
| 10 — Validate     | Synthesizer (app phase)     | (recall from context) | 8  | 8  |
| **App subtotal**  | **`$streetlights-demo app` (1 invocation)** | | **22** | **22** |
| **Full session**  | **8 invocations**           | | **82** | **10** (floor 82÷8) |

> **Infrastructure phase ICR: 8** — each of 7 skill invocations replaced ~8 manual operations.
> **App phase ICR: 22** — all three App steps delivered by one `$streetlights-demo app` invocation.
> \"Traditional ops\" counts SQL statements + bash commands + Python scripts + API calls.

### Query ICR

Run `uv run idd-metrics` to show natural language query metrics:

```bash
uv run idd-metrics
```

ICR score = int(traditional_ops × 1000 ÷ NL tokens) — ops per intent token
(per [icr-lab](https://github.com/kameshsampath/icr-lab) formula).

### Combined IDD Picture

| Dimension | Value | What it measures |
|---|---|---|
| **Infrastructure ICR** | 8 avg/step | 7 invocations, 60 ops (floor 60÷7) |
| **App phase ICR** | 22 | 1 invocation (`$streetlights-demo app`), 22 ops |
| **Full session ICR** | 10 | 8 invocations, 82 ops (floor 82÷8) |
| **Query ICR score** | run `idd-metrics` | NL query ops × 1000 ÷ NL tokens (icr-lab) |
| **SQL leverage** | ~5.9 | SQL tokens generated per NL token |
| **Schema abstraction** | 7 tables / 0 mentioned | User never specifies a table or column name |

> End-to-end [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c):
> infrastructure as intent + queries as intent + AI handles *how*.

## Try these with Snowflake Intelligence

| # | Question | Routing | What it tests |
|---|----------|---------|---------------|
| 1 | "How many street lights are currently faulty?" | Analyst → SQL | Status aggregation |
| 2 | "Which neighborhoods have the highest energy consumption?" | Analyst → SQL | Cross-table join |
| 3 | "Find maintenance reports about exposed wires or sparking" | Search → text | Semantic similarity |
| 4 | "What is the average repair cost by maintenance type?" | Analyst → SQL | Grouped metrics |
| 5 | "Show me the top 5 neighborhoods by maintenance frequency" | Analyst → SQL | Rankings |

**Grid zones + technician dispatch queries (new in app v2):**

| # | Question | Routing | What it tests |
|---|----------|---------|---------------|
| 6 | "Which power grid zones are overloaded and how many faulty lights are nearby?" | Analyst → SQL | Multi-table join with spatial context |
| 7 | "Who has the most experience fixing lights in the neighborhood with the most faults?" | Analyst → SQL | Subquery + ranking |
| 8 | "Show the repair history for the technician assigned to the highest-load grid zone" | Analyst → SQL | Chain reasoning across 3 tables |

**Bonus — try these combined queries:**
- "Tell me about maintenance issues in the busiest neighborhood" (Agent routes to both tools)
- "What's the situation with faulty lights and their repair status?" (Combined routing)
- "Which technician should I dispatch to fix the most critical grid zone right now?" (Grid load + technician join)

The demo is fully operational. You now have:
- PostgreSQL with pg_lake Iceberg tables
- Native CLD sync to Snowflake (no CDC pipeline needed)
- Semantic View for structured analytics
- Cortex Search for text retrieval
- Intelligence Agent combining both (UI auto-renders charts)
- ML Forecast for predictive maintenance
- Multi-page Streamlit dashboard

All powered by a single `$streetlights-demo` skill workflow.

## Mark COMPLETE

```bash
uv run gate --step step-10 --action complete
```

## Next

Demo complete! All 10 steps finished successfully. The streetlights intelligence system is fully operational.
