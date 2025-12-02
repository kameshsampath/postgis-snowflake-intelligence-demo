-- Query 1: Find all lights within a specific neighborhood
-- Demonstrates: ST_Within (point-in-polygon), spatial index usage

-- Description:
-- Find all street lights within the Koramangala neighborhood boundary.
-- This is a common operational query for maintenance teams.

-- Educational notes:
-- - ST_Within checks if a point is completely inside a polygon
-- - Uses GIST spatial index on location and boundary columns
-- - Should execute in <50ms with proper indexes

SELECT 
    l.light_id,
    l.status,
    l.wattage,
    ST_X(l.location) as longitude,
    ST_Y(l.location) as latitude,
    l.installation_date,
    l.last_maintenance,
    n.name as neighborhood
FROM streetlights.street_lights l
JOIN streetlights.neighborhoods n ON ST_Within(l.location, n.boundary)
WHERE n.name = 'Koramangala'
ORDER BY l.light_id;

-- Execution plan (uncomment to see query optimization):
-- EXPLAIN ANALYZE
-- SELECT COUNT(*) 
-- FROM streetlights.street_lights l
-- JOIN streetlights.neighborhoods n ON ST_Within(l.location, n.boundary)
-- WHERE n.name = 'Koramangala';

-- Expected result: ~100 lights (will vary based on data generation)
-- Expected execution time: <50ms with spatial index


