-- Cortex Search: maintenance records full-text search
-- Run: snow sql -f snowflake/03_cortex_search.sql -D "PREFIX=KAMESHS" -c local-oauth --enable-templating ALL

USE ROLE ACCOUNTADMIN;
USE DATABASE <% PREFIX %>_STREETLIGHTS;
USE SCHEMA PUBLIC;
USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

CREATE OR REPLACE CORTEX SEARCH SERVICE <% PREFIX %>_STREETLIGHTS.PUBLIC.maintenance_search
  ON search_text
  ATTRIBUTES light_id, neighborhood, maintenance_type
  WAREHOUSE = <% PREFIX %>_STREETLIGHTS_WH
  TARGET_LAG = '1 day'
  AS
    SELECT
        m."id"::VARCHAR          AS record_id,
        m."light_id"::VARCHAR    AS light_id,
        m."date"::VARCHAR        AS maintenance_date,
        m."type"::VARCHAR        AS maintenance_type,
        m."description"::VARCHAR AS description,
        m."cost"::VARCHAR        AS cost,
        m."technician"::VARCHAR  AS technician,
        l."neighborhood"::VARCHAR AS neighborhood,
        CONCAT(
            'Light ', m."light_id", ' in ', l."neighborhood",
            ' had ', m."type", ' maintenance on ', m."date",
            ': ', m."description",
            ' Cost: $', m."cost",
            ' Technician: ', m."technician"
        ) AS search_text
    FROM <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."maintenance_records" m
    JOIN <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."street_lights" l
      ON l."id" = m."light_id";

-- Verify
SHOW CORTEX SEARCH SERVICES IN DATABASE <% PREFIX %>_STREETLIGHTS;
