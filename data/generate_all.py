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
Generate all sample data for street lights demo
Runs all data generators in the correct order
"""
import os
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
    """Run all data generators in sequence"""
    print("=" * 50)
    print("Street Lights Demo - Data Generation")
    print("=" * 50)
    print()
    
    # Change to data directory so CSV files are written there
    data_dir = Path(__file__).parent
    original_dir = os.getcwd()
    os.chdir(data_dir)
    print(f"Working directory: {data_dir}")
    print()
    
    generators = [
        ("neighborhoods", generate_neighborhoods.main),
        ("street lights", generate_street_lights.main),
        ("maintenance history", generate_maintenance_history.main),
        ("suppliers", generate_suppliers.main),
        ("enrichment data", generate_enrichment_data.main),
    ]
    
    try:
        for i, (name, func) in enumerate(generators, 1):
            print(f"Step {i}/{len(generators)}: Generating {name}...")
            try:
                func()
                print()
            except Exception as e:
                print(f"Error generating {name}: {e}", file=sys.stderr)
                sys.exit(1)
    finally:
        # Restore original directory
        os.chdir(original_dir)
    
    # Summary
    print("=" * 50)
    print("Full Data Generation Complete!")
    print("=" * 50)
    print()
    print("Generated files in data/ directory:")
    
    data_dir = Path(__file__).parent
    # List full dataset files (not sample_*)
    full_files = [
        "neighborhoods.csv",
        "street_lights.csv", 
        "maintenance_requests.csv",
        "suppliers.csv",
        "weather_enrichment.csv",
        "demographics_enrichment.csv",
        "power_grid_enrichment.csv",
    ]
    for filename in full_files:
        csv_file = data_dir / filename
        if csv_file.exists():
            size = csv_file.stat().st_size
            size_kb = size / 1024
            print(f"  {filename} ({size_kb:.1f} KB)")
    
    print()
    print("Next steps:")
    print("  1. Load data into PostgreSQL:")
    print("     psql -U snowflake_admin -d postgres -f ./data/load_data.sql")
    print()
    print("  2. Or use psql from host (if PostgreSQL client installed):")
    print("     psql -h localhost -U snowflake_admin -d postgres -f data/load_data.sql")
    print()
    print("  3. Verify data loaded:")
    print("     psql -U snowflake_admin -d postgres -c 'SELECT COUNT(*) FROM streetlights.street_lights;'")
    print()


if __name__ == "__main__":
    main()

