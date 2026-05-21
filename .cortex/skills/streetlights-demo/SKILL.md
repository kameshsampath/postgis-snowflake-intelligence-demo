---
name: streetlights-demo
description: Guided pedagogical demo of Snowflake Postgres + pg_lake + Intelligence
invocations:
  - streetlights-demo
  - streetlights-demo setup
  - streetlights-demo step <N>
  - streetlights-demo cleanup
---

# Streetlights Demo Skill

## Global Rules
- **Always use markdown** for all user-facing output (tables, code blocks, admonitions)
- **Never hallucinate** — if uncertain about any value, path, or state, use `ask_user_question` to confirm with the user
- **Stop on billable actions** — always warn and confirm before creating PG instances or CLD

## Routing

| Command | Route |
|---------|-------|
| `$streetlights-demo setup` | → `steps/setup.md` |
| `$streetlights-demo step 1` | → `steps/step-1.md` |
| `$streetlights-demo step 2` | → `steps/step-2.md` (routes to `$snowflake-postgres`) |
| `$streetlights-demo step 3` | → `steps/step-3.md` |
| `$streetlights-demo step 4` | → `steps/step-4.md` (routes to `$snowflake-postgres`) |
| `$streetlights-demo step 5` | → `steps/step-5.md` |
| `$streetlights-demo step 6` | → `steps/step-6.md` |
| `$streetlights-demo step 7` | → `steps/step-7.md` |
| `$streetlights-demo step 8` | → `steps/step-8.md` |
| `$streetlights-demo step 9` | → `steps/step-9.md` (routes to `$developing-with-streamlit-in-snowflake`) |
| `$streetlights-demo step 10` | → `steps/step-10.md` |
| `$streetlights-demo cleanup` | → `cleanup/SKILL.md` |

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

## Step Overview

| Step | Title | Key Actions |
|------|-------|-------------|
| setup | Init manifest | Create `.streetlights-demo/manifest.toml`, confirm prefix |
| 1 | Generate Data | Location-aware synthetic data generation |
| 2 | PG Instance | Create/reuse Snowflake Postgres instance (managed storage) |
| 3 | Schema + Load | Create Iceberg tables, load CSV data |
| 4 | CLD | Catalog Integration + Catalog-Linked Database |
| 5 | Semantic View | Create Semantic View on CLD tables |
| 6 | Cortex Search | Create Cortex Search service on maintenance records |
| 7 | Agent | Create Intelligence Agent (Semantic View + Search) |
| 8 | ML Forecast | Train FORECAST model on energy consumption |
| 9 | Deploy SiS | Deploy multi-page Streamlit app |
| 10 | Validate | Run sanity gate, demo the system |
