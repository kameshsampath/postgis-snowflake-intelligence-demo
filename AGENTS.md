# AGENTS.md

## Purpose

This repository is a Snowflake Postgres + pg_lake + Cortex AI reference demo.

It is a guided engineering workspace used by synthesis engines such as Codex, Claude Code, and Cortex Code to demonstrate Intent-Driven Development through a real-world streetlights infrastructure scenario.

The repository itself is not the running demo.

## Core Principle

Treat this repository as structured demo engineering context.

Do not treat it as a generic codebase to refactor freely.

## Demo Skill

The primary reusable reasoning context for this repository is:

```text
.cortex/skills/streetlights-demo/
```

This skill bundle is designed to be autoloaded by compatible coding agents.

Agents should treat:

```text
.cortex/skills/streetlights-demo/SKILL.md
```

as the orchestration entrypoint for:

- demo step sequencing (setup through step 10)
- gate verification logic
- SQL execution patterns
- manifest configuration
- cleanup and teardown

The skill bundle also contains per-step guidance under:

```text
.cortex/skills/streetlights-demo/steps/
```

Operational rules (snow CLI flags, manifest field references, CLD quoting, object placement, warehouse resilience, Intelligence registration, map link format, gate timing) are packaged inside SKILL.md and AGENTS.md in the skill bundle — not in this file.

## Stable Framework Areas

The following directories define the demo framework and should not be modified during demo execution unless explicitly requested:

```text
.cortex/skills/streetlights-demo/
scripts/
snowflake/
init/
tests/
```

Note:

- `scripts/` contains gate logic, data generation, and manifest helpers — changes affect all demo steps
- `snowflake/` contains DDL templates executed against live Snowflake — changes are destructive if applied without re-running steps
- `tests/` defines the correctness contract — do not weaken assertions

## Data Directory

- `data/` and its generated CSVs are git-ignored
- never commit files inside `data/` unless explicitly requested

Generated CSV files:

```text
data/street_lights.csv
data/maintenance_records.csv
data/energy_consumption.csv
data/light_sensors.csv
data/weather_enrichment.csv
data/demographics.csv
data/power_grid_zones.csv
```

## Generation Boundary

During demo execution:

- stable framework context lives outside `data/`
- synthesized data artifacts belong only under `data/`
- generated postgresql file belong only under `init/` 

Agents must not rewrite framework SQL or scripts as a side-effect of running demo steps.

## Demo Philosophy

This repository demonstrates Intent-Driven Development:

```text
Intent
→ Reusable Skill Context
→ Structured Contracts (manifest.toml, gate checks)
→ Deterministic Templates (SQL with <% PREFIX %>)
→ Generated Artifacts (data/, Snowflake objects)
→ Evaluation (sanity_gate.py)
→ Refinement
```

The skill file is the stable engineering context.

Generated Snowflake objects and data are ephemeral synthesis artifacts.

## GitHub

- all GitHub operations must use the `kameshsampath` account
- always verify `gh auth status` shows `kameshsampath` as the active account before any GitHub operations
- if the active account is not `kameshsampath`, switch with:

```bash
gh auth switch --user kameshsampath
```

## Commits

Always use Conventional Commits style:

```text
https://www.conventionalcommits.org/
```

Allowed types:

- feat
- fix
- chore
- docs
- refactor
- test
- build
- ci
- perf
- style
- revert

Example:

```text
feat: add user authentication module
```

## Pre-commit

All commits and code changes must pass pre-commit hooks before being committed.

Run before committing:

```bash
pre-commit run --all-files
```

Task completion requires all pre-commit hooks to pass.

Do not mark a task done if hooks are failing.

Install hooks on first use:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

## Skill Development Standards

When modifying any file under `.cortex/skills/streetlights-demo/`, follow the
`$skill-development` best practices:

- **Frontmatter**: `name` and `description` only — no custom fields (`invocations`,
  `intent_triggers`, or others)
- **Triggers**: encode intent phrases inside the `description` field, not in
  separate fields
- **Size**: keep `SKILL.md` under 500 lines; move reference material to
  `references/` sub-files
- **Instructions**: prefer explaining *why* over rigid `ALWAYS`/`NEVER` rules;
  use ⚠️ **MANDATORY** only for truly required actions, not stylistic preferences

## Tone

Use a calm, architectural, engineering-oriented, teaching tone.

Prefer:

- practical explanations
- systems-thinking
- architectural framing
- deterministic workflows
- reusable context
- measurable abstraction

Avoid:

- AI magic
- autonomous agent hype
- replace developers language
- 10x engineer claims
- vibe coding language
- product marketing language
