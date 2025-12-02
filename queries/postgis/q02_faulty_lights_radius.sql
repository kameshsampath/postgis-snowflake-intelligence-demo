-- Query 2: Find faulty lights within 1km radius
-- Demonstrates: ST_DWithin (distance-based search), geography cast

-- Description:
-- Find all faulty lights within 1km of a given point (maintenance dispatch).
-- Uses geography cast for accurate meter-based distance calculations.

-- Educational notes:
-- - ST_DWithin is more efficient than ST_Distance for radius searches
-- - geography cast (::geography) uses spherical distance (meters)
-- - geometry uses planar distance (degrees, less accurate for real-world distances)
-- - GIST index accelerates the search

-- Example point: Near Koramangala (12.9716, 77.5946)
SELECT 
    light_id,
    status,
    ST_X(location) as longitude,
    ST_Y(location) as latitude,
    ROUND(
        ST_Distance(
            location::geography,
            ST_MakePoint(77.5946, 12.9716)::geography
        )::numeric, 
        2
    ) as distance_meters
FROM streetlights.street_lights
WHERE status = 'faulty'
  AND ST_DWithin(
        location::geography,
        ST_MakePoint(77.5946, 12.9716)::geography,
        1000  -- 1000 meters = 1km
      )
ORDER BY distance_meters;

-- Use case: Maintenance technician at location (77.5946, 12.9716)
-- needs to find nearest faulty lights for routing

-- Expected result: 0-10 faulty lights within 1km (varies by location and data)
-- Expected execution time: <50ms with spatial index


