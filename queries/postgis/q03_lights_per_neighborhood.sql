-- Query 3: Count lights per neighborhood
-- Demonstrates: Spatial aggregation, point-in-polygon with GROUP BY

-- Description:
-- Count total lights and breakdown by status for each neighborhood.
-- Shows which neighborhoods have the most issues requiring attention.

-- Educational notes:
-- - Combines spatial JOIN with aggregation
-- - LEFT JOIN ensures all neighborhoods shown (even with 0 lights)
-- - CASE expression for conditional counting
-- - Useful for resource planning and prioritization

SELECT 
    n.name as neighborhood,
    COUNT(l.light_id) as total_lights,
    COUNT(CASE WHEN l.status = 'operational' THEN 1 END) as operational,
    COUNT(CASE WHEN l.status = 'maintenance_required' THEN 1 END) as maintenance_required,
    COUNT(CASE WHEN l.status = 'faulty' THEN 1 END) as faulty,
    ROUND(
        COUNT(CASE WHEN l.status = 'faulty' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(l.light_id), 0), 
        2
    ) as faulty_percentage
FROM streetlights.neighborhoods n
LEFT JOIN streetlights.street_lights l ON ST_Within(l.location, n.boundary)
GROUP BY n.name
ORDER BY faulty DESC, total_lights DESC;

-- Use case: City planners identifying neighborhoods needing attention
-- Prioritize neighborhoods with highest faulty count or percentage

-- Expected result: 50 rows (one per neighborhood)
-- Expected execution time: <100ms with spatial indexes


