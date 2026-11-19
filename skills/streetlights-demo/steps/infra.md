---
name: streetlights-demo-infra
description: Infrastructure phase orchestration — steps 1–7 sequential, builds PG Iceberg → CLD → Semantic View → Cortex Search → Intelligence Agent
---

## Gate

```bash
uv run gate --step step-1 --prior-step setup --action check
```

If BLOCK: inform the user that setup must be complete before starting the Infrastructure phase.
Run `$streetlights-demo setup` first.
If PASS: continue below.

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately. Do NOT present any step content until
> plan mode is active.

# Infrastructure Phase: Steps 1–7

## Why this matters

This phase builds the complete data and analytics stack from scratch — seven sequential steps
that turn raw CSV data into a live AI-queryable intelligence layer inside Snowflake.

Each step adds a distinct layer:

- **Step 1 — Generate Data**: Location-aware synthetic streetlight data (CSV). Seeded to your
  city or a configurable override — every map link and neighborhood reference is geographically
  coherent.

- **Step 2 — PG Instance** ⚠️: The Snowflake Postgres instance is the managed storage layer.
  Iceberg tables live here. Postgres handles the file layout; Snowflake reads it natively.

- **Step 3 — Schema + Load**: Create all 7 Iceberg tables in Postgres and load the CSVs.
  From this point on, the data lives in Iceberg format — queryable by both Postgres and Snowflake
  without any movement.

- **Step 4 — CLD** ⚠️: The Catalog Integration + Catalog-Linked Database is the zero-copy
  bridge. Snowflake sees the Iceberg tables as native objects — no pipeline, no ETL, no sync job.

- **Step 5 — Semantic View**: Declarative analytics intent. The view encodes *what* the data
  means (dimensions, measures, relationships) so Cortex Analyst can answer SQL questions in
  natural language without knowing table or column names.

- **Step 6 — Cortex Search**: Full-text semantic search over maintenance records. Lets the
  Intelligence Agent answer unstructured questions ("find reports about exposed wires") without
  SQL.

- **Step 7 — Agent**: The Intelligence Agent composes Semantic View + Cortex Search into one
  natural language interface. A single question can route to SQL (Analyst), text (Search), or
  both — and synthesize a unified answer.

**IDD connection** — this is [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14):
seven declarative skill invocations replace 60 manual SQL, bash, Python, and API operations.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim.

## What we'll do

Execute steps 1–7 sequentially. Each step follows its own step file with plan mode confirmation.

> ⚠️ **Billable actions** at two points — confirm with the user before proceeding:
> - **Step 2**: creates a Snowflake Postgres instance (compute + storage cost)
> - **Step 4**: creates a Catalog Integration + CLD (catalog sync cost)

**Plan summary**:
1. Step 1 — Generate location-aware synthetic CSV data
2. Step 2 ⚠️ — Create/reuse PG instance (`$snowflake-postgres` [bundled])
3. Step 3 — Create Iceberg tables + load CSV data into Postgres
4. Step 4 ⚠️ — Create Catalog Integration + CLD (`$snowflake-postgres` [bundled])
5. Step 5 — Create Semantic View on CLD tables
6. Step 6 — Create Cortex Search service on maintenance records
7. Step 7 — Create Intelligence Agent (Semantic View + Search)

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with the summary above. Proceed to Execution only
> after the user confirms.

## Execution

Each step is self-contained. For each step below, follow its step file completely:
gate check → mark IN_PROGRESS → plan mode → execute → mark COMPLETE → "What we did".

Only proceed to the next step after the current step's gate marks it COMPLETE.

### Step 1 — Generate Data

→ Follow `steps/step-1.md`

### Step 2 — PG Instance ⚠️

→ Follow `steps/step-2.md` (routes to `$snowflake-postgres` [bundled])

> The sub-skill handles the billable confirmation and PG creation/reuse.

### Step 3 — Schema + Load

→ Follow `steps/step-3.md`

### Step 4 — CLD ⚠️

→ Follow `steps/step-4.md` (routes to `$snowflake-postgres` [bundled])

> The sub-skill handles the Catalog Integration + CLD creation.

### Step 5 — Semantic View

→ Follow `steps/step-5.md`

### Step 6 — Cortex Search

→ Follow `steps/step-6.md`

### Step 7 — Agent

→ Follow `steps/step-7.md`

> Step 7 ends with the **opt-in gate**: the user is asked whether to continue to the App phase
> (`$streetlights-demo app`) or stop here. Follow the step-7.md opt-in gate instructions —
> do NOT skip this question.

## What we did

- ✅ Step 1: Location-aware CSV data generated
- ✅ Step 2: Snowflake Postgres instance ready (Iceberg managed storage)
- ✅ Step 3: 7 Iceberg tables created + CSV data loaded
- ✅ Step 4: Catalog Integration + CLD live (zero-copy Snowflake access)
- ✅ Step 5: Semantic View deployed (structured analytics intent)
- ✅ Step 6: Cortex Search service ACTIVE (text retrieval on maintenance records)
- ✅ Step 7: Intelligence Agent live and queryable in Snowflake Intelligence

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user.

### IDD Metrics — Infrastructure Phase

| Step | Invocation | Trad. Ops (baseline) | Step ICR |
|------|------------|----------------------|----------|
| 1 — Generate Data   | `$streetlights-demo step 1` | 6  | 6  |
| 2 — PG Instance     | `$streetlights-demo step 2` | 12 | 12 |
| 3 — Schema + Load   | `$streetlights-demo step 3` | 10 | 10 |
| 4 — CLD             | `$streetlights-demo step 4` | 8  | 8  |
| 5 — Semantic View   | `$streetlights-demo step 5` | 8  | 8  |
| 6 — Cortex Search   | `$streetlights-demo step 6` | 8  | 8  |
| 7 — Agent           | `$streetlights-demo step 7` | 8  | 8  |
| **Infrastructure**  | **1 `$streetlights-demo infra` invocation** | **60** | **60** |

> **Infrastructure phase ICR: 60** — all seven sequential steps delivered by one
> `$streetlights-demo infra` invocation.
>
> Per-step average: floor(60 ÷ 7) = **8** manual operations replaced per intent.

> **Note**: The opt-in gate at step 7 closes this phase. Run `$streetlights-demo app` at any
> time to continue with ML Forecast + Streamlit + Validation.
