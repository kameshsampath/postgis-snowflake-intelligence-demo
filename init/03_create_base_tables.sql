-- Create base tables for street lights maintenance system
-- These tables contain operational data

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

-- Table: neighborhoods
-- Geographic boundaries and metadata for city neighborhoods
CREATE TABLE IF NOT EXISTS streetlights.neighborhoods (
    neighborhood_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    boundary GEOMETRY(Polygon, 4326) NOT NULL,
    population INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE streetlights.neighborhoods IS 'City neighborhoods with geographic boundaries';
COMMENT ON COLUMN streetlights.neighborhoods.boundary IS 'Polygon boundary in WGS84 (SRID 4326)';

-- Table: street_lights
-- Operational data for all street lights
CREATE TABLE IF NOT EXISTS streetlights.street_lights (
    light_id TEXT PRIMARY KEY,
    location GEOMETRY(Point, 4326) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('operational', 'faulty', 'maintenance_required')),
    wattage INTEGER,
    installation_date DATE,
    last_maintenance TIMESTAMP,
    neighborhood_id TEXT REFERENCES streetlights.neighborhoods(neighborhood_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE streetlights.street_lights IS 'Street lights with spatial locations and operational status';
COMMENT ON COLUMN streetlights.street_lights.location IS 'GPS coordinates in WGS84 (SRID 4326)';
COMMENT ON COLUMN streetlights.street_lights.status IS 'Current operational status: operational, faulty, or maintenance_required';

-- Table: maintenance_requests
-- Historical and active maintenance requests
CREATE TABLE IF NOT EXISTS streetlights.maintenance_requests (
    request_id TEXT PRIMARY KEY,
    light_id TEXT NOT NULL REFERENCES streetlights.street_lights(light_id),
    reported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    issue_type TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE streetlights.maintenance_requests IS 'Maintenance request history for street lights';
COMMENT ON COLUMN streetlights.maintenance_requests.issue_type IS 'Type of issue: bulb_failure, wiring, pole_damage, etc.';
COMMENT ON COLUMN streetlights.maintenance_requests.description IS 'Free-text description of the issue reported by field staff or residents';

-- Table: suppliers
-- Light equipment suppliers and their service coverage
CREATE TABLE IF NOT EXISTS streetlights.suppliers (
    supplier_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    contact_phone TEXT,
    service_radius_km INTEGER,
    avg_response_hours INTEGER,
    specialization TEXT CHECK (specialization IN ('LED', 'Sodium Vapor', 'All')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE streetlights.suppliers IS 'Light equipment suppliers with service coverage areas';
COMMENT ON COLUMN streetlights.suppliers.location IS 'Supplier office location in WGS84 (SRID 4326)';
COMMENT ON COLUMN streetlights.suppliers.service_radius_km IS 'Maximum service coverage radius in kilometers';

-- Trigger to update updated_at timestamp on street_lights
CREATE OR REPLACE FUNCTION streetlights.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_street_lights_updated_at ON streetlights.street_lights;

CREATE TRIGGER update_street_lights_updated_at
BEFORE UPDATE ON streetlights.street_lights
FOR EACH ROW
EXECUTE FUNCTION streetlights.update_updated_at_column();

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Base tables created successfully!';
    RAISE NOTICE '  - neighborhoods';
    RAISE NOTICE '  - street_lights';
    RAISE NOTICE '  - maintenance_requests';
    RAISE NOTICE '  - suppliers';
END $$;


