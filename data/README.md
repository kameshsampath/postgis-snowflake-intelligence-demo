# Data Generation Scripts

This directory contains scripts to generate synthetic data for the Street Lights Maintenance demo.

> **DISCLAIMER**: All data is fictitious. See [DATA_DISCLAIMER.md](DATA_DISCLAIMER.md) for details.

---

## 📄 Files Overview

### Documentation
- **[SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md)** - Complete database schema reference with examples
- **[DATA_DISCLAIMER.md](DATA_DISCLAIMER.md)** - Legal disclaimer about fictitious data

### Data Generation Scripts (Python)
- **`generate_neighborhoods.py`** - Generate neighborhood polygons
- **`generate_street_lights.py`** - Generate street light locations and status
- **`generate_maintenance_history.py`** - Generate maintenance request history
- **`generate_suppliers.py`** - Generate supplier locations and details
- **`generate_enrichment_data.py`** - Generate weather, demographics, and power grid enrichment
- **`generate_all.py`** - Master script that calls all generators
- **`generate_all_data.sh`** - Shell wrapper to run all generators

### Database Loading Scripts (SQL)
- **`load_data.sql`** - Load full generated dataset (5,000 lights)
- **`load_sample_data.sql`** - Load minimal sample data (10 lights) - fast testing

### Sample Data Files (Pre-generated)
- **`sample_neighborhoods.csv`** - 3 sample neighborhoods
- **`sample_street_lights.csv`** - 10 sample street lights
- **`sample_maintenance_requests.csv`** - Sample maintenance history
- **`sample_suppliers.csv`** - 3 sample suppliers
- **`sample_weather_enrichment.csv`** - Weather enrichment for samples
- **`sample_demographics_enrichment.csv`** - Demographics for samples
- **`sample_power_grid_enrichment.csv`** - Power grid data for samples

### Generated Data Files (Git-ignored)
After running generation scripts, these files are created:
- `neighborhoods.csv` (50 neighborhoods)
- `street_lights.csv` (5,000 lights)
- `maintenance_requests.csv` (500 requests)
- `suppliers.csv` (25 suppliers)
- `weather_enrichment.csv` (15,000 records - 3 seasons × 5,000 lights)
- `demographics_enrichment.csv` (50 records)
- `power_grid_enrichment.csv` (5,000 records)

---

## 🚀 Quick Start

### Option 1: Use Sample Data (Fastest - No Dependencies)

Perfect for quick testing and demos:

```bash
# From project root
docker exec -it streetlights-postgres psql -U postgres -d streetlights -f /data/load_sample_data.sql
```

**What you get:**
- 3 neighborhoods
- 10 street lights
- Sample enrichment data
- Ready in seconds

### Option 2: Generate Full Dataset

For realistic testing and presentations:

```bash
# Install dependencies (if not already)
uv pip install -e .
# or: pip install -e .

# Generate all data
cd data
./generate_all_data.sh

# Load into database
cd ..
docker exec -it streetlights-postgres psql -U postgres -d streetlights -f /data/load_data.sql
```

**What you get:**
- 50 neighborhoods across Bengaluru
- 5,000 street lights with realistic distribution
- 500 maintenance requests
- 25 suppliers with service coverage
- 15,000 enrichment records (seasonal data)

---

## 📊 Data Generation Details

### Neighborhoods (`generate_neighborhoods.py`)
- **Count**: 50 neighborhoods
- **Location**: Bengaluru city bounds (12.8-13.1°N, 77.5-77.7°E)
- **Features**: 
  - Realistic polygon boundaries
  - Population ranges from 50,000 to 200,000
  - Unique names with "-nagar" suffix

### Street Lights (`generate_street_lights.py`)
- **Count**: 5,000 lights
- **Distribution**: 
  - Evenly distributed within neighborhood boundaries
  - Realistic clustering patterns
- **Status Distribution**:
  - 85% operational
  - 10% maintenance_required
  - 5% faulty
- **Wattage**: 100W, 150W, or 200W
- **Installation Dates**: 2015-2023 range

### Maintenance Requests (`generate_maintenance_history.py`)
- **Count**: 500 historical requests
- **Issue Types**: bulb_failure, wiring, pole_damage, electrical
- **Resolution**: 80% resolved, 20% still open
- **Response Time**: 2-72 hours (realistic variation)

### Suppliers (`generate_suppliers.py`)
- **Count**: 25 suppliers
- **Names**: All fictitious (see DATA_DISCLAIMER.md)
- **Coverage**: 5-15 km service radius
- **Response Time**: 2-8 hours average
- **Specialization**: LED, Sodium Vapor, or All

### Enrichment Data (`generate_enrichment_data.py`)

#### Weather Enrichment
- **3 seasons** per light (monsoon, summer, winter)
- **Failure Risk Scores**: 
  - Monsoon: 0.7-0.9 (high)
  - Summer: 0.5-0.7 (medium)
  - Winter: 0.2-0.4 (low)
- **Predicted Failure Dates**: Calculated based on risk + age

#### Demographics Enrichment
- **Population Density**: 5,000-15,000 per sq km
- **Urban Classification**: urban, suburban, rural

#### Power Grid Enrichment
- **Grid Zones**: ZONE-A through ZONE-E
- **Load Percentage**: 60-95%
- **Outage History**: 0-10 historical outages

---

## 🔄 Regenerating Data

You can regenerate data at any time:

```bash
cd data

# Regenerate specific dataset
python generate_neighborhoods.py
python generate_street_lights.py
# ... etc

# Or regenerate everything
./generate_all_data.sh
```

**Note**: Regeneration creates new random data. If you want reproducible data, modify the scripts to set a random seed.

---

## 📋 Dependencies

Python packages required (defined in `requirements.txt`):

```bash
shapely>=2.0.0      # Spatial geometry handling
faker>=18.0.0       # Realistic data generation (not used in current version)
```

Install with:
```bash
uv pip install -r requirements.txt
# or: pip install -r requirements.txt
```

---

## 🧪 Testing Generated Data

After generation, verify the data:

```bash
# Check file sizes
ls -lh *.csv

# Check record counts
wc -l *.csv

# Preview data
head neighborhoods.csv
head street_lights.csv
```

Expected line counts (including header):
- `neighborhoods.csv`: 51 lines (50 + header)
- `street_lights.csv`: 5001 lines (5000 + header)
- `maintenance_requests.csv`: 501 lines (500 + header)
- `suppliers.csv`: 26 lines (25 + header)
- `weather_enrichment.csv`: 15001 lines (15000 + header)

---

## 🔗 Related Documentation

- **[SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md)** - Full schema documentation with SQL examples
- **[DATA_DISCLAIMER.md](DATA_DISCLAIMER.md)** - Legal information about fictitious data
- **[../init/README.md](../init/README.md)** - Database initialization and spatial functions
- **[../README.md](../README.md)** - Project overview

---

## 💡 Tips

1. **Start with sample data** for quick testing
2. **Generate full dataset** when you need realistic volumes
3. **Customize generation** by editing the Python scripts
4. **Add variety** by changing distribution parameters
5. **Set random seeds** if you need reproducible data

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Install dependencies
uv pip install -e .
```

### CSV files not loading
```bash
# Check file permissions
chmod 644 *.csv

# Verify CSV format
head -n 3 street_lights.csv
```

### Database load fails
```bash
# Ensure database is ready
docker exec -it streetlights-postgres psql -U postgres -d streetlights -c "SELECT COUNT(*) FROM street_lights;"

# Reload from scratch
docker exec -it streetlights-postgres psql -U postgres -d streetlights -c "TRUNCATE street_lights CASCADE;"
```

---

**Generated data is for demonstration and educational purposes only.**

