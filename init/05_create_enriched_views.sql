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

-- Create enriched views that JOIN base tables with enrichment data
-- These views provide combined data for analytics

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

-- View: street_lights_enriched
-- Combines lights with all enrichment data (current season)
CREATE OR REPLACE VIEW streetlights.street_lights_enriched AS
SELECT 
    -- Base light data
    l.light_id,
    l.latitude,
    l.longitude,
    l.status,
    l.wattage,
    l.installation_date,
    l.last_maintenance,
    l.neighborhood_id,
    l.created_at,
    l.updated_at,
    
    -- Neighborhood data
    n.name as neighborhood_name,
    n.population,
    
    -- Weather enrichment (current season)
    w.season,
    w.avg_temperature_c,
    w.rainfall_mm,
    w.failure_risk_score,
    w.predicted_failure_date,
    
    -- Demographics enrichment
    d.population_density,
    d.urban_classification,
    
    -- Power grid enrichment
    p.grid_zone,
    p.avg_load_percent,
    p.outage_history_count,
    
    -- Calculated fields
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, l.installation_date)) * 12 + 
        EXTRACT(MONTH FROM AGE(CURRENT_DATE, l.installation_date)) as age_months,
    
    EXTRACT(DAY FROM AGE(CURRENT_DATE, l.last_maintenance)) as days_since_maintenance,
    
    -- Maintenance urgency based on predicted failure date
    CASE 
        WHEN w.predicted_failure_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'CRITICAL'
        WHEN w.predicted_failure_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'HIGH'
        WHEN w.predicted_failure_date <= CURRENT_DATE + INTERVAL '90 days' THEN 'MEDIUM'
        ELSE 'LOW'
    END as maintenance_urgency

FROM streetlights.street_lights l

-- Join neighborhood
LEFT JOIN streetlights.neighborhoods n ON l.neighborhood_id = n.neighborhood_id

-- Join weather enrichment for current season
LEFT JOIN streetlights.weather_enrichment w ON l.light_id = w.light_id 
    AND w.season = CASE 
        WHEN EXTRACT(MONTH FROM CURRENT_DATE) BETWEEN 3 AND 5 THEN 'spring'
        WHEN EXTRACT(MONTH FROM CURRENT_DATE) BETWEEN 6 AND 8 THEN 'summer'
        WHEN EXTRACT(MONTH FROM CURRENT_DATE) BETWEEN 9 AND 11 THEN 'fall'
        ELSE 'winter'
    END

-- Join demographics enrichment
LEFT JOIN streetlights.demographics d ON n.neighborhood_id = d.neighborhood_id

-- Join power grid enrichment
LEFT JOIN streetlights.power_grid_zones p ON l.light_id = p.light_id;

COMMENT ON VIEW streetlights.street_lights_enriched IS 'Enriched view combining lights with all contextual data (current season)';

-- View: maintenance_requests_enriched
-- Combines maintenance requests with location and enrichment context
CREATE OR REPLACE VIEW streetlights.maintenance_requests_enriched AS
SELECT 
    -- Maintenance request data
    m.request_id,
    m.light_id,
    m.reported_at,
    m.resolved_at,
    m.issue_type,
    m.description,
    m.created_at,
    
    -- Light location data
    l.latitude,
    l.longitude,
    l.wattage,
    l.neighborhood_id,
    
    -- Neighborhood data
    n.name as neighborhood_name,
    n.population,
    
    -- Weather enrichment at time of report
    w.season,
    w.failure_risk_score,
    w.avg_temperature_c,
    w.rainfall_mm,
    
    -- Calculated fields
    CASE 
        WHEN m.resolved_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (m.resolved_at - m.reported_at)) / 3600.0
        ELSE NULL 
    END as resolution_hours,
    
    CASE 
        WHEN m.resolved_at IS NULL THEN 'OPEN'
        ELSE 'CLOSED'
    END as status

FROM streetlights.maintenance_requests m

-- Join light
INNER JOIN streetlights.street_lights l ON m.light_id = l.light_id

-- Join neighborhood
LEFT JOIN streetlights.neighborhoods n ON l.neighborhood_id = n.neighborhood_id

-- Join weather enrichment for season at time of report
LEFT JOIN streetlights.weather_enrichment w ON l.light_id = w.light_id 
    AND w.season = CASE 
        WHEN EXTRACT(MONTH FROM m.reported_at) BETWEEN 3 AND 5 THEN 'spring'
        WHEN EXTRACT(MONTH FROM m.reported_at) BETWEEN 6 AND 8 THEN 'summer'
        WHEN EXTRACT(MONTH FROM m.reported_at) BETWEEN 9 AND 11 THEN 'fall'
        ELSE 'winter'
    END;

COMMENT ON VIEW streetlights.maintenance_requests_enriched IS 'Maintenance requests with location and enrichment context';

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Enriched views created successfully!';
    RAISE NOTICE '  - street_lights_enriched (main analytics view)';
    RAISE NOTICE '  - maintenance_requests_enriched';
END $$;
