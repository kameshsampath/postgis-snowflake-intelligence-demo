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

-- Create indexes for performance
-- B-tree indexes on lat/lng and common filter/join columns

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

-- B-tree indexes on street_lights lat/lng for coordinate queries
CREATE INDEX IF NOT EXISTS idx_lights_latitude ON streetlights.street_lights(latitude);
CREATE INDEX IF NOT EXISTS idx_lights_longitude ON streetlights.street_lights(longitude);
COMMENT ON INDEX streetlights.idx_lights_latitude IS 'Fast filtering by latitude range';
COMMENT ON INDEX streetlights.idx_lights_longitude IS 'Fast filtering by longitude range';

-- B-tree indexes on suppliers lat/lng
CREATE INDEX IF NOT EXISTS idx_suppliers_latitude ON streetlights.suppliers(latitude);
CREATE INDEX IF NOT EXISTS idx_suppliers_longitude ON streetlights.suppliers(longitude);
COMMENT ON INDEX streetlights.idx_suppliers_latitude IS 'Fast filtering by supplier latitude';
COMMENT ON INDEX streetlights.idx_suppliers_longitude IS 'Fast filtering by supplier longitude';

-- Regular B-tree indexes for foreign keys and common filters
CREATE INDEX IF NOT EXISTS idx_lights_status ON streetlights.street_lights(status);
COMMENT ON INDEX streetlights.idx_lights_status IS 'Fast filtering by light status (operational, faulty, maintenance_required)';

CREATE INDEX IF NOT EXISTS idx_lights_neighborhood ON streetlights.street_lights(neighborhood_id);
COMMENT ON INDEX streetlights.idx_lights_neighborhood IS 'Fast JOIN with neighborhoods table';

CREATE INDEX IF NOT EXISTS idx_maintenance_light ON streetlights.maintenance_requests(light_id);
COMMENT ON INDEX streetlights.idx_maintenance_light IS 'Fast JOIN with street_lights table';

CREATE INDEX IF NOT EXISTS idx_maintenance_reported ON streetlights.maintenance_requests(reported_at);
COMMENT ON INDEX streetlights.idx_maintenance_reported IS 'Fast filtering by report date';

CREATE INDEX IF NOT EXISTS idx_weather_light ON streetlights.weather_enrichment(light_id);
COMMENT ON INDEX streetlights.idx_weather_light IS 'Fast JOIN for enrichment';

CREATE INDEX IF NOT EXISTS idx_weather_season ON streetlights.weather_enrichment(season);
COMMENT ON INDEX streetlights.idx_weather_season IS 'Fast filtering by season';

CREATE INDEX IF NOT EXISTS idx_power_grid_light ON streetlights.power_grid_zones(light_id);
COMMENT ON INDEX streetlights.idx_power_grid_light IS 'Fast JOIN for enrichment';

-- Analyze tables for query optimizer
ANALYZE streetlights.neighborhoods;
ANALYZE streetlights.street_lights;
ANALYZE streetlights.maintenance_requests;
ANALYZE streetlights.suppliers;
ANALYZE streetlights.weather_enrichment;
ANALYZE streetlights.demographics;
ANALYZE streetlights.power_grid_zones;

-- Log completion with index statistics
DO $$
DECLARE
    idx_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO idx_count 
    FROM pg_indexes 
    WHERE schemaname = 'streetlights';
    
    RAISE NOTICE 'Indexes created successfully!';
    RAISE NOTICE 'B-tree indexes:';
    RAISE NOTICE '  - idx_lights_latitude, idx_lights_longitude';
    RAISE NOTICE '  - idx_suppliers_latitude, idx_suppliers_longitude';
    RAISE NOTICE '  - idx_lights_status';
    RAISE NOTICE '  - idx_lights_neighborhood';
    RAISE NOTICE '  - idx_maintenance_light';
    RAISE NOTICE '  - idx_maintenance_reported';
    RAISE NOTICE '  - idx_weather_light';
    RAISE NOTICE '  - idx_weather_season';
    RAISE NOTICE '  - idx_power_grid_light';
    RAISE NOTICE 'Total indexes in streetlights schema: %', idx_count;
    RAISE NOTICE 'Tables analyzed for query optimization';
END $$;
