-- Copyright 2025 Kamesh Sampath
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- Create enrichment tables
-- These tables store contextual data separate from operational data
-- Approach: Database tables + views (not external APIs) for demo reliability

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

-- Table: weather_enrichment
-- Seasonal weather patterns affecting light failure rates
CREATE TABLE IF NOT EXISTS streetlights.weather_enrichment (
    light_id TEXT REFERENCES streetlights.street_lights(light_id),
    season TEXT NOT NULL CHECK (season IN ('monsoon', 'summer', 'winter')),
    avg_temperature_c NUMERIC(5,2),
    rainfall_mm NUMERIC(6,2),
    failure_risk_score NUMERIC(3,2) CHECK (failure_risk_score BETWEEN 0 AND 1),
    predicted_failure_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (light_id, season)
);

COMMENT ON TABLE streetlights.weather_enrichment IS 'Seasonal weather patterns per light for predictive maintenance';
COMMENT ON COLUMN streetlights.weather_enrichment.season IS 'Season: monsoon (Jun-Sep), summer (Mar-May), winter (Dec-Feb)';
COMMENT ON COLUMN streetlights.weather_enrichment.failure_risk_score IS 'Predicted failure risk: 0.0 (low) to 1.0 (high)';
COMMENT ON COLUMN streetlights.weather_enrichment.predicted_failure_date IS 'ML-predicted failure date (mock data for Phase 1-5)';

-- Table: demographics_enrichment
-- Neighborhood characteristics for resource planning
CREATE TABLE IF NOT EXISTS streetlights.demographics_enrichment (
    neighborhood_id TEXT PRIMARY KEY REFERENCES streetlights.neighborhoods(neighborhood_id),
    population_density INTEGER,
    urban_classification TEXT CHECK (urban_classification IN ('urban', 'suburban', 'rural')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE streetlights.demographics_enrichment IS 'Neighborhood demographics for resource allocation';
COMMENT ON COLUMN streetlights.demographics_enrichment.population_density IS 'People per square kilometer';
COMMENT ON COLUMN streetlights.demographics_enrichment.urban_classification IS 'Development level: urban, suburban, or rural';

-- Table: power_grid_enrichment
-- Electrical infrastructure context per light
CREATE TABLE IF NOT EXISTS streetlights.power_grid_enrichment (
    light_id TEXT PRIMARY KEY REFERENCES streetlights.street_lights(light_id),
    grid_zone TEXT NOT NULL,
    avg_load_percent NUMERIC(5,2),
    outage_history_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE streetlights.power_grid_enrichment IS 'Power grid data for each light';
COMMENT ON COLUMN streetlights.power_grid_enrichment.grid_zone IS 'Power grid zone identifier (e.g., ZONE-A, ZONE-B)';
COMMENT ON COLUMN streetlights.power_grid_enrichment.avg_load_percent IS 'Average grid load percentage (0-100)';
COMMENT ON COLUMN streetlights.power_grid_enrichment.outage_history_count IS 'Number of historical power outages';

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Enrichment tables created successfully!';
    RAISE NOTICE '  - weather_enrichment (seasonal patterns)';
    RAISE NOTICE '  - demographics_enrichment (neighborhood data)';
    RAISE NOTICE '  - power_grid_enrichment (electrical grid data)';
    RAISE NOTICE 'Note: These tables will be populated by data generation scripts';
END $$;


