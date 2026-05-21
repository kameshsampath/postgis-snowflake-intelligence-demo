---
name: streetlights-demo-step-1
description: Generate location-aware synthetic streetlight data
---

# Step 1: Generate Synthetic Data

## Prerequisites

- `.streetlights-demo/manifest.toml` exists (run `$streetlights-demo setup` first)

## Steps

1. Read city and coordinates from manifest
2. Run data generation:
   ```bash
   uv run generate --city "{city}" --lat {lat} --lng {lng} --count 500
   ```
3. Verify output: check that 7 CSV files exist in `data/`
4. Show summary table: file name, row count, sample columns

## Expected Output Files

| File | Contents |
|------|----------|
| `data/street_lights.csv` | Light locations, status, installation info |
| `data/maintenance_records.csv` | Maintenance history with descriptions |
| `data/energy_consumption.csv` | Hourly energy readings per light |
| `data/light_sensors.csv` | Sensor readings (lux, temperature) |
| `data/weather_enrichment.csv` | Seasonal weather patterns |
| `data/demographics.csv` | Neighborhood population data |
| `data/power_grid_zones.csv` | Grid zone assignments |

## Error Handling

- If `uv run` fails: check that dependencies are installed (`uv sync`)
- If location auto-detect was used and fails: ask user for city override
