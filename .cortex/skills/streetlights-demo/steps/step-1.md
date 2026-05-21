---
name: streetlights-demo-step-1
description: Generate location-aware synthetic streetlight data
---

# Step 1: Generate Synthetic Data

## What we'll do

Generate 7 CSV files of synthetic streetlight data (lights, maintenance records, energy consumption, sensors, weather, demographics, power grid zones) centered on the configured city.

- Run the data generator with city coordinates from manifest
- Produce ~500 street lights plus related tables
- Output to `data/` directory

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Step 1"
- Question: "Ready to generate synthetic data for your city?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

1. Read city and coordinates from manifest
2. Run data generation:
   ```bash
   uv run generate --city "{city}" --lat {lat} --lng {lng} --count 500
   ```
3. Verify output: check that 7 CSV files exist in `data/`
4. Show summary table: file name, row count, sample columns

### Expected Output Files

| File | Contents |
|------|----------|
| `data/street_lights.csv` | Light locations, status, installation info |
| `data/maintenance_records.csv` | Maintenance history with descriptions |
| `data/energy_consumption.csv` | Hourly energy readings per light |
| `data/light_sensors.csv` | Sensor readings (lux, temperature) |
| `data/weather_enrichment.csv` | Seasonal weather patterns |
| `data/demographics.csv` | Neighborhood population data |
| `data/power_grid_zones.csv` | Grid zone assignments |

### Error Handling

- If `uv run` fails: check that dependencies are installed (`uv sync`)
- If location auto-detect was used and fails: ask user for city override

## What we did

- ✅ Generated 7 CSV files in `data/`
- ✅ Data centered on configured city coordinates
- ✅ All files have expected row counts
