---
name: streetlights-demo
description: >
  Guided pedagogical demo of Snowflake Postgres + pg_lake + Cortex AI,
  demonstrating Intent-Driven Development through a streetlights infrastructure
  scenario. Use when: "start the streetlights demo", "run the streetlights demo",
  "show me the streetlights demo", "streetlights infrastructure demo",
  "demo snowflake postgres with Cortex", "pg_lake demo",
  "demo Cortex Intelligence with streetlights".
---

# Streetlights Demo Skill

## Global Rules

### Core execution rules (see AGENTS.md for full details)

1. **snow sql**: always pass `--format json`, `-c {connection}`, `--enable-templating STANDARD`.
   - Template syntax: `<% PREFIX %>` (STANDARD). Never `${PREFIX}`.
   - Execution: `snow sql -f snowflake/FILE.sql -D "PREFIX=KAMESHS" -c {connection} --enable-templating STANDARD`

2. **manifest.toml is source of truth**: read config via `load_manifest()`. manifest.toml is the single config source — no `.env` lookup. `prefix` is lowercase in manifest but must be UPPERCASE in `-D "PREFIX=..."` flag.

3. **CLD columns need quoting**: CLD tables have lowercase column names from PostgreSQL. Always double-quote: `"light_id"`, `"date"`, `"status"`, `"kwh"`, etc.

4. **Object placement**: create ALL Snowflake objects (semantic views, Cortex Search, agents, ML Forecast, Streamlit) in `{PREFIX}_STREETLIGHTS.PUBLIC`. CLD is read-only — SELECT only.

- **Always use markdown** for all user-facing output (tables, code blocks, admonitions)
- **Never hallucinate** — if uncertain about any value, path, or state, use `ask_user_question` to confirm with the user
- **Stop on billable actions** — always warn and confirm before creating PG instances or CLD
- **Bundled skills** — Skills marked [bundled] are system-level. Invoke via the `skill` tool — do NOT search the project `.cortex/skills/` directory.
- **CRITICAL: PostgreSQL connections MUST use pg_service** — use `psql "service=$PGSERVICE"`. NEVER use `-h`, `-U`, or pass credentials directly. `PGSERVICE` is set via `.envrc`/direnv from the manifest.
- **THREE MANDATORY presentation points per step** — You MUST output these sections verbatim to the user as formatted markdown. Never skip, summarize, or paraphrase:
  1. "Why this matters" — the teaching moment (concepts + IDD connection)
  2. "What we'll do" — the intro preview of actions
  3. "What we did" — the outro summary of completed work
  Each is a natural pause point. Present it, let the user read it, then continue.
- ⚠️ **MANDATORY — Step plan mode**: Call `enter_plan_mode` immediately after marking a step IN_PROGRESS, before presenting any content. The full step preview (Why this matters → What we'll do → dry-run output) runs inside plan mode. Call `exit_plan_mode` with a plan summary after the dry-run output (or after "What we'll do" for steps without a dry-run). There are no intermediate `Proceed?` asks or `STOP` blocks within the step flow — `exit_plan_mode` is the single confirmation gate.

## Routing

| Command | Route |
|---------|-------|
| `$streetlights-demo` (no args) | → Demo Introduction (plan mode overview) |
| `$streetlights-demo setup` | → `steps/setup.md` |
| `$streetlights-demo step 1` | → `steps/step-1.md` |
| `$streetlights-demo step 2` | → `steps/step-2.md` (routes to `$snowflake-postgres` [bundled]) |
| `$streetlights-demo step 3` | → `steps/step-3.md` |
| `$streetlights-demo step 4` | → `steps/step-4.md` (routes to `$snowflake-postgres` [bundled]) |
| `$streetlights-demo step 5` | → `steps/step-5.md` |
| `$streetlights-demo step 6` | → `steps/step-6.md` |
| `$streetlights-demo step 7` | → `steps/step-7.md` |
| `$streetlights-demo step 8` | → `steps/step-8.md` (standalone; or via `$streetlights-demo app`) |
| `$streetlights-demo step 9` | → `steps/step-9.md` (routes to `$developing-with-streamlit-in-snowflake` [bundled]; or via `$streetlights-demo app`) |
| `$streetlights-demo step 10` | → `steps/step-10.md` (or via `$streetlights-demo app`) |
| `$streetlights-demo app` | → `steps/app.md` (App phase: steps 8–10 in parallel via Team `streetlights-app-phase`) |
| `$streetlights-demo cleanup` | → `cleanup/SKILL.md` |

## Demo Introduction

> ⚠️ **MANDATORY**: When `$streetlights-demo` is invoked with no step argument (or via
> an intent trigger), call `enter_plan_mode` before presenting any content. Then present:
>
> 1. **What this demo is** — Intent-Driven Development applied to real infrastructure:
>    a single skill invocation replaces dozens of manual Snowflake + Postgres operations.
> 2. **Two-phase structure** — from the Phase Overview below.
> 3. **Architecture overview** — from the Architecture section below.
> 4. **Step table** — from the Step Overview section below.
>
> Call `exit_plan_mode` after presenting all four. Then ask which step to start with
> and suggest `$streetlights-demo setup` as the entry point.

## Phase Overview

This demo has **two self-contained phases**:

| Phase | Command | Steps | What it builds |
|-------|---------|-------|----------------|
| **Infrastructure** | `$streetlights-demo step 1` … `step 7` | setup → 7 | PG Iceberg → CLD → Semantic View → Cortex Search → Intelligence Agent |
| **App** | `$streetlights-demo app` | 8–10 (parallel) | ML Forecast + Streamlit dashboard + end-to-end validation |

**The Infrastructure phase is self-contained.** At the end of step 7, the user is asked whether
to continue to the App phase or stop and use the Intelligence Agent directly in Snowflake
Intelligence. The App phase (`$streetlights-demo app`) can be run at any time after step 7.

## Prerequisites
- Snowflake account with Cortex features enabled
- `snow` CLI configured (connection in manifest)
- `uv` for Python dependency management
- `psql` for PostgreSQL access

## Quick Start
```
$streetlights-demo setup
$streetlights-demo step 1
... (follow steps sequentially)
```

## Architecture

```
Snowflake Postgres (pg_lake)          Snowflake
┌──────────────────────────┐          ┌─────────────────────────────────┐
│ Iceberg tables (ALL 7)   │  Shared  │  Catalog Integration (CLD)      │
│ (managed storage ONLY)   │──Iceberg─│         ↓                       │
│                          │          │  Semantic View + Cortex Search  │
│ Location-aware data:     │          │  + ML FORECAST models           │
│ user's city or override  │          │  + Intelligence Agent           │
│                          │          │  (Semantic View + Search)       │
│ Spatial: lat/lng FLOAT   │          │                                 │
│ (no PostGIS GEOMETRY     │          │  + SiS Multi-Page App           │
│  in Iceberg tables)      │          │                                 │
└──────────────────────────┘          └─────────────────────────────────┘
```

## Methodology

This demo follows **Intent-Driven Development (IDD)** — a methodology where AI agents execute declarative skill files that encode infrastructure and workflow intent.

References:
- [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
- [Ghost in the Machine](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
- [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
- [Intent Compression Ratio](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)
- [ICR and Token Economics](https://blogs.kameshs.dev/icr-and-token-economics-9a014a75b399)
- [icr-lab](https://github.com/kameshsampath/icr-lab) — interactive ICR + token economics simulator

## IDD Tracking

After each step's "What we did" section, display and carry forward in session memory:

| Metric | What to count |
|---|---|
| **Intent expressed** | Always 1 — the `$streetlights-demo step N` invocation |
| **Agent operations** | Distinct commands actually run: SQL statements, bash commands, Python scripts, API calls |
| **Traditional ops** | The step's pre-defined baseline (what a developer would do manually without this skill) |
| **Step ICR** | `traditional_ops ÷ 1 invocation = traditional_ops` (whole integer) |

**"Traditional ops"** counts all discrete manual actions: SQL statements written, bash/shell
commands run, Python scripts called, API calls made, configuration files written.

Step 10 recalls these from session memory and compiles the full **IDD Session Summary**
(Infrastructure ICR + Query ICR via `uv run idd-metrics`).

For pre-computed baseline values to answer user questions, see `references/idd-metrics.md`.

## Step Overview

| Step | Title | Key Actions |
|------|-------|-------------|
| setup | Init manifest | Create `.streetlights-demo/manifest.toml`, confirm prefix |
| 1 | Generate Data | Location-aware synthetic data generation |
| 2 | ⚠️ PG Instance | Create/reuse Snowflake Postgres instance (managed storage) |
| 3 | Schema + Load | Create Iceberg tables, load CSV data |
| 4 | ⚠️ CLD | Catalog Integration + Catalog-Linked Database |
| 5 | Semantic View | Create Semantic View on CLD tables |
| 6 | Cortex Search | Create Cortex Search service on maintenance records |
| 7 | Agent | Create Intelligence Agent (Semantic View + Search) ← **Infrastructure phase ends here** |
| — | — | *Step 7 asks: continue to App phase or stop here?* |
| **app** | **App Phase** | **`$streetlights-demo app` — runs steps 8–10 in parallel via Team `streetlights-app-phase`** |
| 8 | ML Forecast | Train FORECAST model on energy consumption (Forecast worker) |
| 9 | Deploy SiS | Deploy multi-page Streamlit app (Deploy worker) |
| 10 | Validate | Run sanity gate, compile full IDD session summary (Synthesizer) |
