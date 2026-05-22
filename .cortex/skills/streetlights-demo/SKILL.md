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
- **Bundled skills** — Skills marked [bundled] are system-level. Invoke via the `skill` tool — do NOT search the project `.cortex/skills/` directory.
- **CRITICAL: PostgreSQL connections MUST use pg_service** — use `psql "service=$PGSERVICE"`. NEVER use `-h`, `-U`, or pass credentials directly. `PGSERVICE` is set via `.envrc`/direnv from the manifest.

## Routing

| Command | Route |
|---------|-------|
| `$streetlights-demo setup` | → `steps/setup.md` |
| `$streetlights-demo step 1` | → `steps/step-1.md` |
| `$streetlights-demo step 2` | → `steps/step-2.md` (routes to `$snowflake-postgres` [bundled]) |
| `$streetlights-demo step 3` | → `steps/step-3.md` |
| `$streetlights-demo step 4` | → `steps/step-4.md` (routes to `$snowflake-postgres` [bundled]) |
| `$streetlights-demo step 5` | → `steps/step-5.md` |
| `$streetlights-demo step 6` | → `steps/step-6.md` |
| `$streetlights-demo step 7` | → `steps/step-7.md` |
| `$streetlights-demo step 8` | → `steps/step-8.md` |
| `$streetlights-demo step 9` | → `steps/step-9.md` (routes to `$developing-with-streamlit-in-snowflake` [bundled]) |
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

## Methodology

This demo follows **Intent-Driven Development (IDD)** — a methodology where AI agents execute declarative skill files that encode infrastructure and workflow intent.

References:
- [Infrastructure as Intent](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
- [Ghost in the Machine](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
- [Intent-Driven Development](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
- [Intent Compression Ratio](https://medium.com/@kameshsampath/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)
- [ICR and Token Economics](https://medium.com/@kameshsampath/icr-and-token-economics-9a014a75b399)

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
| 7 | Agent | Create Intelligence Agent (Semantic View + Search) |
| 8 | ML Forecast | Train FORECAST model on energy consumption |
| 9 | Deploy SiS | Deploy multi-page Streamlit app |
| 10 | Validate | Run sanity gate, demo the system |
