-- Load generated CSV data into PostgreSQL database
-- Run this script after generating data with Python scripts

-- Enable timing for performance monitoring
\timing on

-- Set search path to streetlights schema
SET search_path TO streetlights, public;

\echo ''
\echo '============================================'
\echo 'Loading data into PostgreSQL database...'
\echo '============================================'

-- Load neighborhoods
\echo ''
\echo '1. Loading neighborhoods...'
\copy streetlights.neighborhoods(neighborhood_id, name, boundary, population) FROM 'data/neighborhoods.csv' WITH (FORMAT csv, HEADER true);
SELECT COUNT(*) AS neighborhoods_loaded FROM streetlights.neighborhoods;

-- Load street lights
\echo ''
\echo '2. Loading street lights...'
\copy streetlights.street_lights(light_id, location, status, wattage, installation_date, last_maintenance, neighborhood_id) FROM 'data/street_lights.csv' WITH (FORMAT csv, HEADER true);
SELECT COUNT(*) AS lights_loaded FROM streetlights.street_lights;

-- Load maintenance requests
\echo ''
\echo '3. Loading maintenance requests...'
-- Note: resolved_at can be empty, handle NULL properly
\copy streetlights.maintenance_requests(request_id, light_id, reported_at, resolved_at, issue_type) FROM 'data/maintenance_requests.csv' WITH (FORMAT csv, HEADER true, NULL '');
SELECT COUNT(*) AS requests_loaded FROM streetlights.maintenance_requests;

-- Load suppliers
\echo ''
\echo '4. Loading suppliers...'
\copy streetlights.suppliers(supplier_id, name, location, contact_phone, service_radius_km, avg_response_hours, specialization) FROM 'data/suppliers.csv' WITH (FORMAT csv, HEADER true);
SELECT COUNT(*) AS suppliers_loaded FROM streetlights.suppliers;

-- Load weather enrichment
\echo ''
\echo '5. Loading weather enrichment...'
\copy streetlights.weather_enrichment(light_id, season, avg_temperature_c, rainfall_mm, failure_risk_score, predicted_failure_date) FROM 'data/weather_enrichment.csv' WITH (FORMAT csv, HEADER true, NULL '');
SELECT COUNT(*) AS weather_records_loaded FROM streetlights.weather_enrichment;

-- Load demographics enrichment
\echo ''
\echo '6. Loading demographics enrichment...'
\copy streetlights.demographics_enrichment(neighborhood_id, population_density, urban_classification) FROM 'data/demographics_enrichment.csv' WITH (FORMAT csv, HEADER true);
SELECT COUNT(*) AS demographics_records_loaded FROM streetlights.demographics_enrichment;

-- Load power grid enrichment
\echo ''
\echo '7. Loading power grid enrichment...'
\copy streetlights.power_grid_enrichment(light_id, grid_zone, avg_load_percent, outage_history_count) FROM 'data/power_grid_enrichment.csv' WITH (FORMAT csv, HEADER true);
SELECT COUNT(*) AS power_grid_records_loaded FROM streetlights.power_grid_enrichment;

-- Data validation queries
\echo ''
\echo '============================================'
\echo 'Data Validation Checks'
\echo '============================================'

-- Check: All lights should be within neighborhoods
\echo ''
\echo 'Checking spatial integrity...'
SELECT COUNT(*) AS lights_within_neighborhoods
FROM streetlights.street_lights l
JOIN streetlights.neighborhoods n ON ST_Within(l.location, n.boundary);

SELECT COUNT(*) AS lights_outside_neighborhoods
FROM streetlights.street_lights l
WHERE NOT EXISTS (
    SELECT 1 FROM streetlights.neighborhoods n WHERE ST_Within(l.location, n.boundary)
);

-- Status distribution
\echo ''
\echo 'Light status distribution:'
SELECT status, COUNT(*) AS count, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM streetlights.street_lights), 2) AS percentage
FROM streetlights.street_lights
GROUP BY status
ORDER BY count DESC;

-- Lights per neighborhood (top 10)
\echo ''
\echo 'Top 10 neighborhoods by light count:'
SELECT n.name, COUNT(l.light_id) AS light_count
FROM streetlights.neighborhoods n
LEFT JOIN streetlights.street_lights l ON ST_Within(l.location, n.boundary)
GROUP BY n.name
ORDER BY light_count DESC
LIMIT 10;

-- Maintenance requests summary
\echo ''
\echo 'Maintenance requests summary:'
SELECT 
    COUNT(*) AS total_requests,
    COUNT(CASE WHEN resolved_at IS NULL THEN 1 END) AS open_requests,
    COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END) AS closed_requests
FROM streetlights.maintenance_requests;

-- Enrichment coverage
\echo ''
\echo 'Enrichment data coverage:'
SELECT 
    (SELECT COUNT(DISTINCT light_id) FROM streetlights.weather_enrichment) AS lights_with_weather,
    (SELECT COUNT(DISTINCT light_id) FROM streetlights.power_grid_enrichment) AS lights_with_power_grid,
    (SELECT COUNT(DISTINCT neighborhood_id) FROM streetlights.demographics_enrichment) AS neighborhoods_with_demographics,
    (SELECT COUNT(*) FROM streetlights.street_lights) AS total_lights,
    (SELECT COUNT(*) FROM streetlights.neighborhoods) AS total_neighborhoods;

-- Test enriched view
\echo ''
\echo 'Testing enriched view (sample 5 records):'
SELECT light_id, status, neighborhood_name, season, failure_risk_score, maintenance_urgency
FROM streetlights.street_lights_enriched
WHERE status = 'faulty'
LIMIT 5;

-- Supplier coverage check
\echo ''
\echo 'Supplier specialization distribution:'
SELECT specialization, COUNT(*) AS count
FROM streetlights.suppliers
GROUP BY specialization
ORDER BY count DESC;

\echo ''
\echo '============================================'
\echo 'Data loading complete!'
\echo '============================================'
\echo ''
\echo 'Next steps:'
\echo '  1. Verify enriched views: SELECT * FROM street_lights_enriched LIMIT 10;'
\echo '  2. Test spatial queries: See queries/postgis/'
\echo '  3. Start Streamlit dashboard: http://localhost:8501'
\echo ''

