-- Query 5: Query enriched view with all contextual data
-- Demonstrates: Enriched view usage, combined operational + enrichment data

-- Description:
-- Query the enriched view to show combined operational data with
-- weather patterns, demographics, and power grid information.
-- This is the data that will flow through CDC to Snowflake.

-- Educational notes:
-- - Enriched view joins base tables with enrichment tables
-- - Shows current season's weather data automatically
-- - Calculates maintenance urgency based on predicted failure date
-- - Demonstrates value of enrichment for decision-making

-- Show high-risk operational lights with full context
SELECT 
    light_id,
    status,
    neighborhood_name,
    longitude,
    latitude,
    age_months,
    days_since_maintenance,
    season,
    avg_temperature_c,
    rainfall_mm,
    failure_risk_score,
    predicted_failure_date,
    maintenance_urgency,
    population_density,
    urban_classification,
    grid_zone,
    avg_load_percent,
    outage_history_count
FROM streetlights.street_lights_enriched
WHERE status = 'operational'  -- Still operational but at risk
  AND failure_risk_score > 0.7  -- High risk
ORDER BY failure_risk_score DESC, predicted_failure_date ASC
LIMIT 10;

-- Alternative: Show faulty lights with enrichment context
-- SELECT light_id, status, neighborhood_name,
--        season, failure_risk_score, 
--        grid_zone, avg_load_percent
-- FROM streetlights.street_lights_enriched
-- WHERE status = 'faulty'
-- ORDER BY outage_history_count DESC;

-- Alternative: Group by maintenance urgency
-- SELECT maintenance_urgency, COUNT(*) as count
-- FROM streetlights.street_lights_enriched
-- WHERE status != 'faulty'
-- GROUP BY maintenance_urgency
-- ORDER BY CASE maintenance_urgency
--     WHEN 'CRITICAL' THEN 1
--     WHEN 'HIGH' THEN 2
--     WHEN 'MEDIUM' THEN 3
--     WHEN 'LOW' THEN 4
-- END;

-- Use case: Proactive maintenance planning
-- Identifies operational lights likely to fail soon
-- Enrichment data provides context for prioritization decisions

-- Expected result: Top 10 high-risk lights with full context
-- Expected execution time: <100ms (multi-table JOIN via view)


