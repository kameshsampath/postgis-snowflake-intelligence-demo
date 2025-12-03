#!/usr/bin/env python3
# Copyright 2025 Kamesh Sampath
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate small sample data for quick testing and demos.
Creates sample_*.csv files with minimal records.

Sample sizes:
- 5 neighborhoods
- 10 street lights
- 10 maintenance requests
- 3 suppliers
- Enrichment data for all lights/neighborhoods
"""
import sys
from pathlib import Path

# Import all the generator modules
from data import (
    generate_neighborhoods,
    generate_street_lights,
    generate_maintenance_history,
    generate_suppliers,
    generate_enrichment_data,
)


def main():
    """Generate sample datasets with smaller counts"""
    print("=" * 50)
    print("Street Lights Demo - Sample Data Generation")
    print("=" * 50)
    print()
    print("Generating small sample datasets for quick testing...")
    print()
    
    data_dir = Path(__file__).parent
    
    # Step 1: Generate sample neighborhoods (5)
    print("Step 1/5: Generating sample neighborhoods...")
    neighborhoods = generate_neighborhoods.generate_neighborhoods(count=5)
    generate_neighborhoods.save_to_csv(neighborhoods, str(data_dir / "sample_neighborhoods.csv"))
    print()
    
    # Step 2: Generate sample street lights (10)
    print("Step 2/5: Generating sample street lights...")
    lights = generate_street_lights.generate_street_lights(neighborhoods, count=10)
    generate_street_lights.save_to_csv(lights, str(data_dir / "sample_street_lights.csv"))
    print()
    
    # Step 3: Generate sample maintenance requests (10)
    print("Step 3/5: Generating sample maintenance requests...")
    requests = generate_maintenance_history.generate_maintenance_requests(lights, count=10)
    generate_maintenance_history.save_to_csv(requests, str(data_dir / "sample_maintenance_requests.csv"))
    print()
    
    # Step 4: Generate sample suppliers (3)
    print("Step 4/5: Generating sample suppliers...")
    suppliers = generate_suppliers.generate_suppliers(count=3)
    generate_suppliers.save_to_csv(suppliers, str(data_dir / "sample_suppliers.csv"))
    print()
    
    # Step 5: Generate sample enrichment data
    print("Step 5/5: Generating sample enrichment data...")
    weather, demographics, power_grid = generate_enrichment_data.generate_enrichment_data(
        lights, neighborhoods
    )
    generate_enrichment_data.save_to_csv(
        weather, demographics, power_grid,
        weather_file=str(data_dir / "sample_weather_enrichment.csv"),
        demographics_file=str(data_dir / "sample_demographics_enrichment.csv"),
        power_grid_file=str(data_dir / "sample_power_grid_enrichment.csv")
    )
    print()
    
    # Summary
    print("=" * 50)
    print("Sample Data Generation Complete!")
    print("=" * 50)
    print()
    print("Generated sample files:")
    
    sample_files = sorted(data_dir.glob("sample_*.csv"))
    for csv_file in sample_files:
        with open(csv_file) as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header
        print(f"  {csv_file.name}: {line_count} records")
    
    print()
    print("Next steps:")
    print("  Load sample data into PostgreSQL:")
    print("     psql -f data/load_sample_data.sql")
    print()


if __name__ == "__main__":
    main()

