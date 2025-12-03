-- Create enriched views that JOIN base tables with enrichment data
-- These views provide combined data for analytics and CDC capture

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

-- View: street_lights_enriched
-- Combines lights with all enrichment data (current season)
CREATE OR REPLACE VIEW streetlights.street_lights_enriched AS
SELECT 
    -- Base light data
    l.light_id,
    l.location,
    ST_X(l.location) as longitude,
    ST_Y(l.location) as latitude,
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
        WHEN EXTRACT(MONTH FROM CURRENT_DATE) BETWEEN 6 AND 9 THEN 'monsoon'
        WHEN EXTRACT(MONTH FROM CURRENT_DATE) BETWEEN 3 AND 5 THEN 'summer'
        ELSE 'winter'
    END

-- Join demographics enrichment
LEFT JOIN streetlights.demographics_enrichment d ON n.neighborhood_id = d.neighborhood_id

-- Join power grid enrichment
LEFT JOIN streetlights.power_grid_enrichment p ON l.light_id = p.light_id;

COMMENT ON VIEW streetlights.street_lights_enriched IS 'Enriched view combining lights with all contextual data (current season)';

-- View: maintenance_requests_enriched
-- Combines maintenance requests with spatial and enrichment context
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
    l.location,
    ST_X(l.location) as longitude,
    ST_Y(l.location) as latitude,
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
        WHEN EXTRACT(MONTH FROM m.reported_at) BETWEEN 6 AND 9 THEN 'monsoon'
        WHEN EXTRACT(MONTH FROM m.reported_at) BETWEEN 3 AND 5 THEN 'summer'
        ELSE 'winter'
    END;

COMMENT ON VIEW streetlights.maintenance_requests_enriched IS 'Maintenance requests with spatial and enrichment context';

-- Create function to get nearest supplier for a light
CREATE OR REPLACE FUNCTION streetlights.get_nearest_supplier(p_light_id TEXT)
RETURNS TABLE (
    supplier_id TEXT,
    supplier_name TEXT,
    distance_km NUMERIC,
    contact_phone TEXT,
    avg_response_hours INTEGER,
    specialization TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.supplier_id,
        s.name as supplier_name,
        ROUND((ST_Distance(s.location::geography, l.location::geography) / 1000.0)::numeric, 2) as distance_km,
        s.contact_phone,
        s.avg_response_hours,
        s.specialization
    FROM streetlights.suppliers s
    CROSS JOIN streetlights.street_lights l
    WHERE l.light_id = p_light_id
    ORDER BY s.location <-> l.location
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION streetlights.get_nearest_supplier(TEXT) IS 'Find nearest supplier to a specific light using KNN operator';

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Enriched views created successfully!';
    RAISE NOTICE '  - street_lights_enriched (main CDC capture view)';
    RAISE NOTICE '  - maintenance_requests_enriched';
    RAISE NOTICE 'Helper functions created:';
    RAISE NOTICE '  - get_nearest_supplier(light_id) - Find nearest supplier to a light';
END $$;


