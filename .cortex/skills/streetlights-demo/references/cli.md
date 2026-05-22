# Gate CLI Reference

The `gate` script manages step progression and verification for the streetlights demo.

## Usage

```bash
uv run gate --step <STEP> --action <ACTION> [--prior-step <STEP>] [--desc <TEXT>]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Step identifier: `setup`, `step-1` through `step-10` |
| `--action` | Yes | Action to perform (see below) |
| `--prior-step` | No | Verify this step (and its ancestors) are COMPLETE before checking current |
| `--desc` | No | Description text (used with `start` action) |

## Actions

| Action | Effect |
|--------|--------|
| `check` | Verify step prerequisites and current step state. Exits 0 (PASS) or 1 (BLOCK). If `--prior-step` is given, walks the full ancestor chain and re-verifies stale entries. |
| `start` | Mark step as IN_PROGRESS in the manifest. |
| `complete` | Mark step as COMPLETE in the manifest (timestamps it). |
| `reset` | Remove the step's state from the manifest entirely. |
| `dry-run` | Print the execution plan for the step without running anything. |

## Step Chain

The gate enforces ordering via a chain. Each step depends on the previous:

```
setup → step-1 → step-2 → step-3 → step-4 → step-5 → step-6 → step-7 → step-8 → step-9 → step-10
```

## Internal Verify Functions

These functions run automatically when `--action check` is invoked for a step. They are NOT standalone CLI actions — do not call them directly.

| Step | Internal Check | What It Verifies |
|------|---------------|-----------------|
| `setup` | `check_manifest` | Manifest file exists and parses |
| `step-1` | `_check_csv_files` | All 7 CSV files present in `data/` |
| `step-2` | `check_pg_reachable` | PG instance responds to `SELECT 1` |
| `step-3` | `_check_pg_tables` | Tables exist in `streetlights` schema (also auto-generates DDL if missing) |
| `step-4` | `check_cld_healthy` | CLD propagation complete, 7 tables visible |
| `step-5` | `_check_semantic_view` | Semantic view DDL succeeded |
| `step-6` | `_check_cortex_search` | Search service status = ACTIVE |
| `step-7` | `_check_agent` | Agent responds to test query |
| `step-8` | `_check_forecast` | Forecast model trained |
| `step-9` | `_check_streamlit` | Streamlit app deployed |
| `step-10` | `_check_all` | Full end-to-end smoke test |

## Examples

```bash
# Check if step-2 prerequisites are met (verifies step-1 and setup)
uv run gate --step step-2 --prior-step step-1 --action check

# Mark step-3 as in-progress
uv run gate --step step-3 --desc "Creating schema and loading data" --action start

# Show dry-run plan for step-3
uv run gate --step step-3 --action dry-run

# Mark step-3 complete
uv run gate --step step-3 --action complete

# Reset step-3 state (for re-running)
uv run gate --step step-3 --action reset
```

## Exit Codes

- `0` — PASS (check succeeded, or action completed)
- `1` — BLOCK (prerequisite not met, or check failed)
