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

-- ============================================================================
-- PostGIS Queries - Street Lights Maintenance System
-- ============================================================================
-- These queries demonstrate the TECHNICAL COMPLEXITY of spatial SQL.
-- 
-- To answer simple business questions, you need expertise in:
--   - PostGIS functions: ST_Within, ST_Distance, ST_DWithin, ST_MakePoint
--   - Geography vs Geometry types and SRID 4326 projections
--   - Complex JOINs, LATERAL subqueries, CTEs, and window functions
--   - KNN operators (<->) for nearest neighbor searches
--   - Type casting (::geography, ::numeric) and unit conversions
--
-- Compare this with Snowflake Intelligence where you can simply ask:
--   "Which neighborhoods have the most faulty lights?"      → Cortex Analyst
--   "Find the nearest supplier to faulty light SL-0208"     → Cortex Analyst
--   "Find safety hazards and dangerous situations"          → Cortex Search
--   "Show me issues similar to flickering lights"           → Cortex Search
-- ============================================================================

\echo '============================================================================'
\echo 'PostGIS Demo Queries - Street Lights Maintenance System'
\echo '============================================================================'
\echo ''

-- Set search path for convenience
SET search_path TO streetlights, public;

-- ============================================================================
-- 1. OVERVIEW - Data Summary
-- ============================================================================
\echo '>>> 1. Data Overview'
\echo ''

SELECT 
    'Neighborhoods' AS entity,
    COUNT(*)::TEXT AS count
FROM neighborhoods
UNION ALL
SELECT 'Street Lights', COUNT(*)::TEXT FROM street_lights
UNION ALL
SELECT 'Suppliers', COUNT(*)::TEXT FROM suppliers
UNION ALL
SELECT 'Maintenance Requests', COUNT(*)::TEXT FROM maintenance_requests
UNION ALL
SELECT '  └─ Open Requests', COUNT(*)::TEXT FROM maintenance_requests WHERE resolved_at IS NULL
UNION ALL
SELECT '  └─ Closed Requests', COUNT(*)::TEXT FROM maintenance_requests WHERE resolved_at IS NOT NULL;

-- ============================================================================
-- 2. STREET LIGHT STATUS - Distribution by Status
-- ============================================================================
\echo ''
\echo '>>> 2. Street Light Status Distribution'
\echo ''

SELECT 
    status,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS percentage
FROM street_lights
GROUP BY status
ORDER BY count DESC;

-- ============================================================================
-- 3. SPATIAL QUERY - Faulty Lights by Neighborhood
-- ============================================================================
\echo ''
\echo '>>> 3. Faulty Lights by Neighborhood (Top 10)'
\echo ''

SELECT 
    n.name AS neighborhood,
    COUNT(l.light_id) AS faulty_lights,
    n.population,
    ROUND(n.population::NUMERIC / NULLIF(COUNT(l.light_id), 0), 0) AS residents_per_faulty_light
FROM neighborhoods n
LEFT JOIN street_lights l ON ST_Within(l.location, n.boundary) AND l.status = 'faulty'
WHERE l.light_id IS NOT NULL
GROUP BY n.neighborhood_id, n.name, n.population
ORDER BY faulty_lights DESC
LIMIT 10;

-- ============================================================================
-- 4. SPATIAL QUERY - Find Nearest Supplier for Each Faulty Light
-- ============================================================================
\echo ''
\echo '>>> 4. Faulty Lights with Nearest Suppliers (Sample 5)'
\echo ''

SELECT 
    l.light_id,
    n.name AS neighborhood,
    s.name AS nearest_supplier,
    s.specialization,
    ROUND((ST_Distance(l.location::geography, s.location::geography) / 1000.0)::numeric, 2) AS distance_km,
    s.avg_response_hours
FROM street_lights l
JOIN neighborhoods n ON l.neighborhood_id = n.neighborhood_id
CROSS JOIN LATERAL (
    SELECT 
        supplier_id,
        name,
        location,
        specialization,
        avg_response_hours
    FROM suppliers s2
    ORDER BY l.location <-> s2.location
    LIMIT 1
) s
WHERE l.status = 'faulty'
ORDER BY distance_km DESC
LIMIT 5;

-- ============================================================================
-- 5. RISK ANALYSIS - Highest Risk Lights by Failure Score
-- ============================================================================
\echo ''
\echo '>>> 5. Highest Risk Lights (Top 10 by Failure Risk Score)'
\echo ''

SELECT 
    light_id,
    neighborhood_name,
    status,
    season,
    failure_risk_score,
    predicted_failure_date,
    maintenance_urgency,
    days_since_maintenance
FROM street_lights_enriched
WHERE failure_risk_score IS NOT NULL
ORDER BY failure_risk_score DESC, predicted_failure_date
LIMIT 10;

-- ============================================================================
-- 6. SUPPLIER COVERAGE - Lights Within Service Radius
-- ============================================================================
\echo ''
\echo '>>> 6. Supplier Coverage Analysis'
\echo ''

SELECT 
    s.name AS supplier,
    s.specialization,
    s.service_radius_km,
    COUNT(DISTINCT l.light_id) AS lights_in_range,
    COUNT(DISTINCT l.light_id) FILTER (WHERE l.status = 'faulty') AS faulty_in_range,
    COUNT(DISTINCT l.light_id) FILTER (WHERE l.status = 'maintenance_required') AS maintenance_needed_in_range
FROM suppliers s
LEFT JOIN street_lights l ON ST_DWithin(
    s.location::geography, 
    l.location::geography, 
    s.service_radius_km * 1000  -- Convert km to meters
)
GROUP BY s.supplier_id, s.name, s.specialization, s.service_radius_km
ORDER BY faulty_in_range DESC, lights_in_range DESC
LIMIT 10;

-- ============================================================================
-- 7. NEIGHBORHOOD ANALYSIS - Urban Classification & Infrastructure
-- ============================================================================
\echo ''
\echo '>>> 7. Neighborhood Infrastructure Summary'
\echo ''

SELECT 
    n.name AS neighborhood,
    d.urban_classification,
    d.population_density AS pop_density_per_sqkm,
    COUNT(l.light_id) AS total_lights,
    COUNT(l.light_id) FILTER (WHERE l.status = 'operational') AS operational,
    COUNT(l.light_id) FILTER (WHERE l.status != 'operational') AS needs_attention,
    ROUND(100.0 * COUNT(l.light_id) FILTER (WHERE l.status = 'operational') / NULLIF(COUNT(l.light_id), 0), 1) AS operational_pct
FROM neighborhoods n
LEFT JOIN demographics_enrichment d ON n.neighborhood_id = d.neighborhood_id
LEFT JOIN street_lights l ON l.neighborhood_id = n.neighborhood_id
GROUP BY n.neighborhood_id, n.name, d.urban_classification, d.population_density
ORDER BY operational_pct ASC
LIMIT 10;

-- ============================================================================
-- 8. MAINTENANCE ANALYSIS - Issue Types and Resolution Time
-- ============================================================================
\echo ''
\echo '>>> 8. Maintenance Issue Analysis'
\echo ''

SELECT 
    issue_type,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE resolved_at IS NULL) AS open_requests,
    ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - reported_at)) / 3600.0)::numeric, 1) AS avg_resolution_hours,
    ROUND(MAX(EXTRACT(EPOCH FROM (resolved_at - reported_at)) / 3600.0)::numeric, 1) AS max_resolution_hours
FROM maintenance_requests
GROUP BY issue_type
ORDER BY total_requests DESC;

-- ============================================================================
-- 9. POWER GRID CORRELATION - Outages and Light Failures
-- ============================================================================
\echo ''
\echo '>>> 9. Power Grid Impact on Light Status'
\echo ''

SELECT 
    p.grid_zone,
    COUNT(l.light_id) AS total_lights,
    ROUND(AVG(p.avg_load_percent)::numeric, 1) AS avg_grid_load_pct,
    ROUND(AVG(p.outage_history_count)::numeric, 1) AS avg_outages,
    COUNT(l.light_id) FILTER (WHERE l.status = 'faulty') AS faulty_lights,
    ROUND(100.0 * COUNT(l.light_id) FILTER (WHERE l.status = 'faulty') / NULLIF(COUNT(l.light_id), 0), 1) AS faulty_pct
FROM power_grid_enrichment p
JOIN street_lights l ON p.light_id = l.light_id
GROUP BY p.grid_zone
ORDER BY faulty_pct DESC;

-- ============================================================================
-- 10. TEXT SEARCH - Find Safety Hazards in Descriptions
-- ============================================================================
-- Compare with Cortex Search: "Find safety hazards and dangerous situations"
-- PostgreSQL requires: ILIKE patterns, OR conditions, no semantic understanding
\echo ''
\echo '>>> 10. Text Search: Safety Hazards (requires ILIKE, no semantics)'
\echo ''

SELECT 
    m.request_id,
    m.light_id,
    n.name AS neighborhood,
    m.issue_type,
    LEFT(m.description, 60) || '...' AS description_preview,
    CASE WHEN m.resolved_at IS NULL THEN 'OPEN' ELSE 'CLOSED' END AS status
FROM maintenance_requests m
JOIN street_lights l ON m.light_id = l.light_id
LEFT JOIN neighborhoods n ON l.neighborhood_id = n.neighborhood_id
WHERE 
    -- Must manually specify every keyword variant - no semantic understanding!
    m.description ILIKE '%danger%'
    OR m.description ILIKE '%hazard%'
    OR m.description ILIKE '%urgent%'
    OR m.description ILIKE '%exposed wire%'
    OR m.description ILIKE '%fire%'
    OR m.description ILIKE '%spark%'
    OR m.description ILIKE '%leaning%'
ORDER BY m.reported_at DESC
LIMIT 10;

-- ============================================================================
-- 11. TEXT SEARCH - Find Flickering Light Issues
-- ============================================================================
-- Compare with Cortex Search: "Find lights that flicker on and off"
-- Cortex Search understands: flickering ≈ blinking ≈ intermittent ≈ unstable
\echo ''
\echo '>>> 11. Text Search: Flickering Issues (no synonym matching)'
\echo ''

SELECT 
    m.request_id,
    m.light_id,
    n.name AS neighborhood,
    m.issue_type,
    LEFT(m.description, 70) || '...' AS description_preview
FROM maintenance_requests m
JOIN street_lights l ON m.light_id = l.light_id
LEFT JOIN neighborhoods n ON l.neighborhood_id = n.neighborhood_id
WHERE 
    -- Must list every possible term - misses semantic equivalents!
    m.description ILIKE '%flicker%'
    OR m.description ILIKE '%blink%'
    OR m.description ILIKE '%intermittent%'
    OR m.description ILIKE '%on and off%'
ORDER BY m.reported_at DESC
LIMIT 10;

-- ============================================================================
-- 12. GEOGRAPHIC QUERY - Lights Within 1km of a Point
-- ============================================================================
\echo ''
\echo '>>> 12. Lights Near Koramangala Center (within 1 km)'
\echo ''

-- Using a point near Koramangala, Bengaluru (77.62, 12.93) with 1km radius
WITH reference_point AS (
    SELECT ST_SetSRID(ST_MakePoint(77.62, 12.93), 4326)::geography AS geog
)
SELECT 
    l.light_id,
    l.status,
    l.wattage,
    n.name AS neighborhood,
    ROUND((ST_Distance(l.location::geography, r.geog))::numeric, 0) AS distance_meters
FROM street_lights l
CROSS JOIN reference_point r
LEFT JOIN neighborhoods n ON l.neighborhood_id = n.neighborhood_id
WHERE ST_DWithin(l.location::geography, r.geog, 1000)
ORDER BY distance_meters
LIMIT 10;

-- ============================================================================
-- SUMMARY
-- ============================================================================
\echo ''
\echo '============================================================================'
\echo 'Demo Complete!'
\echo ''
\echo 'PostGIS Spatial Functions Used:'
\echo '  - ST_Within(point, polygon)     Point-in-polygon containment'
\echo '  - ST_Distance(geog, geog)       Accurate distance in meters'
\echo '  - ST_DWithin(geog, geog, dist)  Find features within distance'
\echo '  - <-> operator                  KNN (K-Nearest Neighbor) index'
\echo ''
\echo 'Text Search Limitations Demonstrated:'
\echo '  - ILIKE requires exact keyword matches'
\echo '  - No semantic understanding (flickering != blinking)'
\echo '  - Must manually list all synonyms'
\echo ''
\echo 'With Snowflake Intelligence, just ask in plain English:'
\echo '  - Cortex Analyst: "How many lights are faulty by neighborhood?"'
\echo '  - Cortex Search:  "Find safety hazards and dangerous situations"'
\echo '============================================================================'
