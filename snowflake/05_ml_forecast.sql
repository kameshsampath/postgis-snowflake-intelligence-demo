-- ML Forecast: daily energy consumption per light
-- Run: snow sql -f snowflake/05_ml_forecast.sql -D "PREFIX=KAMESHS" -c local-oauth --enable-templating ALL

USE ROLE ACCOUNTADMIN;
USE DATABASE <% PREFIX %>_STREETLIGHTS;
USE SCHEMA PUBLIC;
USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

-- Step 1: Create training view from CLD energy_consumption table
CREATE OR REPLACE VIEW <% PREFIX %>_STREETLIGHTS.PUBLIC.energy_daily_vw AS
    SELECT
        m."light_id"::VARCHAR AS series_id,
        m."date"::DATE        AS ds,
        SUM(m."kwh")          AS daily_kwh
    FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."energy_consumption" m
    GROUP BY m."light_id", m."date";

-- Step 2: Train the forecast model
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST <% PREFIX %>_STREETLIGHTS.PUBLIC.energy_forecast(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', '<% PREFIX %>_STREETLIGHTS.PUBLIC.energy_daily_vw'),
    SERIES_COLNAME => 'SERIES_ID',
    TIMESTAMP_COLNAME => 'DS',
    TARGET_COLNAME => 'DAILY_KWH'
);

-- Verify
SHOW SNOWFLAKE.ML.FORECAST IN DATABASE <% PREFIX %>_STREETLIGHTS;
