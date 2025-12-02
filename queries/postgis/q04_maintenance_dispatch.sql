-- Query 4: Nearest faulty lights for maintenance dispatch
-- Demonstrates: ST_Distance, KNN operator (<->), ORDER BY distance

-- Description:
-- Find the 5 nearest faulty lights to a technician's current location.
-- Optimized for maintenance routing and dispatch decisions.

-- Educational notes:
-- - KNN operator (<->) uses spatial index for fast nearest neighbor search
-- - More efficient than calculating distance to all points
-- - geography cast for accurate meter-based distances
-- - LIMIT controls how many results returned

-- Technician location: (77.5946, 12.9716)
WITH technician_location AS (
    SELECT ST_MakePoint(77.5946, 12.9716)::geography as location
)
SELECT 
    l.light_id,
    l.status,
    ST_X(l.location) as longitude,
    ST_Y(l.location) as latitude,
    l.wattage,
    ROUND(
        ST_Distance(
            l.location::geography,
            t.location
        )::numeric / 1000, 
        2
    ) as distance_km,
    n.name as neighborhood
FROM streetlights.street_lights l
CROSS JOIN technician_location t
LEFT JOIN streetlights.neighborhoods n ON l.neighborhood_id = n.neighborhood_id
WHERE l.status = 'faulty'
ORDER BY l.location::geography <-> t.location
LIMIT 5;

-- Alternative using simpler syntax (slightly less efficient):
-- SELECT light_id, status,
--        ST_Distance(location::geography, ST_MakePoint(77.5946, 12.9716)::geography) / 1000 as distance_km
-- FROM streetlights.street_lights
-- WHERE status = 'faulty'
-- ORDER BY distance_km
-- LIMIT 5;

-- Use case: Maintenance dispatch system assigning work orders
-- Shows technician the 5 closest faulty lights to minimize travel time

-- Expected result: 5 faulty lights, ordered by distance
-- Expected execution time: <20ms with spatial index and KNN operator


