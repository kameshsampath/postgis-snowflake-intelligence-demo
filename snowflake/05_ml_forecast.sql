-- ML Forecast: daily energy consumption per light with location enrichment
-- Run: snow sql -f snowflake/05_ml_forecast.sql \
--        -D "PREFIX=KAMESHS" -D "ROLE=KAMESH_DEMOS" \
--        -c devrel-ent --enable-templating STANDARD

-- ─────────────────────────────────────────────────────────────
-- Block 1: ACCOUNTADMIN — schema grants + resize warehouse up
-- ─────────────────────────────────────────────────────────────
USE ROLE ACCOUNTADMIN;
GRANT CREATE VIEW ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
GRANT CREATE SNOWFLAKE.ML.FORECAST ON SCHEMA <% PREFIX %>_STREETLIGHTS.PUBLIC TO ROLE <% ROLE %>;
ALTER WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH SET WAREHOUSE_SIZE = 'MEDIUM';

-- ─────────────────────────────────────────────────────────────
-- Block 2: Worker role — create enriched training view
--   Joins street_lights to add location + status context
--   ANY_VALUE() is safe: lat/lng/neighborhood/status are fixed per light_id
-- ─────────────────────────────────────────────────────────────
USE ROLE <% ROLE %>;
USE DATABASE <% PREFIX %>_STREETLIGHTS;
USE SCHEMA PUBLIC;
USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

CREATE OR REPLACE VIEW <% PREFIX %>_STREETLIGHTS.PUBLIC.energy_daily_vw AS
    SELECT
        m."light_id"::VARCHAR           AS series_id,
        m."date"::DATE                  AS ds,
        SUM(m."kwh")                    AS daily_kwh,
        ANY_VALUE(l."latitude")         AS latitude,
        ANY_VALUE(l."longitude")        AS longitude,
        ANY_VALUE(l."neighborhood")     AS neighborhood,
        ANY_VALUE(l."status")           AS status
    FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."energy_consumption" m
    JOIN <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."street_lights" l
      ON l."id" = m."light_id"
    GROUP BY m."light_id", m."date";

-- ─────────────────────────────────────────────────────────────
-- Block 3: Worker role — train forecast model
--   Synchronous DDL: blocks until training is complete.
--   Run this SQL file in background (run_in_background=True) so the
--   calling agent does not wait. The step-9 gate auto-verifies the
--   model via --prior-step step-8 backfill.
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST <% PREFIX %>_STREETLIGHTS.PUBLIC.energy_forecast(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', '<% PREFIX %>_STREETLIGHTS.PUBLIC.energy_daily_vw'),
    SERIES_COLNAME => 'SERIES_ID',
    TIMESTAMP_COLNAME => 'DS',
    TARGET_COLNAME => 'DAILY_KWH'
);

-- ─────────────────────────────────────────────────────────────
-- Block 4: ACCOUNTADMIN — resize warehouse back to XSMALL
--   Runs automatically after training finishes (end of this file).
-- ─────────────────────────────────────────────────────────────
USE ROLE ACCOUNTADMIN;
ALTER WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH SET WAREHOUSE_SIZE = 'XSMALL';
SHOW SNOWFLAKE.ML.FORECAST IN DATABASE <% PREFIX %>_STREETLIGHTS;
