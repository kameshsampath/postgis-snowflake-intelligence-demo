#!/bin/bash
# Generate all sample data for street lights demo
# This script runs all Python data generators in the correct order

set -e  # Exit on error

echo "========================================"
echo "Street Lights Demo - Data Generation"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found"
    exit 1
fi

# Check if in correct directory
if [ ! -f "generate_neighborhoods.py" ]; then
    echo "Error: Please run this script from the data/ directory"
    echo "Usage: cd data && ./generate_all_data.sh"
    exit 1
fi

# Install Python dependencies if needed
echo "Checking Python dependencies..."
if ! python3 -c "import shapely" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip3 install --user -r requirements.txt
    echo ""
fi

# Step 1: Generate neighborhoods
echo "Step 1/5: Generating neighborhoods..."
python3 generate_neighborhoods.py
echo ""

# Step 2: Generate street lights (depends on neighborhoods)
echo "Step 2/5: Generating street lights..."
python3 generate_street_lights.py
echo ""

# Step 3: Generate maintenance history (depends on lights)
echo "Step 3/5: Generating maintenance request history..."
python3 generate_maintenance_history.py
echo ""

# Step 4: Generate suppliers
echo "Step 4/5: Generating suppliers..."
python3 generate_suppliers.py
echo ""

# Step 5: Generate enrichment data (depends on lights and neighborhoods)
echo "Step 5/5: Generating enrichment data..."
python3 generate_enrichment_data.py
echo ""

# Summary
echo "========================================"
echo "Data Generation Complete!"
echo "========================================"
echo ""
echo "Generated files:"
ls -lh *.csv | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Next steps:"
echo "  1. Load data into PostgreSQL:"
echo "     psql -U snowflake_admin -d postgres -f ./data/load_data.sql"
echo ""
echo "  2. Or use psql from host (if PostgreSQL client installed):"
echo "     psql -h localhost -U snowflake_admin -d postgres -f load_data.sql"
echo ""
echo "  3. Verify data loaded:"
echo "     psql -U snowflake_admin -d postgres -c 'SELECT COUNT(*) FROM street_lights;'"
echo ""


