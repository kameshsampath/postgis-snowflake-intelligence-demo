# Snowflake Postgres Intelligence Plugin

**CoCo + Claude Code Plugin for Snowflake Postgres + pg_lake + Cortex AI**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## What This Is

A distributable plugin for [Cortex Code (CoCo)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) and [Claude Code](https://code.claude.com) that provides a guided pedagogical demo of Snowflake Postgres + pg_lake + Cortex Intelligence.

The plugin contains **skill orchestration only** — it bootstraps its own workspace via sparse checkout from the [source repository](https://github.com/kameshsampath/postgis-snowflake-intelligence-demo) when invoked.

## Installation

### Cortex Code (CoCo)

```bash
cortex plugin install --source github --repo kameshsampath/postgis-snowflake-intelligence-demo --branch feature/coco-claude-plugin
```

### Claude Code

Add the marketplace or install directly:

```bash
claude --plugin-dir /path/to/this/repo
```

Or submit to the [Claude community marketplace](https://claude.ai/settings/plugins/submit) for discoverable installation.

### Local Development

```bash
# CoCo
cortex --plugin-dir .

# Claude Code
claude --plugin-dir .
```

## Skills Provided

| Skill | Trigger | Description |
|-------|---------|-------------|
| `streetlights-demo` | `$streetlights-demo` | Full guided demo (setup through step 10) |
| `streetlights-demo-cleanup` | `$streetlights-demo cleanup` | Tear down all demo resources |

## How It Works

1. User invokes `$streetlights-demo`
2. Plugin bootstraps a workspace via **sparse git checkout** (detached HEAD)
3. Only runtime-required directories are cloned: `snowflake/`, `scripts/`, `app/`, `init/`
4. Root-level files (`pyproject.toml`, `.envrc`, etc.) are included automatically (cone mode)
5. Demo executes in the isolated workspace

The plugin itself never needs the runtime project files — it reads `sparseCheckout` config from `.cortex-plugin/plugin.json` to know what to pull.

## Plugin Structure

```
.
├── .claude-plugin/
│   └── plugin.json              # Claude Code manifest
├── .claude/commands/
│   └── streetlights-demo.md     # Claude Code slash command
├── .cortex-plugin/
│   ├── plugin.json              # CoCo manifest (with sparseCheckout config)
│   └── skills -> ../skills      # Symlink to shared skills
├── .cortex/skills/
│   └── streetlights-demo -> ../../skills/streetlights-demo
├── skills/                      # Canonical skill content
│   └── streetlights-demo/
│       ├── SKILL.md             # Main orchestration entrypoint
│       ├── steps/               # Per-step guidance (setup, 1-10)
│       ├── references/          # Concepts, CLI ref, IDD metrics
│       ├── cleanup/             # Teardown skill
│       └── scripts/             # Gate verification
├── AGENTS.md                    # Agent instructions
├── CLAUDE.md                    # Claude Code project context
└── README.md
```

## Prerequisites

Before running the demo (handled by the skill's Bootstrap):

| Tool | Purpose |
|------|---------|
| `git` | Sparse checkout of workspace |
| `snow` CLI | Snowflake operations |
| `uv` | Python dependency management |
| `psql` | PostgreSQL access |

Snowflake account must have Snowflake Postgres enabled.

## Demo Overview

The plugin orchestrates a 10-step demo across two phases:

**Phase 1 — Infrastructure** (steps 1-7): Data generation → PG Iceberg → CLD → Semantic View → Cortex Search → Intelligence Agent

**Phase 2 — App** (steps 8-10): ML Forecast + Streamlit dashboard + end-to-end validation

See [skills/streetlights-demo/SKILL.md](skills/streetlights-demo/SKILL.md) for full orchestration details.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

Copyright 2025 Kamesh Sampath
