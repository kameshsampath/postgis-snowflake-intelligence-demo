---
name: streetlights-demo-step-1
description: Generate location-aware synthetic streetlight data
---

## Gate

```bash
uv run gate --step step-1 --prior-step setup --action check
```

If BLOCK: stop and inform the user which prior step needs completing first.
If PASS: continue below.

## Mark IN_PROGRESS

```bash
uv run gate --step step-1 --desc "Generating synthetic data" --action start
```

> ⚠️ **MANDATORY**: Call `enter_plan_mode` immediately after marking the step IN_PROGRESS. Do NOT present any step content until plan mode is active.

# Step 1: Generate Synthetic Data

## Why this matters

**Why synthetic data?** — This demo runs on generated data so it can be reproduced anywhere, by anyone, without needing access to a real municipal database. Synthetic data lets us demonstrate the full technical stack — Iceberg storage, CLD, Semantic View, Cortex AI — with zero dependency on external data sources or privacy concerns.

**Location-aware generation** — The data generator doesn't produce generic coordinates. It uses your configured city's center point and fetches real neighborhood names from OpenStreetMap (Koramangala, Indiranagar, Whitefield for Bangalore; Shoreditch, Canary Wharf for London). This makes the demo visually credible: map links point to real streets, neighborhood names match local knowledge.

**IDD connection** — The `generate --city` command compresses 7 table definitions, ~40,000 rows, and realistic inter-table relationships (light → maintenance records → energy readings → sensor data) into a single invocation. That is [Intent Compression Ratio](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9) in action — intent expressed once, platform executes the complexity.

> ⚠️ **MANDATORY**: Present the "Why this matters" section above to the user verbatim. This is a teaching moment — do NOT skip or summarize it.

## What we'll do

Generate 7 CSV files of synthetic streetlight data (lights, maintenance records, energy consumption, sensors, weather, demographics, power grid zones) centered on the configured city. Neighborhood names are fetched from OpenStreetMap when available (e.g., Koramangala, Indiranagar for Bangalore), with automatic fallback to generated names if unavailable.

- Run the data generator with city coordinates from manifest
- Produce ~2000 street lights plus related tables
- Output to `data/` directory

> **Script**: `scripts/generate_all.py` writes 8 CSV files to `data/` and regenerates `init/02_create_iceberg_tables.sql`

> ⚠️ **MANDATORY**: Present the "What we'll do" summary above to the user before continuing to Dry-Run or Execution.

> ⚠️ **MANDATORY**: Call `exit_plan_mode` with a summary of what data will be generated. Proceed to Execution only after the user confirms.

## Execution

1. Read city and coordinates from manifest
2. Run data generation:
   ```bash
   uv run generate --city "{city}" --lat {lat} --lng {lng} --count 2000
   ```
3. Verify output: check that 7 CSV files exist in `data/`
4. Show summary table: file name, row count, sample columns

### Expected Output Files

| File | Contents |
|------|----------|
| `data/street_lights.csv` | Light locations, status, installation info (~2000 rows) |
| `data/maintenance_records.csv` | Maintenance history with descriptions (~4000 rows) |
| `data/energy_consumption.csv` | Hourly energy readings per light (~288,000 rows) |
| `data/light_sensors.csv` | Sensor readings (lux, temperature) (~8,400 rows) |
| `data/weather_enrichment.csv` | Seasonal weather patterns (365 rows) |
| `data/demographics.csv` | Neighborhood population data (8–16 rows) |
| `data/power_grid_zones.csv` | Grid zone assignments (8–16 rows) |
| `data/intent_log.csv` | Operational intent records (~500 rows) |

### Error Handling

- If `uv run` fails: check that dependencies are installed (`uv sync`)
- If location auto-detect was used and fails: ask user for city override

## What we did

- ✅ Generated 8 CSV files in `data/` (including `intent_log.csv`)
- ✅ Data centered on configured city coordinates
- ✅ All files have expected row counts
- ✅ Neighborhood names: real names from OpenStreetMap (or generated names if OSM unavailable)

> ⚠️ **MANDATORY**: Present the "What we did" checklist above to the user before asking about the next step.

### IDD Metrics — This Step

| Metric | Value |
|---|---|
| **Intent expressed** | 1 — `$streetlights-demo step 1` |
| **Agent operations** | _Count the SQL statements, bash commands, Python scripts, API calls you executed above_ |
| **Traditional ops** | ~12 — (7 schema entities + 1 Python script written + 2 runs + 2 verifications without this skill) |
| **Step ICR** | **12** (12 ops replaced by 1 invocation) |

> Carry forward in session memory — Step 10 compiles the full IDD session summary.

## Mark COMPLETE

```bash
uv run gate --step step-1 --action complete
```

## Next

Use the `ask_user_question` tool:
- Header: "Next"
- Question: "Continue to Step 2: Snowflake Postgres Instance?"
- Options: ["Yes, continue", "Stop here"]

If "Stop here": show `$streetlights-demo step 2` for later resumption.
