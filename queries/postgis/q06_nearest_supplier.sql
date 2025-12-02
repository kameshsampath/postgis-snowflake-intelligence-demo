-- Query 6: Find nearest supplier for a faulty light
-- Demonstrates: Nearest neighbor search across suppliers, spatial function usage

-- Description:
-- For each faulty light, find the nearest supplier that can service it.
-- Useful for maintenance dispatch and supplier allocation.

-- Educational notes:
-- - Uses get_nearest_supplier() function created in init scripts
-- - KNN operator (<->) for efficient nearest neighbor search
-- - geography cast for accurate distance in kilometers
-- - Can filter by supplier specialization if needed

-- Find nearest supplier for a specific light
SELECT * FROM streetlights.get_nearest_supplier('SL-0001');

-- Find nearest supplier for all faulty lights
SELECT 
    l.light_id,
    l.status,
    ST_X(l.location) as light_longitude,
    ST_Y(l.location) as light_latitude,
    n.name as neighborhood,
    s.name as nearest_supplier,
    s.specialization,
    ROUND(
        ST_Distance(s.location::geography, l.location::geography)::numeric / 1000, 
        2
    ) as distance_km,
    s.avg_response_hours,
    s.contact_phone
FROM streetlights.street_lights l
LEFT JOIN streetlights.neighborhoods n ON l.neighborhood_id = n.neighborhood_id
CROSS JOIN LATERAL (
    SELECT supplier_id, name, specialization, location, avg_response_hours, contact_phone
    FROM streetlights.suppliers
    ORDER BY location <-> l.location
    LIMIT 1
) s
WHERE l.status = 'faulty'
ORDER BY distance_km;

-- Alternative: Find suppliers within service radius
-- SELECT 
--     l.light_id,
--     s.name as supplier,
--     s.specialization,
--     ST_Distance(s.location::geography, l.location::geography) / 1000 as distance_km,
--     s.service_radius_km
-- FROM streetlights.street_lights l
-- CROSS JOIN streetlights.suppliers s
-- WHERE l.status = 'faulty'
--   AND ST_Distance(s.location::geography, l.location::geography) / 1000 <= s.service_radius_km
-- ORDER BY l.light_id, distance_km;

-- Use case: Maintenance dispatch system
-- Automatically assigns faulty lights to nearest available supplier
-- Considers service radius and response time

-- Expected result: One supplier per faulty light, with distance
-- Expected execution time: <100ms with spatial index


