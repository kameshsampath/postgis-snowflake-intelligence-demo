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

-- =====================================================
-- Databricks Genie Space Configuration
-- =====================================================
-- Prerequisites:
--   1. Databricks Genie enabled on the workspace
--   2. Setup from 01_setup.sql completed
--   3. Appropriate permissions for Genie space creation
--
-- Variables to replace:
--   <% PREFIX %> = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

-- Set current catalog/schema
USE CATALOG <% PREFIX %>_STREETLIGHTS;
USE SCHEMA streetlights;

-- =====================================================
-- Create Genie Space for structured data
-- =====================================================

-- Create Genie space with streetlights context
CREATE GENIE SPACE IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_GENIE
  CATALOG <% PREFIX %>_STREETLIGHTS
  DESCRIPTION 'Natural language interface for streetlights maintenance and energy data'
  PROPERTIES (
    'purpose' = 'DEMO',
    'domain' = 'Infrastructure Management',
    'language' = 'English'
  );

-- Set current Genie space context
USE GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE;

-- =====================================================
-- Configure Analyst Tool for Structured Queries
-- =====================================================

-- Create Analyst tool that understands our semantic layer
CREATE GENIE TOOL IF NOT EXISTS <% PREFIX %>_STREETLIGHTS_ANALYST
  TYPE SQL_ANALYST
  CATALOG <% PREFIX %>_STREETLIGHTS
  SCHEMA streetlights
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  DESCRIPTION 'Structured query tool for streetlights data analysis'
  INSTRUCTIONS $$
You are a streetlights domain expert with access to clean, curated views.

**AVAILABLE TABLES AND THEIR PURPOSES:**
- street_lights_clean: All street light locations, types, and status information
- maintenance_records_clean: Maintenance history with descriptions and costs
- energy_consumption_clean: Energy usage data for forecasting and analysis
- weather_enrichment_clean: Weather data that affects maintenance patterns
- light_sensors_clean: Sensor readings for light performance monitoring
- demographics_clean: Neighborhood demographic information
- power_grid_zones_clean: Power grid infrastructure zones

**COMMON ANALYSIS PATTERNS:**
- Use location data (latitude, longitude, neighborhood) for geographic queries
- Join street_lights_clean with maintenance_records_clean on street_light_id
- Join energy_consumption_clean with street_lights_clean on street_light_id
- Use date fields for temporal analysis (trends, patterns over time)
- Consider severity, status, and cost for maintenance analysis
- Use neighborhood for demographic and geographic grouping

**MAP LINK FORMAT:**
When returning results with latitude/longitude coordinates, include a map link:
format: https://www.google.com/maps/search/?api=1&query={LAT},{LON}

**RESULT FORMATTING:**
- Return clean, readable tables
- Include relevant metrics and aggregations
- Provide context and insights alongside raw data
- Use appropriate number formatting (2 decimal places for costs, currency symbols)
$$;

-- =====================================================
-- Configure Semantic Layer Definitions
-- =====================================================

-- Define entity relationships and business logic
CREATE OR REPLACE GENIE ENTITY DEFINITION street_lights
  CATALOG <% PREFIX %>_STREETLIGHTS
  SCHEMA streetlights
  BASE TABLE street_lights_clean
  DESCRIPTION 'Individual street light fixtures with location and operational status'
  PRIMARY KEY (street_light_id)
  MAIN ATTRIBUTES (
    street_light_id,
    neighborhood,
    status,
    location,
    bulb_type,
    wattage,
    installation_date,
    last_maintenance_date
  )
  RELATIONSHIPS (
    maintenance_records (ONE_TO_MANY, street_light_id),
    energy_consumption (ONE_TO_MANY, street_light_id),
    light_sensors (ONE_TO_MANY, street_light_id),
    power_grid_zones (MANY_TO_ONE, power_grid_zone_id)
  );

CREATE OR REPLACE GENIE ENTITY DEFINITION maintenance_records
  CATALOG <% PREFIX %>_STREETLIGHTS
  SCHEMA streetlights
  BASE TABLE maintenance_records_clean
  DESCRIPTION 'Maintenance work orders and repair history'
  PRIMARY KEY (maintenance_id)
  MAIN ATTRIBUTES (
    maintenance_id,
    street_light_id,
    maintenance_date,
    maintenance_type,
    description,
    status,
    cost,
    severity,
    neighborhood
  )
  RELATIONSHIPS (
    street_lights (MANY_TO_ONE, street_light_id)
  );

CREATE OR REPLACE GENIE ENTITY DEFINITION energy_consumption
  CATALOG <% PREFIX %>_STREETLIGHTS
  SCHEMA streetlights
  BASE TABLE energy_consumption_clean
  DESCRIPTION 'Historical energy consumption data for cost and usage analysis'
  PRIMARY KEY (consumption_id)
  MAIN ATTRIBUTES (
    consumption_id,
    street_light_id,
    consumed_date,
    energy_consumed_kwh,
    cost,
    rate_type,
    neighborhood,
    avg_7day_consumption
  )
  RELATIONSHIPS (
    street_lights (MANY_TO_ONE, street_light_id)
  );

-- =====================================================
-- Create Verified Answers for Common Questions
-- =====================================================

-- These provide reference answers that Genie can use for consistency

CREATE OR REPLACE GENIE VERIFIED ANSWER faulty_lights_count
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  QUESTION 'How many street lights are currently faulty?'
  SQL_QUERY $$
SELECT COUNT(*) as faulty_count 
FROM <% PREFIX %>_STREETLIGHTS.streetlights.street_lights_clean 
WHERE status = 'Faulty'
$$;

CREATE OR REPLACE GENIE VERIFIED ANSWER maintenance_cost_by_type
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  QUESTION 'What is the average repair cost by maintenance type?'
  SQL_QUERY $$
SELECT 
    maintenance_type,
    AVG(cost)::DECIMAL(10,2) as avg_cost,
    COUNT(*) as total_records
FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean 
WHERE cost IS NOT NULL
GROUP BY maintenance_type
ORDER BY avg_cost DESC
$$;

CREATE OR REPLACE GENIE VERIFIED ANSWER energy_high_neighborhoods
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  QUESTION 'Which neighborhoods have the highest energy consumption?'
  SQL_QUERY $$
SELECT 
    neighborhood,
    SUM(energy_consumed_kwh) as total_energy_kwh,
    SUM(cost)::DECIMAL(10,2) as total_cost
FROM <% PREFIX %>_STREETLIGHTS.streetlights.energy_consumption_clean 
WHERE neighborhood IS NOT NULL
GROUP BY neighborhood
ORDER BY total_energy_kwh DESC
LIMIT 10
$$;

CREATE OR REPLACE GENIE VERIFIED ANSWER recent_maintenance
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  QUESTION 'What recent maintenance has been performed?'
  SQL_QUERY $$
SELECT 
    maintenance_date,
    maintenance_type,
    description,
    status,
    cost,
    neighborhood
FROM <% PREFIX %>_STREETLIGHTS.streetlights.maintenance_records_clean 
ORDER BY maintenance_date DESC
LIMIT 20
$$;

-- =====================================================
-- Create Intent Examples for Routing
-- =====================================================

-- These help Genie understand different query intents

CREATE OR REPLACE GENIE INTENT EXAMPLE geographic_query
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  EXAMPLES (
    'Show me faulty lights in Koramangala',
    'How many street lights are in downtown?',
    'What is the distribution of lights by neighborhood?'
  )
  ROUTED_TO TOOL <% PREFIX %>_STREETLIGHTS_ANALYST;

CREATE OR REPLACE GENIE INTENT EXAMPLE maintenance_query
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  EXAMPLES (
    'How many street lights are currently faulty?',
    'What is the average repair cost by maintenance type?',
    'Show me maintenance history for polg lamp replacements'
  )
  ROUTED_TO TOOL <% PREFIX %>_STREETLIGHTS_ANALYST;

CREATE OR REPLACE GENIE INTENT EXAMPLE predictive_query
  IN GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE
  EXAMPLES (
    'Predict energy consumption for the next 30 days',
    'Forecast maintenance costs for next quarter',
    'What will be the expected energy usage tomorrow?'
  )
  ROUTED_TO TOOL <% PREFIX %>_STREETLIGHTS_ANALYST;

-- =====================================================
-- Verification queries
-- =====================================================

-- LIST GENIE SPACES;
-- DESCRIBE GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE;
-- LIST GENIE TOOLS;
-- DESCRIBE GENIE TOOL <% PREFIX %>_STREETLIGHTS_ANALYST;

-- Test the Genie space with a sample query
-- USE GENIE SPACE <% PREFIX %>_STREETLIGHTS_GENIE;
-- EXPLAIN SELECT * FROM street_lights_clean WHERE status = 'Faulty';
